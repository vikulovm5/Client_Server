import json
from socket import *
import time
import argparse
import threading
import logging
import HW3.log.client_log_config
from HW3.common.variables import *
from HW3.common.utils import *
from HW3.errors import WrongDataReceived, MissingField, ServerError
from HW3.decors import Log
import sys
from HW3.metaclasses import ClientMaker
from client_db import ClientDB


logger = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def exit_msg(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    def create_msg(self):
        to_user = input('Введите имя получателя. ')
        msg = input('Введите сообщение. ')

        with database_lock:
            if not self.database.check_user(to_user):
                logger.error(f'Попытка отправить сообщение незарегистрированному адресату: {to_user}')

        msg_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: msg
        }
        logger.debug(f'Сформирован словарь сообщения: {msg_dict}')

        with database_lock:
            self.database.save_message(self.account_name, to_user, msg)

        with sock_lock:
            try:
                send_message(self.sock, msg_dict)
                logger.info(f'Отправлено сообщение пользователю {to_user} ')
            except OSError as err:
                if err.errno:
                    logger.critical('Соединение с сервером прервано ')
                    exit(1)
                else:
                    logger.error('Таймаут соединения. Сообщение не передано. ')

    def user_interaction(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_msg()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.exit_msg())
                    except Exception as e:
                        print(e)
                        pass
                    print('Завершение соединения ')
                    logger.info('Соединение прервано пользователем ')
                time.sleep(1)
                break
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            elif command == 'edit':
                self.edit_contacts()
            elif command == ' history':
                self.print_history()

            else:
                print('Неизветная команда. help - показать возможные команды ')

    def print_help(self):
        print('Возможные команды: ')
        print('message - отправить сообщение ')
        print('history - история сообщений ')
        print('contacts - список контактов ')
        print('edit - редактирование списка контактов ')
        print('help - вывести подсказки по командам ')
        print('exit - выход из программы ')

    def print_history(self):
        ask = input('in - показать входящие, out - исходящие, Enter - все: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            if ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователя: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')

    def edit_contact(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock , self.account_name, edit)
                    except ServerError:
                        logger.error('Не удалось отправить информацию на сервер.')


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def msg_from_server(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    msg = get_message(self.sock)
                except WrongDataReceived:
                    logger.error('Ошибка декодирования ')
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Соединение с сервером прервано ')
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    logger.critical(f'Соединение с сервером прервано ')
                    break
                else:
                    if ACTION in msg and msg[ACTION] == MESSAGE and SENDER in msg and DESTINATION in msg and MESSAGE_TEXT in msg and msg[DESTINATION] == self.account_name:
                        print(f'Получено сообщение от пользователя {msg[SENDER]}: '
                              f'{msg[MESSAGE_TEXT]}')
                        with database_lock:
                            try:
                                self.database.save_message(msg[SENDER], self.account_name, msg[MESSAGE_TEXT])
                            except Exception as e:
                                print(e)
                                logger.error('Ошибка взаимодействия с базой данных')

                        logger.info(f'Получено сообщение от пользователя {msg[SENDER]}: '
                                    f'{msg[MESSAGE_TEXT]}')
                    else:
                        logger.error(f'Получено некорректное сообщение от сервера: {msg} ')


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


def contacts_list_request(sock, name):
    logger.debug(f'Запрос списка контактов для пользователя {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    logger.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_message(sock)
    logger.debug(f'Получен ответ {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def add_contact(sock, username, contact):
    logger.debug(f'Создание контка {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта. ')
    print('Контакт создан. ')


def user_list_request(sock, username):
    logger.debug(f'Запрос списка известных пользователей {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def remove_contact(sock, username, contact):
    logger.debug(f'Создание контакта {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления контакта')
    print('Контакт удалён')


def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        logger.error('Ошибка запроса списка известных пользователей')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        logger.error('Ошибка запроса списка контактов')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():

    server_addr, server_port, client_name = arg_parser()

    print(f'Запущен мессенджер. Клиентский модудь. Пользователь: {client_name} ')
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

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
        exit(1)
    except ServerError as err:
        logger.error(f'Ошибка сервера: {err.text} ')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        logger.critical(f'Ошибка подключения к серверу {server_addr}:{server_port} ')
        exit(1)
    except MissingField as missing_err:
        logger.error(f'В ответе сервера отсутствует поле: {missing_err.missing_field} ')
        exit(1)
    else:

        database = ClientDB(client_name)
        database_load(s, database, client_name)

        sender = ClientSender(client_name, s, database)
        sender.daemon = True
        sender.start()
        logger.debug('Процессы запущены ')

        receiver = ClientReader(client_name, s, database)
        receiver.daemon = True
        receiver.start()

        while True:
            time.sleep(1)
            if receiver.is_alive() and sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
