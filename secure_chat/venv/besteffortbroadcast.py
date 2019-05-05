from perfectpointtopointlinks import PerfectPointToPointLinks
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto import Random
from base64 import b64encode, b64decode


class BestEffortBroadcast:

    def __init__(self, process_id, addr_str, callback, arg_callback):
        self.address = addr_str
        self.deliver_call_back = callback
        self.arg_callback = arg_callback
        self.links = PerfectPointToPointLinks(port=process_id, addr_str=addr_str, arg_callback=self.deliver)

    def close(self):
        self.links.close()

    def deliver(self, sender_id, message):
        if message is not None:
            self.deliver_call_back((sender_id, message), self.arg_callback)

    def encrypt_message(self, a_message, publickey):
        c = PKCS1_v1_5.new(publickey)
        encoded_encrypted_msg = c.encrypt(b64encode(a_message.encode()))
        return encoded_encrypted_msg

    def broadcast(self, message, process_id_list):
        Random.atfork()
        for process_id in process_id_list.keys():
            temp = process_id_list.get(process_id)
            k = RSA.importKey(temp)
            msg = self.encrypt_message(message, k)
            print(len(msg))
            print(msg)
            self.links.send(process_id, self.address, msg)
