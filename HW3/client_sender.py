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
from HW3.errors import MissingField, ServerError
from HW3.decors import Log


logger = logging.getLogger('client')


@Log()
def msg_from_server(msg):
    if ACTION in msg and msg[ACTION] == MESSAGE and SENDER in msg and MESSAGE_TEXT in msg:
        print(f'Получено сообщение от пользователя {msg[SENDER]}: '
              f'{msg[MESSAGE_TEXT]}')
        logger.info(f'Получено сообщение от пользователя {msg[SENDER]}: '
                    f'{msg[MESSAGE_TEXT]}')
    else:
        logger.error(f'Получено некорректное сообщение от сервера: {msg} ')


@Log()
def create_msg(sock, account_name='Guest'):
    msg = input('Введите сообщение. Для завершения работы введите \'exit\'.')
    if msg == 'exit':
        sock.close()
        logger.info('Пользователь завершил работу.')
        print('Работа завершена. ')
        sys.exit(0)
    msg_dict = {
        ACTION: MESSAGE,
        TIME: time.time(),
        ACCOUNT_NAME: account_name,
        MESSAGE_TEXT: msg
    }
    logger.debug(f'Сформирован словарь сообщения: {msg_dict}')
    return msg_dict


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
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise MissingField(RESPONSE)


@Log()
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, nargs='?')
    parser.add_argument('-m', '--mode', default='send', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_addr = namespace.addr
    server_port = namespace.port
    client_mode = namespace.mode

    if not 1023 < server_port < 65536:
        logger.critical(
            f'Номер порта клиента некорректен: {server_port} '
            f'Номер порта должен быть в диапазоне от 1024 до 65535 '
        )
        sys.exit(1)

    if client_mode not in ('listen', 'send'):
        logger.critical(f'Указанный режим работы - {client_mode} не относится к допустимым: listen, send. ')
        sys.exit(1)

    return server_addr, server_port, client_mode


def main():

    server_addr, server_port, client_mode = arg_parser()

    logger.info(
        f'Запущен клиент с параметрами: '
        f'Адрес сервера: {server_addr}, порт: {server_port}, режим работы: {client_mode} '
    )

    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((server_addr, server_port))
        send_message(s, create_request())
        answer = process_ans(get_message(s))
        logger.info(f'Ответ сервера: {answer} ')
        print('Соединение с сервером установлено. ')
    except json.JSONDecodeError:
        logger.error('Ошибка декодирования json ')
    except ServerError as err:
        logger.error(f'Ошибка сервера: {err.text} ')
    except ConnectionRefusedError:
        logger.critical(f'Ошибка подключения к серверу {server_addr}:{server_port} ')
    except MissingField as missing_err:
        logger.error(f'В ответе сервера отсутствует поле: {missing_err.missing_field} ')
    else:
        if client_mode == 'send':
            print('Режим работы - отправка сообщений. ')
        else:
            print('Режим работы - прием сообщений. ')
        while True:
            if client_mode == 'send':
                try:
                    send_message(s, create_msg(s))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    logger.error(f'Соединение с сервером {server_addr} прервано. ')
                    sys.exit(1)
            if client_mode == 'listen':
                try:
                    msg_from_server(get_message(s))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    logger.error(f'Соединение с сервером {server_addr} прервано. ')
                    sys.exit(1)


if __name__ == '__main__':
    main()
