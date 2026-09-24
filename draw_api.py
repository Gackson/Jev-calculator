"""One drawing round per request, with explicit, inspectable Jev decisions."""
import copy
import time

from calculator import validate_choice, validate_noul, notes_context
from typesafe_client import model_matches, system_one

DIRECTIONS = {'N': (0, -1), 'NE': (1, -1), 'E': (1, 0), 'SE': (1, 1),
              'S': (0, 1), 'SW': (-1, 1), 'W': (-1, 0), 'NW': (-1, -1)}
BASE = ('Draw a recognizable black-and-white pixel picture of `description`. '
        'The square canvas uses zero-based (x, y) coordinates: x increases rightward, '
        'y increases downward; (0, 0) is the top-left. `rows` shows the actual canvas, '
        'one string per row: 1 is black, 0 is white. Black marks cannot be erased. '
        'Use the whole composition and negative space to represent the description. ')


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('Invalid drawing progress')
    return value


def point_key(index, size):
    return f'{index % size},{index // size}'


def position_options(size):
    return {point_key(i, size): f'Paint pixel ({point_key(i, size)}) black.' for i in range(size * size)}


def status_of(state, mode, total):
    if mode == 'enumeration':
        return 'complete' if state['scan'] == total else 'continue'
    if '0' not in state['pixels']:
        return 'full'
    if mode == 'monte_carlo' and state['repeats'] >= 3:
        return 'repeated'
    if mode == 'ballpoint' and state['marks'] > total:
        return 'limit'
    return 'continue'


def read_cursor(cursor, identity):
    size, mode = identity['size'], identity['mode']
    total = size * size
    if cursor is None:
        return dict(pixels='0' * total, scan=0, marks=0, judgments=0, pen=None,
                    last=None, repeats=0)
    if not isinstance(cursor, dict) or cursor.get('input') != identity or not isinstance(cursor.get('state'), dict):
        raise ValueError('Drawing settings changed')
    state = copy.deepcopy(cursor['state'])
    if set(state) != {'pixels', 'scan', 'marks', 'judgments', 'pen', 'last', 'repeats'}:
        raise ValueError('Invalid drawing progress')
    if not isinstance(state['pixels'], str) or len(state['pixels']) != total or set(state['pixels']) - {'0', '1'}:
        raise ValueError('Invalid canvas')
    for key in ('scan', 'marks', 'judgments', 'repeats'):
        integer(state[key], 0, total if key == 'scan' else 10**9)
    for key in ('pen', 'last'):
        if state[key] is not None:
            integer(state[key], 0, total - 1)
            if state['pixels'][state[key]] != '1':
                raise ValueError('Invalid pen')
    if state['pixels'].count('1') > state['marks'] or state['marks'] > state['judgments']:
        raise ValueError('Invalid mark count')
    if mode == 'enumeration':
        if state['scan'] != state['judgments'] or '1' in state['pixels'][state['scan']:] or state['pen'] is not None:
            raise ValueError('Invalid enumeration progress')
    elif state['scan'] != 0:
        raise ValueError('Invalid scan')
    if mode != 'ballpoint' and state['pen'] is not None:
        raise ValueError('Invalid pen mode')
    if (state['last'] is None) != (state['repeats'] == 0):
        raise ValueError('Invalid repeat count')
    if status_of(state, mode, total) != 'continue':
        raise ValueError('Drawing already finished')
    return state


