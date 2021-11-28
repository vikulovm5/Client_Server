# 5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из байтовового в строковый тип на
# кириллице.

import subprocess


def sub_ping(param):
    subproc_ping = subprocess.Popen(param, stdout=subprocess.PIPE)
    for line in subproc_ping.stdout:
        line = line.decode('cp866').encode('utf-8')
        print(line.decode('utf-8'))


args = ['ping', '-n', '5', 'yandex.ru']  # т.к. использую русскоязычный win10 вместо параметра '-c' использовал '-n'
args_2 = ['ping', '-n', '5', 'yandex.ru']

sub_ping(args)
sub_ping(args_2)
