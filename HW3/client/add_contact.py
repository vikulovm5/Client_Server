from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import sys
import logging

sys.path.append('../')

logger = logging.getLogger('client')


class AddContactDialog(QDialog):
    """
    Диалог добавления контактов. Предлагает пользователю список пользователей и добавляет выбранный в контакты.
    """

    def __init__(self, s, database):
        super().__init__()
        self.s = s
        self.database = database

        self.setFixedSize(350, 120)
        self.setWindowTitle('Выберите контакт для добавления: ')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт для добавления: ', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_refresh = QPushButton('Обновить список', self)
        self.btn_refresh.setFixedSize(100, 30)
        self.btn_refresh.move(60, 60)

        self.btn_ok = QPushButton('Добавить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.possible_contacts_update()
        self.btn_refresh.clicked.connect(self.update_possible_contacts)

    def possible_contacts_update(self):
        """
        Метод заполнения списка возможных контактов. Добавляет в список всех зарегистрированных пользователей,
        кроме уже добавленных и самого себя.
        """

        self.selector.clear()
        contacts_list = set(self.database.get_contacts())
        users_list = set(self.database.get_users())
        users_list.remove(self.s.username)
        self.selector.addItems(users_list - contacts_list)

    def update_possible_contacts(self):
        """
        Метод, обновляющий список возможных контактов.
        """

        try:
            self.s.user_list_update()
        except OSError:
            pass
        else:
            logger.debug('Обновление списка пользователей выполнено')
            self.possible_contacts_update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from database import ClientDB

    database = ClientDB('user1')
    from transport import ClientTransport

    transport = ClientTransport(7777, '127.0.0.1', database, 'user1')
    window = AddContactDialog(transport, database)
    window.show()
    app.exec_()
