# -*- coding: utf-8 -*-

from selenium import webdriver
from WriterWrapper import WriterWrapper
from time import sleep
import configparser
import csv
import os


DATA_PATH = './data'


def get_driver(config_file_path: str) -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    config = configparser.ConfigParser()
    config.read(config_file_path)
    driver = webdriver.Chrome(config['DRIVER']['PATH'], chrome_options=chrome_options)
    driver.implicitly_wait(3)
    return driver


def iso2sec(iso: str) -> int:
    arr = iso.split(':')
    len_arr = len(arr)
    if len_arr <= 3:
        arr = ['0'] * (3 - len_arr) + arr
    else:
        raise Exception('len_arr > 3, arr: {}'.format(arr))

    return int(arr[0]) * 60 * 60 + int(arr[1]) * 60 + int(arr[2])


class BaseCrawler:

    def __init__(self, config_file_path: str):
        self.driver = None
        self.config_file_path = config_file_path


class VideoURLCrawler(BaseCrawler):

    def __init__(self, config_file_path: str):
        super().__init__(config_file_path)
        self.url = 'https://www.youtube.com/user/FIFATV/videos?live_view=503&sort=dd&view=2&shelf_id=0'
        self.fieldnames = ['title', 'video_url', 'time']

    def run(self):
        self.driver = get_driver(self.config_file_path)
        self.driver.get(self.url)
        r = []

        for _ in range(6):
            sleep(1)
            self.driver.execute_script('return window.scrollBy(0,1000)')

        for div in self.driver.find_elements_by_css_selector('#dismissable'):

            anchor = div.find_element_by_id('video-title')
            time = div.find_element_by_class_name('ytd-thumbnail-overlay-time-status-renderer').text

            title = anchor.text
            video_url = anchor.get_attribute('href')
            r.append({
                'title': title,
                'video_url': video_url,
                'time': time,
            })
            print(title, video_url, time)

        return r

    def export(self):
        writer = WriterWrapper(os.path.join(DATA_PATH, 'VideoURL'), self.fieldnames)
        for line in self.run():
            writer.write_row(line)
        writer.close()


class ChatCrawler(BaseCrawler):

    def __init__(self, config_file_path: str):
        super().__init__(config_file_path)
        self.urls = []

    def get_urls(self):
        video_url_filename = [os.path.join(DATA_PATH, f) for f in os.listdir(DATA_PATH)
                              if f.startswith('VideoURL')][0]
        reader = csv.DictReader(open(video_url_filename, 'r', encoding='utf-8'))
        return list(reader)

    def run(self):
        for url_dict in self.get_urls():
            self.run_one(url_dict)
            exit()

    def run_one(self, url_dict: dict):
        title, video_url, time = url_dict['title'], url_dict['video_url'], url_dict['time']
        time_in_sec = iso2sec(time)

        self.driver = get_driver(self.config_file_path)
        self.driver.get(video_url)

        sleep(5)
        iframe = self.driver.find_element_by_css_selector('#chatframe')
        self.driver.switch_to.frame(iframe)

        # TODO: Implement here
        for emt in self.driver.find_elements_by_css_selector('yt-live-chat-text-message-renderer'):
            print(emt)

        self.driver.switch_to.default_content()


if __name__ == '__main__':
    crawler = ChatCrawler('./config.ini')
    crawler.run()
