from perfectpointtopointlinks import PerfectPointToPointLinks
import json
import socket
import time
import threading

from Crypto.PublicKey import RSA
from Crypto import Random

# This is the chat server which keeps track of the people in the chat application


class ChatServer:
    def __init__(self):
        self.ADDRESS = "127.0.0.1"
        self.PORT = 11000
        # a dictionary which acts like a hash map
        self.clients = {}
        self.keys = {}
        # self.approvals = {}
        self.just_delivered = False
        # This server link is to deliver
        self.server_link = PerfectPointToPointLinks(port=self.PORT, addr_str=self.ADDRESS, arg_callback=self.delivery)

    # Send message to every one in the client list
    # Create a new client and send without using the p2p send method so that one can fake port
    # to mark if it is a client list update or notification
    def send(self, message):
        for port in self.clients.keys():
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect((self.ADDRESS, int(port)))
            except socket.error:
                print("Cannot connect to {}.".format(self.clients.get(port)))
                continue
            client_socket.send(message.encode())
            client_socket.close()

    # # authentication send/deliver methods go here:
    # def send_to_client(self, port, message):
    #     client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     try:
    #         client_socket.connect((self.ADDRESS, int(port)))
    #     except socket.error:
    #         print("Cannot connect to {}.".format(self.clients.get(port)))
    #     client_socket.send(message.encode())
    #     client_socket.close()
    #
    # def permission_thread(self, s_port, name):
    #     # for each current client
    #     mesg = "-3+is {} allowed to join your chat group? y/n".format(name)
    #     # for port in self.clients.keys():
    #     #     self.send_to_client(port, mesg)
    #     self.send(mesg)
    #     approvals = {}
    #     # get response here!!!
    #     server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     server_socket.bind((self.ADDRESS, 11100))
    #     server_socket.listen(len(self.clients))
    #     i = 0
    #     while True:
    #         connection, address = server_socket.accept()
    #         buf = connection.recv(2048)
    #         message = None
    #         if buf:
    #             message = buf.decode()
    #             sender_port = message.split("+")[0]
    #             message = message.split("+")[1]
    #         connection.close()
    #         if message == "y":
    #             approvals.update({int(sender_port): 1})
    #         elif message == "n":
    #             approvals.update({int(sender_port): 0})
    #         if i >= len(self.clients):
    #             break
    #         i += 1
    #     server_socket.close()
    #     self.clients.update({int(s_port): name})
    #     msg = "-1+" + json.dumps(self.clients)
    #     for port in approvals.keys():
    #         if approvals.get(port):
    #             self.send_to_client(port, msg)

    # Send the current client list to everyone
    def send_address_list(self):
        message = json.dumps(self.clients)
        mesg = "-1" + "+" + message
        self.send(mesg)

    def send_key_list(self):
        message = json.dumps(self.keys)
        msg = "-4+" + message
        self.send(msg)

    def delivery(self, sender_port, message):
        # Update client list when someone joins/quits
        # First send is to update the client list
        # Second send is to notify who just joins/quits
        if message.startswith("New client:"):
            name = message.split(':')[1]
            pk = message.split('PK*')[1]
            self.clients.update({int(sender_port): name})
            self.keys.update({int(sender_port): pk})
            self.send_address_list()
            self.send_key_list()
            message = "-2" + "+" + "{} just joined the network.".format(name)
            self.send(message)
        elif message == "{quit}":
            name = self.clients.get(int(sender_port))
            message = "-2" + "+" + "{} just left the conversation.".format(name)
            self.clients.pop(int(sender_port), None)
            self.send_address_list()
            self.send(message)
        else:
            return
        print(self.clients)
        print(self.keys)


def main():
    chat_server = ChatServer()


if __name__ == "__main__":
    main()
