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
import sys
from HW3.common.variables import *
from HW3.common.utils import get_message, send_message


def process_client_message(msg):
    if ACTION in msg and msg[ACTION] == PRESENCE and TIME in msg and USER in msg and msg[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    return {
        RESPONDEFAULT_IP_ADDRESSSE: 400,
        ERROR: 'Bad Request'
    }


def main():
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        print('После параметра -\'p\' необходимо указать номер порта.')
        sys.exit(1)
    except ValueError:
        print('Номер порта должен быть в диапазоне от 1024 до 65535')
        sys.exit(1)

    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''

    except IndexError:
        print('После параметра -\'a\' необходимо указать адрес')
        sys.exit(1)

    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind((listen_address, listen_port))
    s.listen(MAX_CONNECTIONS)

    while True:
        client, client_address = s.accept()
        try:
            cl_msg = get_message(client)
            print(cl_msg)
            response = process_client_message(cl_msg)
            send_message(client, response)
            client.close()
        except (ValueError, json.JSONDecodeError):
            print('Ошибка декодирования')
            client.close()


if __name__ == '__main__':
    main()
