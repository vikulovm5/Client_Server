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
import sys
from HW3.metaclasses import ClientMaker


logger = logging.getLogger('client')


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
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

        msg_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: msg
        }
        logger.debug(f'Сформирован словарь сообщения: {msg_dict}')
        try:
            send_message(self.sock, msg_dict)
            logger.info(f'Отправлено сообщение пользователю {to_user} ')
        except:
            logger.critical('Соединение с сервером прервано ')
            exit(1)

    def user_interaction(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_msg()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                try:
                    send_message(self.sock, self.exit_msg())
                except:
                    pass
                print('Завершение соединения ')
                logger.info('Соединение прервано пользователем ')
                time.sleep(1)
                break
            else:
                print('Неизветная команда. help - показать возможные команды ')

    def print_help(self):
        print('Возможные команды: ')
        print('message - отправить сообщение ')
        print('help - вывести подсказки по командам ')
        print('exit - выход из программы ')


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def msg_from_server(self):
        while True:
            try:
                msg = get_message(self.sock)
                if ACTION in msg and msg[ACTION] == MESSAGE and SENDER in msg and DESTINATION in msg and MESSAGE_TEXT in msg and msg[DESTINATION] == self.account_name:
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
        receiver = ClientReader(client_name, s)
        receiver.daemon = True
        receiver.start()

        sender = ClientSender(client_name, s)
        sender.daemon = True
        sender.start()
        logger.debug('Процессы запущены ')

        while True:
            time.sleep(1)
            if receiver.is_alive() and sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
