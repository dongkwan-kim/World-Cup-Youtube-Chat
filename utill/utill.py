import os
import sys
from time import sleep
from selenium import webdriver
from typing import List
import configparser


def get_readlines(path) -> List[str]:
    return [line for line in open(path, 'r', encoding='utf-8').readlines()]


def country_to_code(path) -> list:
    return [tuple(x.strip().split('\t')) for x in open(path, encoding='utf-8').readlines()]


def get_files(path: str, search_text: str = None) -> list:
    return [f for f in os.listdir(path) if (not search_text) or (search_text in f)]


def get_files_with_dir_path(path: str, search_text: str = None) -> list:
    return [os.path.join(path, f) for f in get_files(path, search_text)]


def try_except(f):
    """
    :param f: function that use this decorator
    :return:
    """
    def wrapper(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except Exception as e:
            print('P{0} | Error: {1}'.format(os.getpid(), f.__name__), e, file=sys.stderr)

    return wrapper

def try_except_with_sleep(f):
    """
    :param f: function that use this decorator
    :return:
    """
    def wrapper(*args, **kwargs):
        try:
            sleep(0.6)
            f(*args, **kwargs)
            sleep(0.6)
        except Exception as e:
            print('P{0} | Error: {1}'.format(os.getpid(), f.__name__), e, file=sys.stderr)

    return wrapper


def get_driver(config_file_path: str) -> webdriver.Chrome:
    """
    :param config_file_path: path of .ini file
        config.ini
            [Driver]
            PATH="Something"
    :return: webdriver.Chrome
    """
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
