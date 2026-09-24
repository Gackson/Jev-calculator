"""One Jev Choice per output character; no generated text is repaired or sampled."""
import string
import copy
import time

from calculator import validate_choice, notes_context, model_request
from typesafe_client import model_matches, system_one

MAX_CHARACTERS = 256
CHARACTERS = string.ascii_uppercase + string.digits + " .,?!'\"-:;()/+=" + "\n"
OPTIONS = {c: f"Append the character {c!r}." for c in CHARACTERS if c not in ' \n'}
OPTIONS.update(SPACE="Append one space between words.", NEWLINE="Append one line break.",
               END="The reply is complete; stop without appending a character.")
VALUES = {key: {'SPACE': ' ', 'NEWLINE': '\n', 'END': ''}.get(key, key) for key in OPTIONS}
INSTRUCTIONS = (
    "You are a helpful assistant answering `user_message`, taking `conversation` into account. "
    "Your goal is a helpful, concise, coherent answer written as a complete English sentence made of words. "
    "You write this answer one character at a time: consecutive letters form words, "
    "spaces separate words, and the words together form a meaningful, grammatically complete sentence "
    "that answers the user's message. Each selected character is appended to the same growing answer; "
    "it is not a separate answer on its own. "
    "`reply_so_far` is the exact reply already written, possibly empty. "
    "Which SINGLE character should be appended next? Continue from the end, never restart or rewrite it. "
    "If a word is unfinished, choose its next letter. When a word is finished and the sentence needs "
    "another word, choose SPACE, then begin the next word. "
    "Write in English using UPPERCASE letters A-Z, digits, and the available punctuation. "
    "SPACE inserts a word separator; NEWLINE inserts a line break. "
    "Select END only when the words and punctuation already written form a complete answer. "
    "For this step, select only the next character or END; the accumulated characters form the final sentence."
)


def repeated_character(text):
    return len(text) >= 5 and text[-5:] == text[-1] * 5


def chat_step(body, token, model='jev-1.13.0', call=None):
    if not isinstance(body, dict):
        raise ValueError('Invalid request')
    extra_context = notes_context(body.get('notes', ''))
    prompt, prefix = body.get('message'), body.get('reply', '')
    limit, history = body.get('max_characters', 128), body.get('history', [])
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 1000:
        raise ValueError('Invalid message')
    if type(limit) is not int or not 1 <= limit <= MAX_CHARACTERS:
        raise ValueError('Invalid character limit')
    if (not isinstance(prefix, str) or len(prefix) >= limit or prefix.endswith('  ')
            or repeated_character(prefix)
            or any(c not in CHARACTERS for c in prefix)):
        raise ValueError('Invalid reply prefix')
    if not isinstance(history, list) or len(history) > 6:
        raise ValueError('Invalid history')
    clean_history = []
    for item in history:
        if (not isinstance(item, dict) or item.get('role') not in ('user', 'assistant')
                or not isinstance(item.get('content'), str) or len(item['content']) > 1000):
            raise ValueError('Invalid history entry')
        clean_history.append({'role': item['role'], 'content': item['content']})
    payload = model_request(model, {'conversation': clean_history, 'user_message': prompt,
                            'reply_so_far': prefix, **extra_context}, {'character': {
                                'type': 'choice', 'instructions': INSTRUCTIONS, 'criteria': OPTIONS}})
    started = time.monotonic()
    request_input = copy.deepcopy(payload)
    response = (call or (lambda payload: system_one(token, payload)))(payload)
    if (not isinstance(response, dict) or not model_matches(response.get('model'), model) or not isinstance(response.get('answers'), dict)
            or set(response['answers']) != {'character'}):
        raise ValueError('Invalid model response')
    answer = validate_choice(response['answers']['character'], OPTIONS)
    character = VALUES[answer['choice']]
    reply = prefix + character
    usage = response.get('usage', {})
    tokens = sum(usage.get(key, 0) for key in ('input_tokens', 'output_tokens'))
    status = ('complete' if answer['choice'] == 'END' else
              'repeated_space' if reply.endswith('  ') else
              'repeated_character' if repeated_character(reply) else
              'limit' if len(reply) >= limit else 'continue')
    return {'step': {**answer, 'character': character, 'position': len(prefix),
                     'request': request_input,
                     'model': response['model'], 'latency_ms': round((time.monotonic() - started) * 1000),
                     'tokens': tokens}, 'reply': reply,
            'status': status}
