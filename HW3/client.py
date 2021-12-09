"""
1. Реализовать простое клиент-серверное взаимодействие по протоколу JIM (JSON instant messaging): клиент
отправляет запрос серверу; сервер отвечает соответствующим кодом результата. Клиент и сервер должны быть реализованы
в виде отдельных скриптов, содержащих соответствующие функции. Функции клиента: сформировать presence-сообщение;
отправить сообщение серверу; получить ответ сервера; разобрать сообщение сервера; параметры командной строки скрипта
client.py <addr> [<port>]: addr — ip-адрес сервера; port — tcp-порт на сервере, по умолчанию 7777. Функции сервера:
принимает сообщение клиента; формирует ответ клиенту; отправляет ответ клиенту; имеет параметры командной строки: -p
<port> — TCP-порт для работы (по умолчанию использует 7777); -a <addr> — IP-адрес для прослушивания (по умолчанию
слушает все доступные адреса).
"""

import sys
import json
from socket import *
import time
import argparse
import logging
import HW3.log.client_log_config
from HW3.common.variables import *
from HW3.common.utils import get_message, send_message
from HW3.errors import MissingField
from HW3.decors import Log


logger = logging.getLogger('client')


@Log()
def create_request(account_name='Guest'):
    req = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    logger.debug(f'Сгенерирован {PRESENCE} запрос для пользователя {account_name} ')
    return req


@Log()
def process_ans(message):
    logger.debug(f'Разбор сообщения сервера: {message} ')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise MissingField(RESPONSE)


@Log()
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, nargs='?')
    return parser


def main():

    parser = arg_parser()
    namespace = parser.parse_args(sys.argv[1:])
    server_addr = namespace.addr
    server_port = namespace.port

    if not 1023 < server_port < 65536:
        logger.critical(
            f'Номер порта клиента некорректен: {server_port} '
            f'Номер порта должен быть в диапазоне от 1024 до 65535 '
        )
        sys.exit(1)

    logger.info(
        f'Запущен клиент с параметрами: '
        f'Адрес сервера: {server_addr}, порт: {server_port} '
    )

    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((server_addr, server_port))
        msg = create_request()
        send_message(s, msg)
        answer = process_ans(get_message(s))
        logger.info(f'Ответ сервера: {answer} ')
    except json.JSONDecodeError:
        logger.error('Ошибка декодирования json ')
    except ConnectionRefusedError:
        logger.critical(f'Ошибка подключения к серверу {server_addr}:{server_port} ')
    except MissingField as missing_err:
        logger.error(f'В ответе сервера отсутствует поле: {missing_err.missing_field} ')


if __name__ == '__main__':
    main()
