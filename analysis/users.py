from collections import defaultdict
from typing import List, Tuple, Dict
from custom_path import DATA_PATH
from lang import MultiLangChatDataLoader, li_classify_str
from utill import get_files_with_dir_path, have_enough_words
from WriterWrapper import WriterWrapper
from pprint import pprint

# https://github.com/Mimino666/langdetect
import langdetect as ld


class YoutubeUser:

    def __init__(self, _name, _img):
        self.name: str = _name
        self.img: str = _img

    def get_img_hash(self):
        splited = self.img.split('/')
        return splited[3] + '_' + splited[-3]

    def __eq__(self, other):
        return (other.name == self.name) and (other.get_img_hash() == self.get_img_hash())

    def __hash__(self):
        return (self.name, self.get_img_hash()).__hash__()

    def __repr__(self):
        return '_'.join([self.name, self.get_img_hash()])

    def pseudo_eq(self, o):
        if isinstance(o, str):
            return self.name == o or self.img == o or self.get_img_hash() == o
        elif isinstance(o, YoutubeUser):
            return self == o
        else:
            raise TypeError


def get_user_to_match_to_lines(_multi_lang_chat_data_loader) -> Dict[YoutubeUser, Dict[tuple, list]]:
    _user_to_match_to_lines: Dict[YoutubeUser, Dict[tuple, list]] = defaultdict(lambda: defaultdict(list))
    for i, data_loader in enumerate(_multi_lang_chat_data_loader):
        match_tuple = (
            data_loader.get_label('country_1'),
            data_loader.get_label('country_2'),
            data_loader.get_label('main'),
            len(data_loader),
        )
        for line_dict in data_loader:
            author_name = line_dict['author_name']
            img = line_dict['img']
            youtube_user = YoutubeUser(author_name, img)
            _user_to_match_to_lines[youtube_user][match_tuple].append(line_dict)
    return _user_to_match_to_lines


def get_user_to_lang_to_count(_lang_list, _sorted_user_to_match_to_lines):
    _user_to_lang_to_count: Dict[YoutubeUser, Dict[str, int]] = defaultdict(lambda: {lang: 0 for lang in _lang_list})
    for _user, _match_to_lines in _sorted_user_to_match_to_lines:
        for match, lines in _match_to_lines.items():
            for line in lines:
                _user_to_lang_to_count[_user][line['lang_message']] += 1
    return _user_to_lang_to_count


def export_user_stats(_multi_lang_chat_data_loader, _sorted_user_to_match_to_lines, _user_to_lang_to_count, _lang_list):
    fieldnames = ['name', 'matches', 'lines'] + _lang_list + ['img']
    writer = WriterWrapper('../Data/Users_' + _multi_lang_chat_data_loader.info, _fieldnames=fieldnames)
    for _user, _match_to_lines in _sorted_user_to_match_to_lines:
        row = {
            'name': _user.name,
            'img': _user.img,
            'matches': len(_match_to_lines.keys()),
            'lines': sum([len(x) for x in _match_to_lines.values()]),
        }
        row.update(_user_to_lang_to_count[_user])
        writer.write_row(row)


def query_match_to_lines_of_user(target_user: YoutubeUser or str,
                                 _user_to_match_to_lines: Dict[YoutubeUser, Dict[tuple, list]]):
    if isinstance(target_user, str):
        for user, match_to_lines in _user_to_match_to_lines.items():
            if user.pseudo_eq(target_user):
                return match_to_lines
    else:
        raise NotImplementedError


if __name__ == '__main__':

    description_files = get_files_with_dir_path(DATA_PATH, 'Description')
    multi_lang_chat_data_loader = MultiLangChatDataLoader(
        path=description_files[0],
        label_condition_func=None,
        label_condition_args=tuple(),
        criteria_funcs=(have_enough_words(1), have_enough_words(1)),
        lang_func=li_classify_str,
    )

    if multi_lang_chat_data_loader.is_dump_possible():
        multi_lang_chat_data_loader.dump()

    user_to_match_to_lines = get_user_to_match_to_lines(multi_lang_chat_data_loader)

    lang_list = multi_lang_chat_data_loader.get_lang_list()['message_lang']
    sorted_user_to_match_to_lines = sorted(user_to_match_to_lines.items(), key=lambda x: -len(x[1].keys()))
    user_to_lang_to_count = get_user_to_lang_to_count(lang_list, sorted_user_to_match_to_lines)

    MODE = 'QUERY'
    if MODE == 'STATS':
        export_user_stats(
            multi_lang_chat_data_loader,
            sorted_user_to_match_to_lines,
            user_to_lang_to_count,
            lang_list
        )

    elif MODE == 'QUERY':
        user_something = 'Elena Yatkina'
        match_to_lines_of_user = query_match_to_lines_of_user(user_something, user_to_match_to_lines)
        for match, lines in match_to_lines_of_user.items():
            print('# ' + '_'.join(map(str, match)))
            for line in lines:
                print('\t', line['lang_message'], line['message'])
