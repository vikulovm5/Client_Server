import sys
import os
import logging
from HW3.common.variables import LOGGING_LEVEL
sys.path.append('../')

client_form = logging.Formatter('%(asctime)s %(levelname)-8s %(filename)s %(message)s')

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_log')

stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(client_form)
stream_handler.setLevel(logging.INFO)
log_file = logging.FileHandler(PATH, encoding='utf-8')
log_file.setFormatter(client_form)

logger = logging.getLogger('client')
logger.addHandler(stream_handler)
logger.addHandler(log_file)
logger.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    logger.critical('Критическая ошибка')
    logger.error('Ошибка')
    logger.info('Информационное сообщение')
    logger.debug('Отладочная информация')
