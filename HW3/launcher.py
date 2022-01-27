import subprocess


def main():
    process = []

    while True:
        ACTION = input('Выберите действие: q - выход, s - запуск сервера и клиентов, x - закрыть все окна: ')

        if ACTION == 'q':
            break
        elif ACTION == 's':
            process.append(subprocess.Popen('python server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
        elif ACTION == 'k':
            print('Убедитесь, что на сервере зарегистрировано необходимо количество клиентов с паролем 123456')
            print('Первый запуск может быть достаточно долгим из-за генерации ключей')
            clients_count = int(
                input('Введите количество тестовых клиентов для запуска: '))
            # Запускаем клиентов:
            for i in range(clients_count):
                process.append(
                    subprocess.Popen(
                        f'python client.py -n test{i + 1} -p 123456',
                        creationflags=subprocess.CREATE_NEW_CONSOLE))
        elif ACTION == 'x':
            while process:
                process.pop().kill()


if __name__ == '__main__':
    main()
