"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона. Меняться должен только
последний октет каждого адреса. По результатам проверки должно выводиться соответствующее сообщение.
"""


from HW1.task1 import host_ping, address_check


def host_range_ping(get_list=False):
    while True:
        subnet = input('Введите адрес: ')
        try:
            addr_start = address_check(subnet)
            last_oct = int(subnet.split('.')[3])
            break
        except Exception as e:
            print(e)
    while True:
        addr_stop = input('Введите число проверяемых адресов: ')
        if addr_stop.isnumeric():
            if (last_oct + int(addr_stop)) > 256:
                print(f'Максимальное число адресов - {256 - last_oct}')
            else:
                break
        else:
            print('Введите число. ')
    host_list = []
    [host_list.append(str(addr_start + i)) for i in range(int(addr_stop))]
    if not get_list:
        host_ping(host_list)
    else:
        return host_ping(host_list, True)


if __name__ == '__main__':
    host_range_ping()
