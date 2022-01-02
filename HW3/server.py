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
from descripts import Port
from metaclasses import ServerMaker


logger = logging.getLogger('server')


@Log()
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_address, listen_port):
        self.addr = listen_address
        self.port = listen_port

        self.clients = []
        self.messages = []
        self.names = dict()

    def init_sock(self):
        logger.info(
            f'Запущен сервер с номером порта: {self.port} '
            f'Адрес подключения: {self.addr} '
            f'При отсутствии указания адреса, соединения принимаются с любых адресов'
        )

        s = socket(AF_INET, SOCK_STREAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        s.bind((self.addr, self.port))
        s.settimeout(1)

        self.sock = s
        self.sock.listen()

    def main_loop(self):
        self.init_sock()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соединение с клиентом {client_address} ')
                self.clients.append(client)

            receive_data_lst = []
            send_data_lst = []
            error_lst = []

            try:
                if self.clients:
                    receive_data_lst, send_data_lst, error_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if receive_data_lst:
                for client_with_msg in receive_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_msg), client_with_msg)
                    except:
                        logger.info(f'Клиент {client_with_msg.getpeername()} отключен от сервера')
                        self.clients.remove(client_with_msg)

            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except:
                    logger.info(f'Связь с клиентом {message[DESTINATION]} прервана ')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    def process_message(self, msg, listen_socks):
        if msg[DESTINATION] in self.names and self.names[msg[DESTINATION]] in listen_socks:
            send_message(self.names[msg[DESTINATION]], msg)
            logger.info(f'Пользователю {msg[DESTINATION]} отправлено сообщение от пользователя {msg[SENDER]} ')
        elif msg[DESTINATION] in self.names and self.names[msg[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(f'Пользователь {msg[DESTINATION]} не зарегистрирован на сервере. Отправка сообщения невозможна ')

    def process_client_message(self, msg, client):
        logger.debug(f'Разбор сообщения клиента: {msg} ')

        if ACTION in msg and msg[ACTION] == PRESENCE and TIME in msg and USER in msg:
            if msg[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[msg[USER][ACCOUNT_NAME]] = client
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Такое имя пользователя уже существует '
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        elif ACTION in msg and msg[ACTION] == MESSAGE and DESTINATION in msg and TIME in msg and SENDER in msg and MESSAGE_TEXT in msg:
            self.messages.append(msg)
            return
        elif ACTION in msg and msg[ACTION] == EXIT and ACCOUNT_NAME in msg:
            self.clients.remove(self.names[msg[ACCOUNT_NAME]])
            self.names[msg[ACCOUNT_NAME]].close()
            del self.names[ACCOUNT_NAME]
            return
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен '
            send_message(client, response)
            return


def main():
    listen_address, listen_port = arg_parser()
    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
