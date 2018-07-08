# -*- coding: utf-8 -*-

from selenium import webdriver
from WriterWrapper import WriterWrapper
import configparser
from time import sleep


def get_driver(config_file_path: str) -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    config = configparser.ConfigParser()
    config.read(config_file_path)
    driver = webdriver.Chrome(config['DRIVER']['PATH'], chrome_options=chrome_options)
    driver.implicitly_wait(3)
    return driver


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
            sleep(0.5)
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
        writer = WriterWrapper('./data/VideoURL', self.fieldnames)
        for line in self.run():
            writer.write_row(line)
        writer.close()


class ChatCrawler(BaseCrawler):

    def __init__(self, config_file_path: str):
        super().__init__(config_file_path)

    def run(self):
        self.driver = get_driver(self.config_file_path)


if __name__ == '__main__':
    crawler = VideoURLCrawler('./config.ini')
    crawler.run()
