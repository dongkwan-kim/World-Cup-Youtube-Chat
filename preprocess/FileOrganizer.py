from path import DATA_PATH, CHAT_PATH
from utill.utill import get_files, country_to_code, get_match_result
from utill.WriterWrapper import WriterWrapper
from typing import List
from termcolor import cprint
import re
import os


FILE_REGEX = [
    '(\w+) vs (\w+)\s?[:|-]\s?(\w+)',
    '(\w+) v. (\w+)\s?[:|-]\s?(\w+)',
    '(\w+) - (\w+)\s?[:|-]\s?(\w+)',
    '(\w+) v. (\w+)\s?[:|-]?\s?(\w+)',
]


class FileOrganizer:

    def __init__(self, file_names: List[str]):
        self.file_names = file_names
        self.preprocessed_file_names = []
        self.match_result = []
        self.prefix = 'Description'
        self.fieldnames = []

    def preprocess_by_replace(self, rules: List[tuple], line_list: List[str]=None):
        """
        :param line_list: list of str
        :param rules: list of tuple (old_text, new_text)
        :return:
        """
        r = []
        line_list = line_list or self.file_names
        for line in line_list:
            for rule in rules:
                line = line.replace(rule[0], rule[1])
            r.append(line)
        return r

    def organize_by_regex(self, rules: List[tuple], regex_list: List[str]) -> List[dict]:

        self.fieldnames += ['main', 'country_1', 'country_2', 'file_name']
        self.preprocessed_file_names = self.preprocess_by_replace(rules)

        organized = []
        not_matched_files = []

        for file_name, preprocessed_file_name in zip(self.file_names, self.preprocessed_file_names):
            for regex_str in regex_list:
                regex = re.compile(regex_str)
                match_obj = regex.search(preprocessed_file_name)

                if match_obj:

                    # main = 'post' or country_x (which is the main country in the conference)
                    (country_1, country_2, main) = match_obj.groups()
                    (country_1, country_2) = tuple(sorted([country_1, country_2]))
                    main = 'post' if 'post' in preprocessed_file_name.lower() else main

                    organized.append({
                        'country_1': country_1,
                        'country_2': country_2,
                        'main': main,
                        'file_name': file_name,
                    })
                    print(country_1, country_2, main, file_name)
                    break
            else:
                not_matched_files.append(file_name)

        for not_matched in not_matched_files:
            cprint('Not matched file: {0}'.format(not_matched), 'yellow')

        return organized

    def add_match_result(self, rules: List[tuple], match_results: List[str]):

        self.fieldnames = ['winner'] + self.fieldnames

        match_result_return = []
        match_results = [line.strip().split('\t') for line in self.preprocess_by_replace(rules, match_results)]

        for score, country_1, country_2, match_date in match_results:
            # now, score = 'int:int'
            score = score if len(score) < 4 else re.search(r'\((.*?)\)', score).group(1)
            [sc1, sc2] = [int(sc) for sc in score.split(':')]
            if sc1 > sc2:
                winner = country_1
            elif sc1 < sc2:
                winner = country_2
            else:
                winner = 'DRAW'

            (country_1, country_2) = tuple(sorted([country_1, country_2]))
            match_result_return.append({
                'country_1': country_1,
                'country_2': country_2,
                'winner': winner,
            })

        self.match_result = match_result_return
        return match_result_return

    def export_organized(self, rules: List[tuple], regex_list: List[str]):

        organized = self.organize_by_regex(rules, regex_list)
        match_to_winner = {(dct['country_1'], dct['country_2']): dct['winner'] for dct in self.match_result}

        result = []
        for obj in organized:
            match = (obj['country_1'], obj['country_2'])
            obj['winner'] = match_to_winner[match]
            result.append(obj)

        writer = WriterWrapper(os.path.join(DATA_PATH, self.prefix), self.fieldnames)
        for line in result:
            writer.write_row(line)
        writer.close()


if __name__ == '__main__':

    chat_files = get_files(CHAT_PATH, 'Chat')
    to_code = country_to_code(os.path.join(DATA_PATH, 'country_to_code.txt'))
    match_result = get_match_result(os.path.join(DATA_PATH, 'match_result.txt'))

    file_organizer = FileOrganizer(chat_files)
    file_organizer.preprocess_by_replace(to_code)
    file_organizer.add_match_result(to_code, match_result)
    file_organizer.export_organized(to_code, FILE_REGEX)
