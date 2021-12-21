"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или
ip-адресом. В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью функции
ip_address().
"""

import platform
import subprocess
import time
from ipaddress import ip_address
from pprint import pprint


results = {'Reachable': "", 'Unreachable': ""}


def address_check(value):
    try:
        ip = ip_address(value)
    except ValueError:
        raise Exception('Не является ip адресом')
    return ip


def host_ping(hosts, get_list=False):
    for host in hosts:
        try:
            ipv4 = address_check(host)
        except Exception as e:
            print(f'{host} - {e}, воспринимаю как имя домена')
            ipv4 = host

        param = '-n' if platform.system().lower() == 'windows' else '-c'
        args = ["ping", param, '1', str(ipv4)]
        response = subprocess.Popen(args, stdout=subprocess.PIPE)
        if response.wait() == 0:
            results['Reachable'] += f'{str(ipv4)}\n'
            res_string = f'{str(ipv4)} - Узел доступен'
        else:
            results['Unreachable'] += f'{ipv4}\n'
            res_string = f'{str(ipv4)} - Узел недоступен'
        if not get_list:
            print(res_string)
    if get_list:
        return results


if __name__ == '__main__':
    hosts = ['www.google.com', '192.168.0.1', 'www.wikipedia.org', '192.168.4.202']
    start = time.time()
    host_ping(hosts)
    end = time.time()
    print(f'total time: {int(end - start)}')

