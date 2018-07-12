from utill import get_driver
from BaseCrawler import BaseCrawler
from WriterWrapper import WriterWrapper
from time import sleep
import os


DATA_PATH = '../data'


class VideoURLCrawler(BaseCrawler):

    def __init__(self, config_file_path: str, target_url: str):
        super().__init__(config_file_path)
        self.url = target_url
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

        self.driver.close()

        return r

    def export(self):
        writer = WriterWrapper(os.path.join(DATA_PATH, self.prefix), self.fieldnames)
        for line in self.run():
            writer.write_row(line)
        writer.close()


if __name__ == '__main__':
    crawler = VideoURLCrawler(
        './config.ini',
        'https://www.youtube.com/user/FIFATV/videos?live_view=503&sort=dd&view=2&shelf_id=0'
    )
    crawler.export()
