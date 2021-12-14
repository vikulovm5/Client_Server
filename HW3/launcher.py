import subprocess

process = []

while True:
    ACTION = input('Выберите действие: q - выход, s - запуск сервера и клиентов, x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        process.append(subprocess.Popen('python server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(2):
            process.append(subprocess.Popen('python server.py -m send', creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(2):
            process.append(subprocess.Popen('python server.py -m listen', creationflags=subprocess.CREATE_NEW_CONSOLE))
    if ACTION == 'x':
        while process:
            process.pop().kill()