def draw_step(body, token, model='jev-1.13.0', call=None):
    if not isinstance(body, dict):
        raise ValueError('Invalid request')
    extra_context = notes_context(body.get('notes', ''))
    prompt, size, mode = body.get('prompt'), body.get('size'), body.get('mode')
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 1000:
        raise ValueError('Invalid description')
    integer(size, 4, 14)
    if mode not in ('enumeration', 'monte_carlo', 'ballpoint'):
        raise ValueError('Invalid drawing mode')
    identity = dict(prompt=prompt, size=size, mode=mode, **extra_context)
    state = read_cursor(body.get('cursor'), identity)
    total = size * size
    view = dict(description=prompt, size=size, **extra_context,
                rows=[state['pixels'][i:i + size] for i in range(0, total, size)],
                marks=state['marks'], pen=None if state['pen'] is None else point_key(state['pen'], size))
    phase = 'pixel' if mode == 'enumeration' else 'move' if state['pen'] is not None else 'place'
    if mode == 'enumeration':
        view['target'] = point_key(state['scan'], size)
        questions = {'draw': {'type': 'noul', 'instructions': BASE +
                     'Should `target` be black in the intended picture? Pixels are visited left to right, top to bottom.',
                     'criteria': {'true': 'This pixel belongs to the black drawing.', 'false': 'Leave this pixel white.'}}}
    else:
        options = position_options(size)
        instruction = BASE + 'Choose the next pixel to paint, or END if the drawing is complete. '
        if phase == 'move':
            x, y = state['pen'] % size, state['pen'] // size
            options = {key: f'Move the pen {key} to ({x + dx},{y + dy}) and paint it black.'
                       for key, (dx, dy) in DIRECTIONS.items() if 0 <= x + dx < size and 0 <= y + dy < size}
            options['LIFT'] = 'End this stroke and lift the pen; next choose a new stroke or end the drawing.'
            instruction = BASE + 'Continue the current stroke to an adjacent pixel, or LIFT to end this stroke. '
        else:
            options['END'] = 'The drawing is complete; stop painting.'
            if mode == 'ballpoint':
                instruction += 'The pen is lifted; choose where to start a new stroke. '
        questions = {'draw': {'type': 'choice', 'instructions': instruction, 'criteria': options}}
    payload = dict(model=model, state=view, questions=questions)
    recorded = copy.deepcopy(payload)
    started = time.monotonic()
    response = (call or (lambda data: system_one(token, data)))(payload)
    if (not isinstance(response, dict) or not model_matches(response.get('model'), model) or not isinstance(response.get('answers'), dict)
            or set(response['answers']) != set(questions)):
        raise ValueError('Invalid model response')
    steps = []
    for key, question in questions.items():
        answer = response['answers'][key]
        if not isinstance(answer, dict):
            raise ValueError('Invalid answer')
        decision = validate_noul(answer) if mode == 'enumeration' else {'type': 'choice', **validate_choice(answer, question['criteria'])}
        state['judgments'] += 1
        steps.append(dict(decision, index=state['judgments'], phase=phase, question_id=key,
                          request=recorded, model=response['model'], target=view.get('target'),
                          choice=('PAINT' if decision['yes'] else 'SKIP') if mode == 'enumeration' else decision['choice']))
    selected = steps[-1]['choice']
    status, point = 'continue', None
    if mode == 'enumeration':
        if selected == 'PAINT':
            point = state['scan']
        state['scan'] += 1
    elif selected == 'END':
        status = 'complete'
    elif selected == 'LIFT':
        state['pen'] = None
    elif phase == 'move':
        dx, dy = DIRECTIONS[selected]
        point = state['pen'] + dy * size + dx
    else:
        x, y = map(int, selected.split(','))
        point = y * size + x
    if point is not None:
        pixels = list(state['pixels'])
        pixels[point] = '1'
        state['pixels'] = ''.join(pixels)
        state['marks'] += 1
        state['repeats'] = state['repeats'] + 1 if state['last'] == point else 1
        state['last'] = point
        if mode == 'ballpoint':
            state['pen'] = point
        steps[-1]['target'] = point_key(point, size)
    if status == 'continue':
        status = status_of(state, mode, total)
    usage = response.get('usage', {})
    tokens = sum(integer(usage.get(key, 0), 0, 10**9) for key in ('input_tokens', 'output_tokens'))
    return dict(steps=steps, pixels=state['pixels'], marks=state['marks'], scan=state['scan'],
                status=status, cursor=dict(input=identity, state=state) if status == 'continue' else None,
                latency_ms=round((time.monotonic() - started) * 1000), tokens=tokens)
