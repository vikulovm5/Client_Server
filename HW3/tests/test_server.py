from server import *
from common.variables import *
import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))


class TestServer(unittest.TestCase):
    error = {RESPONSE: 400, ERROR: 'Bad Request'}
    accept = {RESPONSE: 200}
    ref = {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}

    def test_request(self):
        self.assertEqual(process_client_message(self.ref), self.accept)

    def test_without_act(self):
        self.ref.pop(ACTION)
        self.assertEqual(process_client_message(self.ref), self.error)

    def test_wrong_act(self):
        self.ref[ACTION] = 'wrong action'
        self.assertEqual(process_client_message(self.ref), self.error)

    def test_without_time(self):
        self.ref.pop(TIME)
        self.assertEqual(process_client_message(self.ref), self.error)

    def test_without_user(self):
        self.ref.pop(USER)
        self.assertEqual(process_client_message(self.ref), self.error)

    def test_wrong_acc_name(self):
        wrong_ref = {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'wrong'}}
        self.assertEqual(process_client_message(wrong_ref), self.error)


if __name__ == '__main__':
    unittest.main()
