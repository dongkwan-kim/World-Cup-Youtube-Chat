from utill.utill import get_files, country_to_code
from utill.WriterWrapper import WriterWrapper
from typing import List
from termcolor import cprint
import re
import os


DATA_PATH = '../data'


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
        self.prefix = 'Description'
        self.fieldnames = ['country_1', 'country_2', 'main', 'file_name']

    def preprocess_by_replace(self, rules: List[tuple]):
        """
        :param rules: list of tuple (old_text, new_text)
        :return:
        """
        for file_name in self.file_names:
            for rule in rules:
                file_name = file_name.replace(rule[0], rule[1])
            self.preprocessed_file_names.append(file_name)

    def organize_by_regex(self, regex_list: List[str]) -> List[dict]:

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

    def export_organized(self, regex_list: List[str]):
        result = self.organize_by_regex(regex_list)
        writer = WriterWrapper(os.path.join(DATA_PATH, self.prefix), self.fieldnames)
        for line in result:
            writer.write_row(line)
        writer.close()


if __name__ == '__main__':

    chat_files = get_files(DATA_PATH, 'Chat')
    to_code = country_to_code(os.path.join(DATA_PATH, 'country_to_code.txt'))

    file_organizer = FileOrganizer(chat_files)
    file_organizer.preprocess_by_replace(to_code)
    file_organizer.export_organized(FILE_REGEX)
