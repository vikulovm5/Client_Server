# 6. Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое программирование», «сокет»,
# «декоратор». Проверить кодировку файла по умолчанию. Принудительно открыть файл в формате Unicode и вывести его
# содержимое.

from pathlib import Path


def writing(lst):
    with open('test_file.txt', 'w') as f_n:
        f_n.writelines([str(line) + '\n' for line in lst])
        print(f_n)


def reading(file):
    path = Path(file)
    path.write_text(path.read_text(encoding='cp1251'), encoding='utf-8')
    with open(path) as f_n:
        for el_str in f_n:
            print(el_str, end='')


strings = ['сетевое программирование', 'сокет', 'декоратор']

writing(strings)
reading('test_file.txt')
