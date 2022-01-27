import socket
import sys
import logging
from functools import wraps
sys.path.append('../')
import log.client_log_config
import log.server_log_config


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


def login_required(func):
    def checker(*args, **kwargs):
        from server.core import MessageProcessor
        from common.variables import ACTION, PRESENCE
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True
            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            if not found:
                raise TypeError
        return func(*args, **kwargs)
    return checker
