from custom_path import DATA_PATH
from DataLoader import MultiChatDataLoader
from utill.utill import get_files_with_dir_path
from typing import Callable
from collections import OrderedDict
from utill.utill import try_except, have_enough_words, is_values_of_key_matched

# https://github.com/Mimino666/langdetect
import langdetect as ld

# https://github.com/saffsd/langid.py
import langid as li


@try_except
def detect_func(line_dict: OrderedDict, criteria_func: Callable, langdetect_func: Callable, line_key: str):
    if criteria_func(line_dict[line_key]):
        return langdetect_func(line_dict[line_key])
    else:
        return ''


def li_classify_str(s):
    return li.classify(s)[0]


class MultiLangChatDataLoader(MultiChatDataLoader):

    def __init__(self, path: str, loader_nums: int = None,
                 label_condition_func: Callable = None, label_condition_args: tuple = tuple(),
                 words_enough: tuple = (1, 3), lang_func: Callable = ld.detect):

        super().__init__(
            path=path,
            loader_nums=loader_nums,
            label_condition_func=label_condition_func,
            label_condition_args=label_condition_args,
        )

        # Add detected language.
        # args = (criteria_func: Callable, lang_func: Callable, line_key: str)
        self.add_feature('lang_author_name', detect_func,
                         args=(have_enough_words(words_enough[0]), lang_func, 'author_name'))
        self.add_feature('lang_message', detect_func,
                         args=(have_enough_words(words_enough[1]), lang_func, 'message'))


if __name__ == '__main__':

    description_files = get_files_with_dir_path(DATA_PATH, 'Description')
    multi_lang_chat_data_loader = MultiLangChatDataLoader(
        path=description_files[0],
        label_condition_func=is_values_of_key_matched,
        label_condition_args=({'winner': 'DRAW', 'main': 'ISL'},),
        words_enough=(1, 3),
        lang_func=li_classify_str,
    )

    for lang_chat_data_loader in multi_lang_chat_data_loader:
        for line in lang_chat_data_loader.lines:
            line.pop('img')
            print(line)
        print(lang_chat_data_loader.label_dict)
