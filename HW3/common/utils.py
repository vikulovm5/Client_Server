import json
import sys
from common.decors import Log
from common.variables import *
sys.path.append('../')


@Log()
def get_message(client):
    """
    Функция приёма сообщений от удалённых компьютеров.
    Принимает сообщения JSON, декодирует полученное сообщение
    и проверяет что получен словарь.
    :param client: сокет для передачи данных.
    :return: словарь - сообщение.
    """

    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    json_response = encoded_response.decode(ENCODING)
    response = json.loads(json_response)
    if isinstance(response, dict):
        return response
    else:
        raise TypeError


@Log()
def send_message(sock, message):
    """
    Функция отправки словарей через сокет.
    Кодирует словарь в формат JSON и отправляет через сокет.
    :param sock: сокет для передачи
    :param message: словарь для передачи
    :return: ничего не возвращает
    """

    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
