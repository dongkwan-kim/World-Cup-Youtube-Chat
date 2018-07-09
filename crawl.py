# -*- coding: utf-8 -*-

from selenium import webdriver
from WriterWrapper import WriterWrapper
from time import sleep, time
from multiprocessing import Pool
from orderedset import OrderedSet
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
        self.prefix = None
        self.fieldnames = []
        self.config_file_path = config_file_path

    def run(self):
        raise NotImplementedError


class VideoURLCrawler(BaseCrawler):

    def __init__(self, config_file_path: str):
        super().__init__(config_file_path)
        self.url = 'https://www.youtube.com/user/FIFATV/videos?live_view=503&sort=dd&view=2&shelf_id=0'
        self.fieldnames = ['title', 'video_url', 'time']
        self.prefix = 'VideoURL'

    def run(self):
        self.driver = get_driver(self.config_file_path)
        self.driver.get(self.url)
        r = []

        for _ in range(6):
            sleep(1)
            self.driver.execute_script('return window.scrollBy(0,1000)')

        for div in self.driver.find_elements_by_css_selector('#dismissable'):

            anchor = div.find_element_by_id('video-title')
            play_time = div.find_element_by_class_name('ytd-thumbnail-overlay-time-status-renderer').text

            title = anchor.text
            video_url = anchor.get_attribute('href')
            r.append({
                'title': title,
                'video_url': video_url,
                'time': play_time,
            })
            print(title, video_url, play_time)

        return r

    def export(self):
        writer = WriterWrapper(os.path.join(DATA_PATH, self.prefix), self.fieldnames)
        for line in self.run():
            writer.write_row(line)
        writer.close()


class ChatCrawler(BaseCrawler):

    def __init__(self, config_file_path: str):
        super().__init__(config_file_path)
        self.urls = []
        self.prefix = 'Chat'
        self.fieldnames = ['time_stamp', 'author_name', 'message', 'img']

    def get_urls(self):
        video_url_filename = [os.path.join(DATA_PATH, f) for f in os.listdir(DATA_PATH)
                              if f.startswith('VideoURL')][0]
        reader = csv.DictReader(open(video_url_filename, 'r', encoding='utf-8'))
        return list(reader)

    def turn_off_autoplay(self):
        btn_turn_off = self.driver.find_element_by_id('improved-toggle')
        btn_turn_off.click()

    def mute(self):
        btn_mute = self.driver.find_element_by_class_name('ytp-mute-button')
        btn_mute.click()

    def speed_up(self):
        btn_setting = self.driver.find_element_by_css_selector('#movie_player > div.ytp-chrome-bottom > \
                                                                div.ytp-chrome-controls > div.ytp-right-controls > \
                                                                button.ytp-button.ytp-settings-button.ytp-hd-quality-badge')
        btn_setting.click()
        btn_speed = self.driver.find_element_by_css_selector('#ytp-id-17 > div > div > div:nth-child(2)')
        btn_speed.click()
        sleep(0.5)
        btn_speed_2x = self.driver.find_element_by_css_selector('#ytp-id-17 > div > div > div:nth-child(7)')
        btn_speed_2x.click()
        sleep(1)

    def show_timestamp(self):
        btn_top = self.driver.find_element_by_css_selector('#overflow')
        btn_top.click()
        sleep(0.5)
        btn_bottom = self.driver.find_element_by_css_selector('#items > ytd-menu-service-item-renderer')
        btn_bottom.click()
        sleep(1)

    def run_one(self, url_dict: dict):
        title, video_url, play_time = url_dict['title'], url_dict['video_url'], url_dict['time']
        time_in_sec = iso2sec(play_time)

        self.driver = get_driver(self.config_file_path)
        self.driver.get(video_url)

        sleep(5)
        self.mute()
        self.turn_off_autoplay()
        self.speed_up()

        iframe = self.driver.find_element_by_css_selector('#chatframe')
        self.driver.switch_to.frame(iframe)

        self.show_timestamp()

        r_set = OrderedSet()
        interval = 120
        time_to_crawl_in_one_epoch = 0
        epochs = int(time_in_sec/2/interval) + 1
        for i in range(epochs):
            sleep(interval - time_to_crawl_in_one_epoch)
            start_time = time()
            for chat_emt in self.driver.find_elements_by_css_selector('yt-live-chat-text-message-renderer'):
                content_emt = chat_emt.find_element_by_id('content')
                time_stamp = content_emt.find_element_by_id('timestamp')
                author_name = content_emt.find_element_by_id('author-name')
                message = content_emt.find_element_by_id('message')
                try:
                    img_src = chat_emt.find_element_by_id('img').get_attribute('src')
                except:
                    print(time_stamp.text, author_name.text, message.text)
                    img_src = 'Error'
                r_set.add((time_stamp.text, author_name.text, message.text, img_src))
            time_to_crawl_in_one_epoch = time() - start_time
            print('P{5} | {0} | Interval {1}/{4}, {2} chats, {3}s'.format(
                title, i + 1, len(r_set), time_to_crawl_in_one_epoch, epochs, os.getpid()
            ))

        self.driver.switch_to.default_content()

        return [{
            'time_stamp': tup[0],
            'author_name': tup[1],
            'message': tup[2],
            'img': tup[3],
        } for tup in r_set]

    def export_one(self, url_dict):
        writer = WriterWrapper(os.path.join(DATA_PATH, self.prefix + '_' + url_dict['title']), self.fieldnames)
        for line in self.run_one(url_dict):
            writer.write_row(line)
        writer.close()

    def export(self, processes=5):
        print('Start crawling with {0} processes'.format(processes))
        pool = Pool(processes=processes)
        pool.map(self.export_one, self.get_urls())
        print('Crawling ends')


if __name__ == '__main__':
    crawler = ChatCrawler('./config.ini')
    crawler.export()
