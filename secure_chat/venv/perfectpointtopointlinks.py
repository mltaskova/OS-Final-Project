import socket
from multiprocessing import Process


class PerfectPointToPointLinks:
    def __init__(self, port, addr_str, arg_callback):
        self.port = port
        self.address = addr_str
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.address, int(self.port)))
        self.server_socket.listen(4)
        self.deliver_list = []
        self.p = Process(target=self.deliver, args=(arg_callback,))
        self.p.start()

    def send(self, recipient_process_port, addr_str, message):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((addr_str, int(recipient_process_port)))
        except socket.error:
            print("Friend {} has not joined.".format(recipient_process_port))
        mesg = str(self.port) + "+" + message
        client_socket.send(mesg.encode())
        client_socket.close()

    def deliver(self, arg_callback):
        while True:
            (connection, address) = self.server_socket.accept()
            buf = connection.recv(2048)
            message = None
            if buf:
                message = buf.decode()
                sender_port = message.split("+")[0]
                message = message.split("+")[1]
            connection.close()
            arg_callback(int(sender_port), message)

    def close(self):
        self.server_socket.close()
        self.p.terminate()