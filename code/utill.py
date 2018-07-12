import os
import sys
from time import sleep
from selenium import webdriver
import configparser


def try_except_with_sleep(f):
    def wrapper(*args, **kwargs):
        try:
            sleep(0.6)
            f(*args, **kwargs)
            sleep(0.6)
        except:
            print('P{0} | Error: {1}'.format(os.getpid(), f.__name__), file=sys.stderr)
    return wrapper


def get_driver(config_file_path: str) -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    config = configparser.ConfigParser()
    config.read(config_file_path)
    driver = webdriver.Chrome(config['DRIVER']['PATH'], chrome_options=chrome_options)
    driver.implicitly_wait(3)
    return driver


def iso2sec(iso: str) -> int:
    """
    :param iso: e.g. 1:01:02
    :return: sec in int
    """
    arr = iso.split(':')
    len_arr = len(arr)
    if len_arr <= 3:
        arr = ['0'] * (3 - len_arr) + arr
    else:
        raise Exception('len_arr > 3, arr: {}'.format(arr))

    return int(arr[0]) * 60 * 60 + int(arr[1]) * 60 + int(arr[2])
