import logging
import log.client_log_config
import argparse
import sys
from PyQt5.QtWidgets import QApplication

from common.variables import *
from common.errors import ServerError
from common.decors import Log
from client.database import ClientDB
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog


logger = logging.getLogger('client')


@Log()
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
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


if __name__ == '__main__':
    server_address, server_port, client_name = arg_parser()
    client_app = QApplication(sys.argv)

    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()

        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    logger.info(f'Запущен клиент с параметрами:  адрес сервера: {server_address} , порт: {server_port}, имя '
                f'пользователя: {client_name}')

    database = ClientDB(client_name)

    try:
        transport = ClientTransport(server_port, server_address, database, client_name)
    except ServerError as err:
        print(err.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа - {client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
