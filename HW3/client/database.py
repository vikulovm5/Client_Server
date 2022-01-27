from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import os
import sys
sys.path.append('../')
from common.variables import *
import datetime


class ClientDB:
    class KnownUsers:
        def __init__(self, user):
            self.id = None
            self.username = user

    class MessageHistory:
        def __init__(self, contact, direction, message):
            self.id = None
            self.contact = contact
            self.direction = direction
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.name = contact

    def __init__(self, name):
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'client_{name}.db3'
        self.engine = create_engine(f'sqlite:///{os.path.join(path, filename)}', echo=False, pool_recycle=7200, connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        users = Table(
            'known_users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('username', String)
        )

        history = Table(
            'message_history', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('contact', String),
            Column('direction', String),
            Column('message', Text),
            Column('date', DateTime)
        )

        contacts = Table(
            'contacts', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String, unique=True)
        )

        self.metadata.create_all(self.engine)

        mapper(self.KnownUsers, users)
        mapper(self.MessageHistory, history)
        mapper(self.Contacts, contacts)

        sess = sessionmaker(bind=self.engine)
        self.session = sess()

        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def delete_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()
        self.session.commit()

    def add_users(self, users_list):
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, from_user, to_user, message):
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    def check_user(self, user):
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_history(self, contact):
        query = self.session.query(self.MessageHistory).filter_by(contact=contact)
        return [(history_row.contact, history_row.direction, history_row.message, history_row.date) for history_row in query.all()]


if __name__ == '__main__':
    db = ClientDB('test1')
    for i in ['test3', 'test4', 'test5']:
        db.add_contact(i)
    db.add_contact('test4')
    db.add_users(['test1', 'test2', 'test3', 'test4', 'test5'])
    db.save_message('test1', 'test2', f'Тестовое сообщение от {datetime.datetime.now()}')
    db.save_message('test2', 'test1', f'Тестовое сообщение 2 от {datetime.datetime.now()}')
    print(db.get_contacts())
    print(db.get_users())
    print(db.check_user('test1'))
    print(db.check_user('test10'))
    print(sorted(db.get_history('test2'), key=lambda item: item[3]))
    db.delete_contact('test4')
    print(db.get_contacts())
