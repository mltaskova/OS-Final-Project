import socket
from multiprocessing import Process
import time
import ssl


class PerfectPointToPointLinks:
    def __init__(self, port, addr_str, arg_callback, context):
        self.port = port
        self.address = addr_str
        ssocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.context = context
        self.context.set_ciphers("ADH-AES256-SHA")
        self.context.load_dh_params("dhparam.pem")
        ssocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ssocket.bind((self.address, int(self.port)))
        ssocket.listen(4)
        self.server_socket = self.context.wrap_socket(ssocket, server_side=True)
        self.deliver_list = []
        self.p = Process(target=self.deliver, args=(arg_callback,))
        self.p.start()

    def send(self, recipient_process_port, addr_str, message):
        ssocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket = self.context.wrap_socket(ssocket, server_hostname='localhost')
        try:
            client_socket.connect((addr_str, int(recipient_process_port)))
        except socket.error:
            print("Friend {} has not joined.".format(recipient_process_port))
        mesg = str(self.port) + "+" + str(message)
        client_socket.sendall(mesg.encode())
        client_socket.close()

    def deliver(self, arg_callback):
        while True:
            (connection, address) = self.server_socket.accept()
            message = ""
            data = ''
            buf = connection.recv(2048)
            while buf:
                message = buf.decode()
                buf = connection.recv(2048)
                data += message
            if data:
                sender_port = data.split("+")[0]
                msg = data.split("+", 1)[1:]
                message = message.join(msg)
            connection.close()
            arg_callback(int(sender_port), message)

    def close(self):
        self.server_socket.close()
        self.p.terminate()