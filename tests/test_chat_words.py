import unittest
from unittest.mock import Mock
from chat_api import chat_step
from chat_words import WORDS, WORD_OPTIONS, render_words


def response(choice):
    return {'model': 'jev-1.13.0', 'answers': {'word': {'type':'choice', 'choice':choice,
            'confidence': .8, 'probabilities': {key: float(key==choice) for key in WORD_OPTIONS}}},
            'usage': {'input_tokens':100, 'output_tokens':10}}


class WordChatTests(unittest.TestCase):
    def step(self, choices, choice, **extra):
        call = Mock(return_value=response(choice))
        body = {'mode':'word','message':'Is tomato a fruit?', 'choices':choices,
                'reply':render_words(choices), **extra}
        return chat_step(body, 'private-key', call=call), call

    def test_uses_all_255_options_without_space(self):
        result, call = self.step([], 'YES')
        self.assertEqual(len(WORDS),249)
        criteria=call.call_args.args[0]['questions']['word']['criteria']
        self.assertEqual(len(criteria),255)
        self.assertNotIn('SPACE',criteria)
        self.assertEqual(set(criteria)-set(WORDS),{'.',',','?','!','NEWLINE','END'})
        self.assertEqual(result['reply'],'YES')
        self.assertEqual(result['step']['request'],call.call_args.args[0])
        self.assertEqual(result['step']['probabilities'],response('YES')['answers']['word']['probabilities'])

    def test_sentence_spacing_punctuation_newline_end_and_exact_state(self):
        choices=[]
        for choice in ['YES',',','A','TOMATO','IS','A','FRUIT','.','NEWLINE','THANK','YOU','!','END']:
            result,call=self.step(choices,choice)
            self.assertEqual(call.call_args.args[0]['state']['reply_so_far'],render_words(choices))
            self.assertEqual(call.call_args.args[0]['state']['selected_words_and_marks'],choices)
            self.assertEqual(result['step']['position'],len(render_words(choices)))
            self.assertEqual(result['step']['separator']+result['step']['character'],result['reply'][len(render_words(choices)):])
            if choice != 'END': choices.append(choice)
        self.assertEqual(result['reply'],'YES, A TOMATO IS A FRUIT.\nTHANK YOU!')
        self.assertEqual(result['status'],'complete')

    def test_only_fifth_consecutive_choice_stops(self):
        self.assertEqual(self.step(['YES']*3,'YES')[0]['status'],'continue')
        self.assertEqual(self.step(['YES']*4,'YES')[0]['status'],'repeated_word')
        self.assertEqual(self.step(['YES']*4,'NO')[0]['status'],'continue')
        for choice in ['!', 'NEWLINE']:
            result,_=self.step([choice]*4,choice)
            self.assertEqual(result['status'],'repeated_word')
        call=Mock()
        with self.assertRaises(ValueError):
            chat_step({'mode':'word','message':'x','choices':['YES']*5,'reply':'YES YES YES YES YES'},'key',call=call)
        call.assert_not_called()

    def test_step_limit_includes_marks_and_end_wins(self):
        self.assertEqual(self.step(['HI'],'.',max_steps=2)[0]['status'],'limit')
        self.assertEqual(self.step(['HI'],'END',max_steps=2)[0]['status'],'complete')
        self.assertEqual(self.step([],'END')[0]['reply'],'')

    def test_bad_mode_progress_and_choices_do_not_call_model(self):
        for extra in [{'mode':'other'},{'choices':['SPACE']},{'choices':['UNKNOWN']},{'choices':['END']},
                      {'choices':[{}]},{'choices':'HI'},{'choices':['HI'],'reply':'WRONG'},
                      {'max_steps':129},{'max_steps':True},{'max_steps':0}]:
            with self.subTest(extra=extra):
                call=Mock()
                with self.assertRaises(ValueError):
                    chat_step({'mode':'word','message':'Hi','reply':'','choices':[],**extra},'key',call=call)
                call.assert_not_called()

    def test_notes_and_long_history_preserved(self):
        history=[{'role':'assistant','content':'HELLO '*250}]
        result,call=self.step([], 'HI', history=history, notes='Be brief.')
        state=call.call_args.args[0]['state']
        self.assertEqual(state['conversation'],history)
        self.assertIn('Be brief.', str(state))
        self.assertNotIn('private-key',str(result['step']['request']))

if __name__=='__main__': unittest.main()
