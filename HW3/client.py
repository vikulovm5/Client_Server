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
from HW3.common.variables import *
from HW3.common.utils import get_message, send_message
import time
from socket import *


def create_request(account_name='Guest'):
    req = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    return req


def process_ans(message):
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ValueError


def main():
    try:
        server_addr = sys.argv[1]
        server_port = int(sys.argv[2])
        if 1024 > server_port > 65535:
            raise ValueError
    except IndexError:
        server_addr = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
    except ValueError:
        print('Номер порта должен быть в диапазоне от 1024 до 65535')
        sys.exit(1)

    s = socket(AF_INET, SOCK_STREAM)
    s.connect((server_addr, server_port))
    msg = create_request()
    send_message(s, msg)
    try:
        answer = process_ans(get_message(s))
        print(answer)
    except (ValueError, json.JSONDecodeError):
        print('Ошибка декодирования')


if __name__ == '__main__':
    main()
