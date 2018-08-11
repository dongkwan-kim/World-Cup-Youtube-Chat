from custom_path import DATA_PATH
from DataLoader import MultiChatDataLoader
from utill import get_files_with_dir_path, try_except, have_enough_words, iso2sec
from WriterWrapper import WriterWrapper
from typing import Callable, Tuple
from collections import OrderedDict
from termcolor import cprint, colored
from collections import Counter, defaultdict
import os
import pickle
import matplotlib.pyplot as plt
import itertools

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

    def is_dump_possible(self):
        return self.get_file_name_to_dump_and_load() not in os.listdir(DATA_PATH)

    def get_stats(self):
        author_lang_dict = defaultdict(list)
        message_lang_dict = defaultdict(list)
        for data_loader in self:
            match_tuple = (data_loader.get_label('country_1'), data_loader.get_label('country_2'))
            author_lang_dict[match_tuple] += [line_dict['lang_author_name'] for line_dict in data_loader]
            message_lang_dict[match_tuple] += [line_dict['lang_message'] for line_dict in data_loader]

        return {
            'author_lang': {k: Counter([(vv if vv else None) for vv in v]) for k, v in author_lang_dict.items()},
            'message_lang': {k: Counter([(vv if vv else None) for vv in v]) for k, v in message_lang_dict.items()},
        }

    def export_stats(self):
        stats = self.get_stats()
        for name, lang_dict in stats.items():
            lines, fieldnames = [], []
            for match, counter in lang_dict.items():
                lines.append({'match': match, **dict(counter)})
                fieldnames += list(counter.keys())
            fieldnames = ['match'] + [lang for lang, _ in sorted(list(Counter(fieldnames).items()), key=lambda x: -x[1])]

            writer = WriterWrapper(os.path.join(DATA_PATH, 'lang_dist_{}'.format(name)), fieldnames)
            for line_dict in lines:
                writer.write_row(line_dict)
            writer.close()

    def get_match_to_series(self):
        match_to_series = defaultdict(lambda: defaultdict(list))
        for data_loader in self:
            match_tuple = (
                data_loader.get_label('country_1'),
                data_loader.get_label('country_2'),
                data_loader.get_label('main'),
                data_loader[0]['author_name'],
            )
            time_bin_to_lang_list = defaultdict(list)
            for line_dict in data_loader:
                lang_message = line_dict['lang_message']
                time_stamp_sec = iso2sec(line_dict['time_stamp'])
                if lang_message:
                    time_bin_to_lang_list[int(time_stamp_sec % 60)].append(lang_message)
            total_lang_list = list(set(itertools.chain(*time_bin_to_lang_list.values())))
            time_bin_to_lang_counter = {
                time_bin: Counter(lang_list) for time_bin, lang_list in time_bin_to_lang_list.items()
            }
            for time_bin, lang_counter in sorted(time_bin_to_lang_counter.items(), key=lambda x: x[0]):
                match_to_series[match_tuple]['time_bin'].append(time_bin)
                for lang in total_lang_list:
                    match_to_series[match_tuple][lang].append(lang_counter[lang] if lang in lang_counter else 0)
        return match_to_series

    def plot_match_to_series(self, options=None):
        # https://matplotlib.org/users/pyplot_tutorial.html
        options = options if options else {}
        num_of_plots = None if 'num_of_plots' not in options else options['num_of_plots']
        with_en = True if 'with_en' not in options else options['with_en']
        show_or_save = 'show' if 'show_or_save' not in options else options['show_or_save']

        match_to_series = self.get_match_to_series()
        for match, series in match_to_series.items():

            plt_kwargs_list = []
            for label, values in sorted(series.items(), key=lambda kv: -sum(kv[1])):
                if label == 'time_bin':
                    continue
                plt_kwargs_list.append({
                    'x': series['time_bin'],
                    'y': values,
                    'label': label,
                })

            if not with_en:
                plt_kwargs_list = [kw for kw in plt_kwargs_list if kw['label'] != 'en']

            if num_of_plots:
                plt_kwargs_list = plt_kwargs_list[:num_of_plots]

            plots = []
            for plt_kwargs in plt_kwargs_list:
                _plot = plt.plot(plt_kwargs['x'], plt_kwargs['y'], label=plt_kwargs['label'])
                plots.append(_plot[0])

            plt.xlabel('min')
            plt.title('_'.join(match[:-1]))
            plt.legend(handles=plots)

            if show_or_save == 'show':
                plt.show()
            else:
                plots_path = '../data/plots/{}'.format(self.info)
                if not os.path.isdir(plots_path):
                    os.mkdir(plots_path)
                plt.savefig('{}/{}.png'.format(plots_path, '_'.join(match[:-1])))

            plt.clf()
            plt.cla()
            plt.close()


if __name__ == '__main__':

    description_files = get_files_with_dir_path(DATA_PATH, 'Description')
    multi_lang_chat_data_loader = MultiLangChatDataLoader(
        path=description_files[0],
        label_condition_func=None,
        label_condition_args=tuple(),
        criteria_funcs=(have_enough_words(1), have_enough_words(1)),
        lang_func=ld.detect,
    )

    if multi_lang_chat_data_loader.is_dump_possible():
        multi_lang_chat_data_loader.dump()

    MODE = 'PLOT'
    if MODE == 'PLOT':
        multi_lang_chat_data_loader.plot_match_to_series({
            'num_of_plots': 3,
            'with_en': True,
            'show_or_save': 'save',
        })
    elif MODE == 'STATS':
        multi_lang_chat_data_loader.export_stats()
