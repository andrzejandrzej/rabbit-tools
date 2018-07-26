# -*- coding: utf-8 -*-

import logging.config
import os
import sys
from contextlib import contextmanager


ETC_DIR = '/etc/rabbit_tools'
HOME_DIR = os.path.expanduser('~/.rabbit_tools')


def answer_yes_no(msg):
    positive_answers = ['y', 't', 'yes', 'ok']
    negative_answers = ['n', 'no']
    answer = raw_input(msg + ' (y/n)' + '\n')
    if not answer or answer.lower() in positive_answers:
        return True
    elif answer.lower() in negative_answers:
        return False
    else:
        return None


@contextmanager
def log_exceptions():
    logger = logging.getLogger(__name__)
    logging.config.fileConfig('/home/andrzej/.rabbit_tools/rabbit_tools.conf',
                              disable_existing_loggers=False)
    try:
        yield
    except Exception:
        logger.exception('Exception was raised.')
        raise


@contextmanager
def simple_logger():
    logger = logging.getLogger(__name__)
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format="%(levelname)s - %(message)s")
    try:
        yield
    except Exception:
        logger.exception('Exception was raised when creating config file.')
