"""Fixed 255-option vocabulary and deterministic spacing for word-mode Chat."""

WORDS = tuple("""
A AN THE I YOU HE SHE IT WE THEY ME HIM
HER US THEM MY YOUR HIS ITS OUR THEIR THIS THAT THESE
THOSE WHO WHAT WHICH WHERE WHEN WHY HOW AM IS ARE WAS
WERE BE BEEN BEING HAVE HAS HAD DO DOES DID WILL WOULD
CAN COULD SHOULD MAY MIGHT MUST NOT NO YES AND OR BUT
IF BECAUSE SO AS THAN THEN WHILE OF TO IN ON AT
BY FOR FROM WITH WITHOUT ABOUT INTO OVER BETWEEN BEFORE AFTER UP
DOWN OUT OFF HERE THERE NOW TODAY TOMORROW YESTERDAY ALWAYS NEVER OFTEN
AGAIN STILL JUST ALSO ONLY VERY TOO MORE MOST LESS MUCH MANY
SOME ANY ALL EVERY EACH OTHER SAME HELLO HI PLEASE THANK THANKS
SORRY WELCOME SURE GOOD BAD GREAT WELL HAPPY SAD NICE TRUE FALSE
RIGHT WRONG IMPORTANT DIFFERENT SIMPLE EASY HARD NEW OLD BIG SMALL LONG
SHORT NEXT KNOW THINK UNDERSTAND MEAN SAY TELL ASK ANSWER HELP NEED
WANT LIKE LOVE FEEL MAKE GET GIVE TAKE USE TRY FIND SEE
LOOK READ WRITE LEARN WORK PLAY GO COME LIVE EAT DRINK START
STOP KEEP LET PUT CALL SHOW CHANGE CHECK EXPLAIN PEOPLE PERSON FRIEND
FAMILY LIFE WORLD TIME DAY WAY THING SOMETHING NOTHING EVERYTHING PLACE HOME
SCHOOL WATER FOOD FRUIT TOMATO ANIMAL CAT DOG BOOK WORD LANGUAGE QUESTION
INFORMATION IDEA REASON EXAMPLE PROBLEM NUMBER NAME RESULT COMPUTER CODE ENGLISH AI
ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN ZERO
DOING FEELING WEATHER SUNNY RAIN HEALTH SAFE BEAUTIFUL QUICK SLOW
""".split())
PUNCTUATION = tuple(".,?!")
WORD_OPTIONS = {word: None for word in WORDS}
WORD_OPTIONS.update({mark: f"Append {mark!r}." for mark in PUNCTUATION})
WORD_OPTIONS.update(NEWLINE="Start a new line.", END="The answer is complete; stop.")
assert len(WORDS) == len(set(WORDS)) == 249
assert len(WORD_OPTIONS) == 255

WORD_INSTRUCTIONS = (
    "You are a helpful assistant answering `user_message`, taking `conversation` into account. "
    "Build a helpful, concise English answer ONE WHOLE WORD at a time, using the available words. "
    "`reply_so_far` is the exact answer already written; `selected_words_and_marks` lists all prior selections. "
    "Choose the SINGLE next word or punctuation mark that continues this answer naturally. "
    "Use the words together to form meaningful, grammatically complete sentences that answer the user. "
    "Do not spell words letter by letter or restart the answer. Choose a simple alternative if a word is unavailable. "
    "The application inserts spaces between words automatically and attaches punctuation; do not select a space. "
    "NEWLINE starts a new line. Choose END only when the answer is complete."
)


def repeated_word(choices):
    return len(choices) >= 5 and choices[-5:] == [choices[-1]] * 5


def word_piece(prefix, choice):
    """Return exact added text and automatic separator; never edit prior text."""
    if choice == 'END':
        return '', ''
    if choice == 'NEWLINE':
        return '\n', ''
    separator = '' if not prefix or prefix[-1].isspace() or choice in PUNCTUATION else ' '
    return separator + choice, separator


def render_words(choices):
    text = ''
    for choice in choices:
        text += word_piece(text, choice)[0]
    return text
