import threading
import sys
import os
import json
import logging
import time
import configparser
import log.server_log_config
from errors import WrongDataReceived
from socket import *
import select
import argparse
from HW3.common.variables import *
from HW3.common.utils import *
from HW3.decors import Log
from descripts import Port
from metaclasses import ServerMaker
from server_db import ServerDB
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem


logger = logging.getLogger('server')


new_connection = False
conflag_lock = threading.Lock()


@Log()
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(threading.Thread, metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port

        self.database = database
        self.clients = []
        self.messages = []
        self.names = dict()
        super().__init__()

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
            except OSError as err:
                logger.error(f'Ошибка сокета: {err}')

            if receive_data_lst:
                for client_with_msg in receive_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_msg), client_with_msg)
                    except OSError:
                        logger.info(f'Клиент {client_with_msg.getpeername()} отключен от сервера')
                        for name in self.names:
                            if self.names[name] == client_with_msg:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_msg)

            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    logger.info(f'Связь с клиентом {message[DESTINATION]} прервана ')
                    self.clients.remove(self.names[message[DESTINATION]])
                    self.database.user_logout(message[DESTINATION])
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
                client_ip, client_port = client.getpeername()
                self.database.user_login(msg[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
                with conflag_lock:
                    new_connection = True
            else:
                response = RESPONSE_400
                response[ERROR] = 'Такое имя пользователя уже существует '
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return

        elif ACTION in msg and msg[ACTION] == MESSAGE and DESTINATION in msg and TIME in msg and SENDER in msg and MESSAGE_TEXT in msg:
            self.messages.append(msg)
            self.database.process_message(msg[SENDER], msg[DESTINATION])
            return

        elif ACTION in msg and msg[ACTION] == EXIT and ACCOUNT_NAME in msg:
            self.database.user_logout(msg[ACCOUNT_NAME])
            logger.info(f'Клиент {msg[ACCOUNT_NAME]} отключился от сервера ')
            self.clients.remove(self.names[msg[ACCOUNT_NAME]])
            self.names[msg[ACCOUNT_NAME]].close()
            del self.names[ACCOUNT_NAME]
            with conflag_lock:
                new_connection = True
            return

        elif ACTION in msg and msg[ACTION] == GET_CONTACTS and USER in msg and self.names[msg[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(msg[USER])
            send_message(client, response)

        elif ACTION in msg and msg[ACTION] == ADD_CONTACT and ACCOUNT_NAME in msg and USER in msg and self.names[msg[USER]] == client:
            self.database.add_contact(msg[USER], msg[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        elif ACTION in msg and msg[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in msg and USER in msg and self.names[msg[USER]] == client:
            self.database.remove_contact(msg[USER], msg[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        elif ACTION in msg and msg[ACTION] == USERS_REQUEST and ACCOUNT_NAME in msg and self.names[msg[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            send_message(client, response)

        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен '
            send_message(client, response)
            return


def main():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    listen_address, listen_port = arg_parser(config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    database = ServerDB(
        os.path.join(config['SETTINGS']['Database_path'], config['SETTINGS']['Database_file'])
    )

    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server is working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(['SETTINGS']['Default_port'])
        config_window.ip.insert(['SETTINGS']['Listen_address'])
        config_window.save_btn.clicked.connect(save_server_config())


    def save_server_config():
        global config_window
        msg = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            msg.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    msg.information(config_window, 'OK', 'Настройки сохранены')
            else:
                msg.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()


if __name__ == '__main__':
    main()
