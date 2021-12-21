import subprocess

process = []

while True:
    ACTION = input('Выберите действие: q - выход, s - запуск сервера и клиентов, x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        process.append(subprocess.Popen('python server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
        try:
            i = 0
            cl_number = int(input('Введите количество запускаемых клиентов'))
            if i < cl_number:
                param = f'python client.py -n Client{i+1}'
                process.append(subprocess.Popen(param, creationflags=subprocess.CREATE_NEW_CONSOLE))
                i += 1
        except ValueError:
            print('Необходимо ввести число')

    if ACTION == 'x':
        while process:
            process.pop().kill()
