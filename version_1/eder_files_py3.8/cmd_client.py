import socket
import getip

class CmdClient(object):

    def __init__(self, ipaddress, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.s.connect((ipaddress, port))
        except ConnectionRefusedError:
            print ('Connection Refused: Make sure command server is running.')
        self.s.settimeout(60.0)

    def send(self, message):
        self.s.settimeout(0.3)
        self.receive()
        self.s.settimeout(60.0)
        self.s.sendall(message.encode())
        return self.receive()

    def receive(self):
        try:
            return self.s.recv(10240).decode().split(' => ')
        except socket.timeout:
            return ''
