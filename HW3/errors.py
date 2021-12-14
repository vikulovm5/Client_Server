class WrongDataReceived(Exception):
    def __str__(self):
        return 'Принято некорректное сообщение от пользователя '


class ServerError(Exception):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class NotADict(Exception):
    def __str__(self):
        return 'В аргумент функции подается словарь (dict) '


class MissingField(Exception):
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'В словаре отсутствует поле {self.missing_field} '
