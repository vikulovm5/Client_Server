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
import json
from socket import *
import argparse
import logging
import HW3.log.server_log_config
from errors import WrongDataReceived
import sys
from HW3.common.variables import *
from HW3.common.utils import get_message, send_message


server_logger = logging.getLogger('server')


def process_client_message(msg):
    server_logger.debug(f'Разбор сообщения клиента: {msg}')
    if ACTION in msg and msg[ACTION] == PRESENCE and TIME in msg and USER in msg and msg[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    return {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    return parser


def main():
    parser = arg_parser()
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    if not 1023 < listen_port < 65536:
        server_logger.critical(
            f'Некорректно указан номер порта: {listen_port}'
            f'Номер порта должен быть в диапазоне от 1024 до 65535'
        )
        sys.exit(1)
    server_logger.info(
        f'Запущен сервер с номером порта: {listen_port}'
        f'Адрес подключения: {listen_address}'
        f'При отсутствии указания адреса, соединения принимаются с любых адресов'
    )

    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind((listen_address, listen_port))
    s.listen(MAX_CONNECTIONS)

    while True:
        client, client_address = s.accept()
        server_logger.info(f'Установлено соединение с клиентом {client_address}')
        try:
            cl_msg = get_message(client)
            server_logger.debug(f'Получено сообщение клиента: {cl_msg}')
            response = process_client_message(cl_msg)
            server_logger.info(f'Сформирован ответ клиенту: {response}')
            send_message(client, response)
            server_logger.debug(f'Соединение с клиентом {client_address} закрывается')
            client.close()
        except json.JSONDecodeError:
            server_logger.error(f'Ошибка декодирования json клиента {client_address}')
            client.close()
        except WrongDataReceived:
            server_logger.error(f'Принятые данные от клиента {client_address} некорректны')
            client.close()


if __name__ == '__main__':
    main()
