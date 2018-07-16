from utill import get_driver
from BaseCrawler import BaseCrawler
from WriterWrapper import WriterWrapper
from time import sleep
import os


DATA_PATH = '../data'


class VideoURLCrawler(BaseCrawler):

    def __init__(self, config_file_path: str, target_url: str, number_of_scroll: int=6):
        """
        :param config_file_path: path of .ini file
            config.ini
                [Driver]
                PATH="Something"
        :param target_url: the url of video list.
        :param number_of_scroll: number of scrolls to load a video list.
        """
        super().__init__(config_file_path)
        self.url = target_url
        self.fieldnames = ['title', 'video_url', 'time']
        self.prefix = 'VideoURL'
        self.number_of_scroll = number_of_scroll

    def run(self, search_text: str=None) -> list:
        """
        :param search_text: text to search
        :return: list of videos that contain 'search_text'
        """
        self.driver = get_driver(self.config_file_path)
        self.driver.get(self.url)
        r = []

        for _ in range(self.number_of_scroll):
            sleep(1)
            self.driver.execute_script('return window.scrollBy(0,1000)')

        for div in self.driver.find_elements_by_css_selector('#dismissable'):

            anchor = div.find_element_by_id('video-title')
            play_time = div.find_element_by_class_name('ytd-thumbnail-overlay-time-status-renderer').text

            title = anchor.text
            video_url: str = anchor.get_attribute('href')
            if (not search_text) or (search_text in title.lower()):
                r.append({
                    'title': title,
                    'video_url': video_url,
                    'time': play_time,
                })
                print(title, video_url, play_time)

        self.driver.close()

        return r

    def export(self, search_text: str=None):
        """
        :param search_text: text to search
        """
        writer = WriterWrapper(os.path.join(DATA_PATH, self.prefix), self.fieldnames)
        for line in self.run(search_text=search_text):
            writer.write_row(line)
        writer.close()


if __name__ == '__main__':
    crawler = VideoURLCrawler(
        config_file_path='./config.ini',
        target_url='https://www.youtube.com/user/FIFATV/videos',
        number_of_scroll=50,
    )
    crawler.export(search_text='conference')
