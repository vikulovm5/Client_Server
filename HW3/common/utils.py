import json
from HW3.common.variables import MAX_PACKAGE_LENGTH, ENCODING


def get_message(client):
    enc_resp = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(enc_resp, bytes):
        json_resp = enc_resp.decode(ENCODING)
        response = json.loads(json_resp)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


def send_message(sock, message):
    json_msg = json.dumps(message)
    enc_msg = json_msg.encode(ENCODING)
    sock.send(enc_msg)
