from besteffortbroadcast import BestEffortBroadcast
import multiprocessing
from multiprocessing import Process
import random
import socket
import json
import sys
import time

from Crypto.PublicKey import RSA
from Crypto import Random

import threading

class ChatBox:
    def __init__(self, name, address, port):
        self.private_key = RSA.generate(1024, Random.new().read)
        self.public_key = self.private_key.publickey()
        self.name = name
        self.addr = address
        self.port = port
        self.friend_list = {}
        self.key_list = {}
        self.approved = {}  # for authentication
        self.queue = multiprocessing.Queue()
        self.beb = BestEffortBroadcast(process_id=int(self.port), addr_str=self.addr,
                                       callback=self.chat_deliver, arg_callback=self.queue)

    # # authentication send/deliver methods go here:
    # def send_to_client(self, port, msg):
    #     client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     try:
    #         # Connecting to chat server
    #         client_socket.connect(("127.0.0.1", int(port)))
    #     except socket.error:
    #         print("Cannot connect to {}".format(self.friend_list.get(port)))
    #         return
    #     client_socket.send(msg.encode())
    #     client_socket.close()
    #
    # def permission_thread_response(self, message):
    #     print("Server : {}".format(message))
    #     response = input("")
    #     self.send_to_client(11100, str(self.port) + response)

    def chat_deliver(self, mesg, queue):
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
                message = json.loads(message)
                self.key_list = message
                print("keys: {}".format(self.key_list))
                return
            # if it is a common message from friends, print it out
            elif message:
                sender_name = self.friend_list.get(str(sender_id))
                print("{} : {}".format(sender_name, message))

    def update_friend_list(self):
        # Get the friend list from multiprocessing queue and put it back to use later
        if not self.queue.empty():
            self.friend_list = self.queue.get(block=False)
            self.queue.put(self.friend_list)

    def send(self, message):
        # Get the current friend list before sending out messages
        self.update_friend_list()
        # Get ports out of the hash map / dictionary
        process_id_list = list(self.friend_list.keys())
        process_id_list = list(map(int, process_id_list))
        self.beb.broadcast(message, process_id_list)


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
    mesg = str(port) + "+" + "New client:" + name + ":PK*" + str(chat_box.public_key)
    client_socket.send(mesg.encode())
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
