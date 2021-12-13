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
from socket import *
import sys
import select
import time
import argparse
import json
import logging
import HW3.log.server_log_config
from HW3.errors import WrongDataReceived
from HW3.common.variables import *
from HW3.common.utils import *
from HW3.decors import Log


logger = logging.getLogger('server')


@Log()
def process_client_message(msg, messages_list, client):
    logger.debug(f'Разбор сообщения клиента: {msg} ')
    if ACTION in msg and msg[ACTION] == PRESENCE and TIME in msg and USER in msg and msg[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    elif ACTION in msg and msg[ACTION] == MESSAGE and TIME in msg and MESSAGE_TEXT in msg:
        messages_list.append((msg[ACCOUNT_NAME], msg[MESSAGE_TEXT]))
        return
    else:
        send_message(client, {
            RESPONSE: 400,
            ERROR: 'Bad Request'
        })
        return


@Log()
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    if not 1023 < listen_port < 65536:
        logger.critical(
            f'Некорректно указан номер порта: {listen_port} '
            f'Номер порта должен быть в диапазоне от 1024 до 65535'
        )
        sys.exit(1)

    return listen_address, listen_port


def main():
    listen_address, listen_port = arg_parser()

    logger.info(
        f'Запущен сервер с номером порта: {listen_port} '
        f'Адрес подключения: {listen_address} '
        f'При отсутствии указания адреса, соединения принимаются с любых адресов'
    )

    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind((listen_address, listen_port))
    s.settimeout(1)

    clients = []
    messages = []

    s.listen(MAX_CONNECTIONS)

    while True:
        try:
            client, client_address = s.accept()
        except OSError:
            pass
        else:
            logger.info(f'Установлено соединение с клиентом {client_address} ')
            clients.append(client)

        receive_data_lst = []
        send_data_lst = []
        error_lst = []

        try:
            if clients:
                receive_data_lst, send_data_lst, error_lst = select.select(clients, clients, [], 0)
        except OSError:
            pass

        if receive_data_lst:
            for client_with_msg in receive_data_lst:
                try:
                    process_client_message(get_message(client_with_msg), messages, client_with_msg)
                except:
                    logger.info(f'Клиент {client_with_msg.getpeername()} отключен от сервера')
                    clients.remove(client_with_msg)

        if messages and send_data_lst:
            msg = {
                ACTION: MESSAGE,
                SENDER: messages[0][0],
                TIME: time.time(),
                MESSAGE_TEXT: messages[0][1]
            }
            del messages[0]
            for waiting_cl in send_data_lst:
                try:
                    send_message(waiting_cl, msg)
                except:
                    logger.info(f'Клиент {waiting_cl.getpeername()} отключен от сервера')
                    waiting_cl.close()
                    clients.remove(waiting_cl)


if __name__ == '__main__':
    main()
