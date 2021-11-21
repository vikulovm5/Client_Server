"""
1. Задание на закрепление знаний по модулю CSV. Написать скрипт, осуществляющий выборку определенных данных из
файлов info_1.txt, info_2.txt, info_3.txt и формирующий новый «отчетный» файл в формате CSV. Для этого: Создать
функцию get_data(), в которой в цикле осуществляется перебор файлов с данными, их открытие и считывание данных. В
этой функции из считанных данных необходимо с помощью регулярных выражений извлечь значения параметров «Изготовитель
системы», «Название ОС», «Код продукта», «Тип системы». Значения каждого параметра поместить в соответствующий
список. Должно получиться четыре списка — например, os_prod_list, os_name_list, os_code_list, os_type_list. В этой же
функции создать главный список для хранения данных отчета — например, main_data — и поместить в него названия
столбцов отчета в виде списка: «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы». Значения для
этих столбцов также оформить в виде списка и поместить в файл main_data (также для каждого файла); Создать функцию
write_to_csv(), в которую передавать ссылку на CSV-файл. В этой функции реализовать получение данных через вызов
функции get_data(), а также сохранение подготовленных данных в соответствующий CSV-файл; Проверить работу программы
через вызов функции write_to_csv().
"""
import csv


def get_data(lst):
    main_data = [['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']]
    for file in lst:
        with open(file, 'r', encoding='utf-8') as infile:
            os_prod_list, os_name_list, os_code_list, os_type_list = [], [], [], []
            result = [os_prod_list, os_name_list, os_code_list, os_type_list]
            lines = infile.readlines()
            for line in lines:
                if line.startswith('Изготовитель системы'):
                    dealer_name = line.split('- ')[1].replace('\n', '')
                elif line.startswith('Название ОС'):
                    os_name = line.split('- ')[1].replace('\n', '')
                elif line.startswith('Код продукта'):
                    prod_code = line.split('- ')[1].replace('\n', '')
                elif line.startswith('Тип системы'):
                    sys_type = line.split('- ')[1].replace('\n', '')
                else:
                    print('Данных нет')

            os_prod_list.append(dealer_name)
            os_name_list.append(os_name)
            os_code_list.append(prod_code)
            os_type_list.append(sys_type)

            main_data.append(result)

    return main_data


def write_to_csv(lst):
    data = get_data(files)

    with open('report.csv', 'w', encoding='utf-8', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
        for line in data:
            writer.writerow(line)


files = ['info_1.txt', 'info_2.txt', 'info_3.txt']
write_to_csv(files)
