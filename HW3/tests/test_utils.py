from common.utils import *
from common.variables import *
import sys
import os
import unittest
import json
sys.path.append(os.path.join(os.getcwd(), '..'))


class TestSocket:
    def __init__(self, test):
        self.test = test
        self.enc_msg = None
        self.rec_msg = None

    def send(self, sent_msg):
        json_msg = json.dumps(self.test)
        self.enc_msg = json_msg.encode(ENCODING)
        self.rec_msg = sent_msg

    def recv(self, max_len):
        json_msg = json.dumps(self.test)
        return json_msg.encode(ENCODING)


class TestUtils(unittest.TestCase):
    ref = {
        ACTION: PRESENCE,
        TIME: 2.2,
        USER: {
            ACCOUNT_NAME: 'test_user'
        }
    }

    accept = {RESPONSE: 200}
    error = {RESPONSE: 400, ERROR: 'Bad Request'}

    def test_send(self):
        test_socket = TestSocket(self.ref)
        send_message(test_socket, self.ref)
        self.assertEqual(test_socket.enc_msg, test_socket.rec_msg)
        self.assertRaises(TypeError, send_message, test_socket, "wrong_dictionary")

    def test_get(self):
        sock_accept = TestSocket(self.accept)
        sock_error = TestSocket(self.error)
        self.assertEqual(get_message(sock_accept), self.accept)
        self.assertEqual(get_message(sock_error), self.error)


if __name__ == '__main__':
    unittest.main()
