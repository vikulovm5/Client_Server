from client import *
from common.variables import *
import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))


class TestClient(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_request(self):
        res = {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}
        req = create_request()
        req[TIME] = 1.1
        self.assertEqual(req, res)

    def test_process_ans_positive(self):
        self.assertEqual(process_ans({RESPONSE: 200}), '200 : OK')

    def test_process_answer_negative(self):
        self.assertEqual(process_ans({RESPONSE: 400, ERROR: 'Bad request'}), '400 : Bad request')

    def test_process_answer_error(self):
        self.assertRaises(ValueError, process_ans, {ERROR: 'Bad request'})


if __name__ == '__main__':
    unittest.main()