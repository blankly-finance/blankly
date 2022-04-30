import prompt_toolkit
from functools import lru_cache
from prompt_toolkit import print_formatted_text, formatted_text
from prompt_toolkit.formatted_text import to_formatted_text

import questionary.constants
from yaspin import yaspin, Spinner as YaspinSpinner
from yaspin.core import Yaspin
from yaspin.spinners import Spinners

BOLD = '\033[1m'

STYLE = questionary.Style(
    [
        ('qmark', 'fg:#5f819d'),  # token in front of the question
        ('work', 'fg:#5f819d'),  # token in front of work message
        ('failure', 'fg:#ff726f'),  # token in front of failure message
        ('success', 'fg:#4BCA81'),  # token in front of success message
        ('question', 'bold'),  # question text
        ('answer', 'fg:#FF9D00 bold'),  # submitted answer text behind the question
        ('pointer', ''),  # pointer used in select and checkbox prompts
        ('selected', ''),  # style for a selected item of a checkbox
        ('separator', ''),  # separator in lists
        ('instruction', ''),  # user instructions for select, rawselect, checkbox
        ('text', ''),  # any other text
        ('instruction', ''),  # user instructions for select, rawselect, checkbox
    ]
)
questionary.constants.DEFAULT_STYLE = STYLE

from questionary import confirm, text, select, path


def fprint(text, **kwargs):
    if isinstance(text, str):
        text = [('class:text', text)]
    print_formatted_text(to_formatted_text(text), style=STYLE, **kwargs)


def print_work(text):
    fprint([('class:work', '*'), ('class:question', ' ' + text)])


def print_failure(text):
    fprint([('class:failure', '✘ '), ('class:question', text)])


def print_success(text):
    fprint([('class:success', '✔ '), ('class:question', text)])


@lru_cache(None)
def text_spinner(
        text='BLANKLY',
        left='[',
        right=']',
        interval=80
):
    fullstr = text + ' ' * (len(text)//2) + text[:-1]
    win_size = len(text)
    return YaspinSpinner([
        left + fullstr[i:i + win_size] + right
        for i in range(len(fullstr) - win_size, 0, -1)
    ], interval)


def show_spinner(text):
    return Spinner(text_spinner(), text=BOLD + text)


class Spinner(Yaspin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcome = None
        self.outcome_text = ''

    def fail(self, text):
        self.outcome = False
        self.outcome_text = text

    def ok(self, text):
        self.outcome = True
        self.outcome_text = text

    def stop(self):
        super().stop()
        if self.outcome is None:
            return

        if self.outcome:
            print_success(self.outcome_text)
        else:
            print_failure(self.outcome_text)
