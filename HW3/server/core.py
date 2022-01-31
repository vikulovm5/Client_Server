import threading
import logging
import select
import socket
import json
import hmac
import binascii
import os
import sys
sys.path.append('../')
from common.metaclasses import ServerMaker
from common.descripts import Port
from common.variables import *
from common.utils import send_message, get_message
from common.decors import login_required

# Загрузка логера
logger = logging.getLogger('server')


class MessageProcessor(threading.Thread):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port

        self.database = database
        self.sock = None
        self.clients = []
        self.listen_sockets = None
        self.error_sockets = None
        self.running = True
        self.names = dict()
        super().__init__()

    def run(self):
        self.init_socket()

        while self.running:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соединение с клиентом {client_address} ')
                client.settimeout(5)
                self.clients.append(client)

            receive_data_lst = []
            send_data_lst = []
            error_lst = []

            try:
                if self.clients:
                    receive_data_lst, self.listen_sockets, self.error_sockets = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f'Ошибка сокета: {err.errno}')

            if receive_data_lst:
                for client_with_msg in receive_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_msg), client_with_msg)
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        logger.debug(f'Getting data from client exception.', exc_info=err)
                        self.clients.remove(client_with_msg)

    def remove_client(self, client):
        logger.info(f'Клиент {client.getpeername()} отключился от сервера')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        logger.info(
            f'Запущен сервер с номером порта: {self.port} '
            f'Адрес подключения: {self.addr} '
            f'При отсутствии указания адреса, соединения принимаются с любых адресов'
        )

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.addr, self.port))
        s.settimeout(1)

        self.sock = s
        self.sock.listen(MAX_CONNECTIONS)

    def process_message(self, msg):
        if msg[DESTINATION] in self.names and self.names[msg[DESTINATION]] in self.listen_sockets:
            send_message(self.names[msg[DESTINATION]], msg)
            logger.info(f'Пользователю {msg[DESTINATION]} отправлено сообщение от пользователя {msg[SENDER]} ')
        elif msg[DESTINATION] in self.names and self.names[msg[DESTINATION]] not in self.listen_sockets:
            logger.error(f'Связь с клиентом {msg[DESTINATION]} была потеряна. Отправка невозможна.')
            self.remove_client(self.names[msg[DESTINATION]])
        else:
            logger.error(f'Пользователь {msg[DESTINATION]} не зарегистрирован на сервере. Отправка сообщения невозможна ')

    @login_required
    def process_client_message(self, msg, client):
        logger.debug(f'Разбор сообщения клиента: {msg} ')

        if ACTION in msg and msg[ACTION] == PRESENCE and TIME in msg and USER in msg:
            self.authorize_user(msg, client)

        elif ACTION in msg and msg[ACTION] == MESSAGE and DESTINATION in msg and TIME in msg and SENDER in msg and MESSAGE_TEXT in msg and self.names[msg[SENDER]] == client:
            if msg[DESTINATION] in self.names:
                self.database.process_message(msg[SENDER], msg[DESTINATION])
                self.process_message(msg)
                try:
                    send_message(client, RESPONSE_200)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Пользователь не зарегистрирован на сервере'
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return

        elif ACTION in msg and msg[ACTION] == EXIT and ACCOUNT_NAME in msg and self.names[msg[ACCOUNT_NAME]] == client:
            self.remove_client(client)

        elif ACTION in msg and msg[ACTION] == GET_CONTACTS and USER in msg and self.names[msg[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(msg[USER])
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        elif ACTION in msg and msg[ACTION] == ADD_CONTACT and ACCOUNT_NAME in msg and USER in msg and self.names[msg[USER]] == client:
            self.database.add_contact(msg[USER], msg[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)

        elif ACTION in msg and msg[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in msg and USER in msg and self.names[msg[USER]] == client:
            self.database.remove_contact(msg[USER], msg[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)

        elif ACTION in msg and msg[ACTION] == USERS_REQUEST and ACCOUNT_NAME in msg and self.names[msg[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        elif ACTION in msg and msg[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in msg:
            response = RESPONSE_511
            response[DATA] = self.database.get_pubkey(msg[ACCOUNT_NAME])
            if response[DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Нет публичного ключа для данного пользователя'
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен '
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

    def authorize_user(self, message, sock):
        logger.debug(f'Start auth process for {message[USER]}')
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято'
            try:
                logger.debug(f'Имя занято, отправка {response}')
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_400
            response[ERROR] = 'Пользователь не зарегистрирован'
            try:
                logger.debug(f'Пользователь не зарегистрирован, отправка {response}')
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            logger.debug('Корректное имя пользователя, начата проверка пароля')
            message_auth = RESPONSE_511
            random_str = binascii.hexlify(os.urandom(64))
            message_auth[DATA] = random_str.decode('ascii')
            hash = hmac.new(self.database.get_hash(message[USER][ACCOUNT_NAME]), random_str, 'MD5')
            digest = hash.digest()
            logger.debug(f'Auth message = {message_auth}')
            try:
                send_message(sock, message_auth)
                ans = get_message(sock)
            except OSError as err:
                logger.debug('Error in auth, data: ', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[DATA])

            if RESPONSE in ans and ans[RESPONSE] == 511 and hmac.compare_digest(digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, RESPONSE_200)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])

                self.database.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY]
                )
            else:
                response = RESPONSE_400
                response[ERROR] = 'Неверный пароль'
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_list(self):
        for client in self.names:
            try:
                send_message(self.names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])
