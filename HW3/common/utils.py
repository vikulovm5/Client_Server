from HW3.errors import WrongDataReceived, NotADict
from HW3.decors import Log
import json
import sys
from HW3.common.variables import MAX_PACKAGE_LENGTH, ENCODING

sys.path.append('../')


@Log()
def get_message(client):
    enc_resp = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(enc_resp, bytes):
        json_resp = enc_resp.decode(ENCODING)
        response = json.loads(json_resp)
        if isinstance(response, dict):
            return response
        raise WrongDataReceived
    raise WrongDataReceived


@Log()
def send_message(sock, message):
    if not isinstance(message, dict):
        raise NotADict
    json_msg = json.dumps(message)
    enc_msg = json_msg.encode(ENCODING)
    sock.send(enc_msg)
