from besteffortbroadcast import BestEffortBroadcast
import multiprocessing
from multiprocessing import Process
from base64 import b64decode, b64encode
import random
import socket
import json
import sys
import time

from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Hash import SHA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Cipher import PKCS1_v1_5

import threading

class ChatBox:
    def __init__(self, name, address, port):
        self.key_pair = RSA.generate(1024, Random.new().read)
        self.public_key = RSA.importKey(self.key_pair.publickey().exportKey('PEM'))
        self.private_key = RSA.importKey(self.key_pair.exportKey('PEM'))
        self.name = name
        self.addr = address
        self.port = port
        self.friend_list = {}
        self.key_list = {}
        self.approved = {}  # for authentication
        self.queue = multiprocessing.Queue()
        self.key_queue = multiprocessing.Queue()
        self.beb = BestEffortBroadcast(process_id=int(self.port), addr_str=self.addr,
                                       callback=self.chat_deliver, arg_callback=self.queue)
       
    def decrypt_message(self, encoded_encrypted_msg):
        c = PKCS1_v1_5.new(self.private_key)
        s = Random.get_random_bytes(128)
        print(encoded_encrypted_msg)
        print(len(encoded_encrypted_msg))
        decoded_decrypted_msg = c.decrypt(encoded_encrypted_msg, s)
        return decoded_decrypted_msg

    def chat_deliver(self, mesg, queue):
        Random.atfork()
        if mesg is not None:
            sender_id, message = mesg
            # If it is a client update message from server, update the friend list
            if int(sender_id) == -1:
                # Remove all elements from the queue and put the new update in
                while not self.queue.empty():
                    queue.get(block=False)
                message = json.loads(message)
                queue.put(message)
                # Update friend list for look up
                self.friend_list = message
                update = "Current people in group chat: {}".format(list(self.friend_list.values()))
                print("Server : {}".format(update))
            # If it is a notification from server, print the notification
            elif int(sender_id) == -2:
                print("Server : {}".format(message))
            # permission request
            elif int(sender_id) == -3:
                return
            # key update
            elif int(sender_id) == -4:
                while not self.key_queue.empty():
                    self.key_queue.get(block=False)
                message = json.loads(message)
                self.key_queue.put(message)
                self.key_list = message
                print("keys:" + str(self.key_list))
            # if it is a common message from friends, print it out
            elif message:
                sender_name = self.friend_list.get(str(sender_id))
                msg = self.decrypt_message(message)
                print("{} : {}".format(sender_name, msg.decode()))

    def update_friend_list(self):
        # Get the friend list from multiprocessing queue and put it back to use later
        if not self.queue.empty():
            self.friend_list = self.queue.get(block=False)
            self.queue.put(self.friend_list)

    def update_key_list(self):
        # Get the friend list from multiprocessing queue and put it back to use later
        if not self.key_queue.empty():
            self.key_list = self.key_queue.get(block=False)
            self.key_queue.put(self.key_list)

    def send(self, message):
        # Get the current friend list before sending out messages
        self.update_key_list()
        # Get ports out of the hash map / dictionary
        member_list = {}
        for p in self.key_list.keys():
            member_list.update({int(p): self.key_list.get(p)})
        self.beb.broadcast(message, member_list)


def main():
    name = input("Your name: ")
    addr = '127.0.0.1'
    try:
        # Choose a random port for each client
        port = random.randint(1024, 49151)
        chat_box = ChatBox(name, addr, port)
        print("Chat box initiated")
    except OSError:
        if chat_box.beb:
            chat_box.beb.close()

    # Initiate a client socket to send to chat server as the beb is to send messages to friends
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connecting to chat server
        client_socket.connect(("127.0.0.1", 11000))
    except socket.error:
        print("Cannot connect to chat server.")
        return
    mesg = str(port) + "+" + "New client:" + name + ":"
    client_socket.sendall(mesg.encode().__add__(chat_box.public_key.exportKey("PEM")))
    client_socket.close()

    # Sending messages
    print("## Type a message or {quit} to quit ##")
    while True:
        message = input("")
        # If quit, send quit message to chat server
        if message == '{quit}':
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # Connecting to chat server
                client_socket.connect(("", 11000))
            except socket.error:
                print("Cannot connect to chat server.")
                continue
            msg = str(chat_box.port) + "+" + message
            client_socket.send(msg.encode())
            client_socket.close()
            break
        elif not message:
            continue
        # Send to friends if it a common message
        else:
            chat_box.send(message)


if __name__ == "__main__":
    main()
