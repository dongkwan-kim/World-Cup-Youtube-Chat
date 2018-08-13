from collections import defaultdict
from typing import List, Tuple, Dict
from custom_path import DATA_PATH
from lang import MultiLangChatDataLoader, li_classify_str
from utill import get_files_with_dir_path, have_enough_words
from WriterWrapper import WriterWrapper

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
        # self.get_img_hash()
        return (self.name, self.get_img_hash()).__hash__()

    def __repr__(self):
        return '_'.join([self.name, self.get_img_hash()])


def get_user_to_match_to_lines(_multi_lang_chat_data_loader) -> Dict[YoutubeUser, Dict[tuple, list]] :
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
    for user, match_to_lines in _sorted_user_to_match_to_lines:
        row = {
            'name': user.name,
            'img': user.img,
            'matches': len(match_to_lines.keys()),
            'lines': sum([len(x) for x in match_to_lines.values()]),
        }
        row.update(_user_to_lang_to_count[user])
        writer.write_row(row)


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
    
    MODE = 'STATS'
    if MODE == 'STATS':
        export_user_stats(
            multi_lang_chat_data_loader,
            sorted_user_to_match_to_lines,
            user_to_lang_to_count,
            lang_list
        )
