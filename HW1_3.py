# 3. Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в байтовом типе.

def result(lst):
    for i in lst:
        try:
            i = eval(f"b'{i}'")
        except SyntaxError:
            print(f'слово "{i}" невозможно записать в байтовом типе')


words = ['attribute', 'класс', 'функция', 'type']

result(words)
