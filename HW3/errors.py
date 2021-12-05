class WrongDataReceived(Exception):
    def __str__(self):
        return 'Принято некорректное сообщение от пользователя'


class NotADict(Exception):
    def __str__(self):
        return 'В аргумент функции подается словарь (dict)'


class MissingField(Exception):
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'В словаре отсутствует поле {self.missing_field}'
