# 2. Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования в последовательность
# кодов (не используя методы encode и decode) и определить тип, содержимое и длину соответствующих переменных.

def result(lst):
    for i in lst:
        i = eval(f"b'{i}'")
        print(type(i))
        print(i)
        print(len(i))


words = ['class', 'function', 'method']

result(words)
