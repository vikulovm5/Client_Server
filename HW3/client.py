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
import threading
import logging
import HW3.log.client_log_config
from HW3.common.variables import *
from HW3.common.utils import get_message, send_message
from HW3.errors import WrongDataReceived, MissingField, ServerError
from HW3.decors import Log


logger = logging.getLogger('client')


@Log()
def exit_msg(account_name):
    return {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: account_name
    }


@Log()
def msg_from_server(sock, my_username):
    while True:
        try:
            msg = get_message(sock)
            if ACTION in msg and msg[ACTION] == MESSAGE and SENDER in msg and DESTINATION in msg and MESSAGE_TEXT in msg and msg[DESTINATION] == my_username:
                print(f'Получено сообщение от пользователя {msg[SENDER]}: '
                      f'{msg[MESSAGE_TEXT]}')
                logger.info(f'Получено сообщение от пользователя {msg[SENDER]}: '
                            f'{msg[MESSAGE_TEXT]}')
            else:
                logger.error(f'Получено некорректное сообщение от сервера: {msg} ')
        except WrongDataReceived:
            logger.error('Ошибка декодирования ')
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
            logger.critical(f'Соединение с сервером прервано ')
            break


@Log()
def create_msg(sock, account_name='Guest'):
    to_user = input('Введите имя получателя. ')
    msg = input('Введите сообщение. ')

    msg_dict = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: to_user,
        TIME: time.time(),
        MESSAGE_TEXT: msg
    }
    logger.debug(f'Сформирован словарь сообщения: {msg_dict}')
    try:
        send_message(sock, msg_dict)
        logger.info(f'Отправлено сообщение пользователю {to_user} ')
    except:
        logger.critical('Соединение с сервером прервано ')
        sys.exit(1)


@Log()
def user_interaction(sock, username):
    print_help()
    while True:
        command = input('Введите команду: ')
        if command == 'message':
            create_msg(sock, username)
        elif command == 'help':
            print_help()
        elif command == 'exit':
            send_message(sock, exit_msg(username))
            print('Завершение соединения ')
            logger.info('Соединение прервано пользователем ')
            time.sleep(1)
            break
        else:
            print('Неизветная команда. help - показать возможные команды ')


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


def print_help():
    print('Поддерживаемые команды:')
    print('message - отправить сообщение. Получатель и текст будут запрошены отдельно.')
    print('help - подсказки команд')
    print('exit - выход из программы')


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
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_addr = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        logger.critical(
            f'Номер порта клиента некорректен: {server_port} '
            f'Номер порта должен быть в диапазоне от 1024 до 65535 '
        )
        sys.exit(1)

    return server_addr, server_port, client_name


def main():

    server_addr, server_port, client_name = arg_parser()

    print(f'Запущен мессенджер. Клиентский модудь. Пользователь: {client_name} ')
    if not client_name:
        client_name = input('Введите имя пользователя: ')

    logger.info(
        f'Запущен клиент с параметрами: '
        f'Адрес сервера: {server_addr}, порт: {server_port}, имя пользователя: {client_name} '
    )

    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((server_addr, server_port))
        send_message(s, create_request(client_name))
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
        receiver = threading.Thread(target=user_interaction, args=(s, client_name), daemon=True)
        receiver.start()

        user_interface = threading.Thread(target=user_interaction, args=(s, client_name), daemon=True)
        user_interface.start()
        logger.debug('Процессы запущены ')

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
