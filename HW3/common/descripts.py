import logging
import sys

if sys.argv[0].find('client') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            logger.critical('Номер порта должен быть в диапазоне от 1024 до 65535 ')
            raise TypeError('Некорректный номер порта')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
