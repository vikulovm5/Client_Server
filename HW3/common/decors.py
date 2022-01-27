import sys
import logging
from functools import wraps

import HW3.log.client_log_config
import HW3.log.server_log_config


if sys.argv[0].find('client') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


class Log:
    def __call__(self, func_log):
        @wraps(func_log)
        def log_saver(*args, **kwargs):
            res = func_log(*args, **kwargs)
            logger.debug(
                f'Вызов функции {func_log.__name__} с параметрами {args}, {kwargs} '
            )
            return res
        return log_saver()
