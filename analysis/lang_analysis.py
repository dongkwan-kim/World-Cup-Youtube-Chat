from custom_path import DATA_PATH
from DataLoader import MultiChatDataLoader
from utill.utill import get_files_with_dir_path
from typing import Callable, Tuple
from collections import OrderedDict
from utill.utill import try_except, have_enough_words, is_values_of_key_matched
from termcolor import cprint, colored
import os
import pickle

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
                 criteria_funcs: Tuple[Callable, Callable] = (None, None),
                 lang_func: Callable = ld.detect):
        """
        :param path: path of description file
        :param loader_nums: the number of loaders
        :param label_condition_func: def func(line_dict, *args): ... like is_values_of_key_matched
        :param label_condition_args: e.g. ({'winner': 'DRAW', 'main': 'ISL'},)
        :param criteria_funcs: tuple of criteria_func for feature addition
        :param lang_func: return str
        """

        self.info = '-'.join([
            str(loader_nums),
            str(label_condition_func.__name__ if label_condition_func else None),
            str(label_condition_args if label_condition_args else None),
            str(tuple((cf.__name__ if cf else None) for cf in criteria_funcs)),
            str(lang_func.__name__),
        ])

        if self.load():
            return

        super().__init__(
            path=path,
            loader_nums=loader_nums,
            label_condition_func=label_condition_func,
            label_condition_args=label_condition_args,
        )

        # Add detected language.
        # args = (criteria_func: Callable, lang_func: Callable, line_key: str)
        criteria_func_list = [(cf if cf else lambda _: True) for cf in criteria_funcs]
        self.add_feature('lang_author_name', detect_func,
                         args=(criteria_func_list.pop(0), lang_func, 'author_name'))
        self.add_feature('lang_message', detect_func,
                         args=(criteria_func_list.pop(0), lang_func, 'message'))

    def get_file_name_to_dump_and_load(self):
        return '{}-{}.pkl'.format(self.__class__.__name__, self.info)

    def dump(self):
        dump_file_name = self.get_file_name_to_dump_and_load()

        # If dump_file_name exists, just return.
        if dump_file_name in os.listdir(DATA_PATH):
            cprint('Dump Fail: {} already exists.'.format(dump_file_name), 'red')
            return

        with open(os.path.join(DATA_PATH, dump_file_name), 'wb') as f:
            pickle.dump(self, f)
        cprint('Dumped: {}'.format(dump_file_name), 'blue')

    def load(self):
        load_file_name = self.get_file_name_to_dump_and_load()
        try:
            with open(os.path.join(DATA_PATH, load_file_name), 'rb') as f:
                loaded: MultiLangChatDataLoader = pickle.load(f)
                self.chat_data_loader_list = loaded.chat_data_loader_list
            cprint('Loaded: {}'.format(load_file_name), 'green')
            return True
        except Exception as e:
            print(colored('Load Fail: {0}.\n'.format(load_file_name), 'red'), str(e))
            return False


if __name__ == '__main__':

    description_files = get_files_with_dir_path(DATA_PATH, 'Description')
    multi_lang_chat_data_loader = MultiLangChatDataLoader(
        path=description_files[0],
        label_condition_func=None,
        label_condition_args=tuple(),
        criteria_funcs=(have_enough_words(1), have_enough_words(1)),
        lang_func=li_classify_str,
    )

    for lang_chat_data_loader in multi_lang_chat_data_loader[{}]:
        for line in lang_chat_data_loader.lines:
            print({k: v for k, v in line.items() if k != 'img'})
        print(lang_chat_data_loader.label_dict)

    multi_lang_chat_data_loader.dump()
