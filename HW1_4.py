# 4. Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления в
# байтовое и выполнить обратное преобразование (используя методы encode и decode).

def code_recode(lst):
    for i in lst:
        i_enc = str.encode(i, encoding='utf-8')
        print(i_enc)
        i_dec = bytes.decode(i_enc, encoding='utf-8')
        print(i_dec)


words = ['разработка', 'администрирование', 'protocol', 'standard']

code_recode(words)
