import sys
import os
import logging
import logging.handlers

sys.path.append('../')
from common.variables import LOGGING_LEVEL


server_form = logging.Formatter('%(asctime)s %(levelname)-8s %(filename)s %(message)s')

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.log')

stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(server_form)
stream_handler.setLevel(logging.INFO)
log_file = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf-8', interval=1, when='D')
log_file.setFormatter(server_form)

logger = logging.getLogger('server')
logger.addHandler(stream_handler)
logger.addHandler(log_file)
logger.setLevel(LOGGING_LEVEL)


if __name__ == '__main__':
    logger.critical('Критическая ошибка')
    logger.error('Ошибка')
    logger.debug('Отладочная информация')
    logger.info('Информационное сообщение')
