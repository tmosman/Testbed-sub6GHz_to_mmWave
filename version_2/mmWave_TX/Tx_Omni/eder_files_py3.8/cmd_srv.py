import socket
import threading
import json
import copy
import getip

class CmdSrv(object):

    def __init__(self, device, port, device_name='eder'):
        self.port = port
        print ('Connect to IP address {} port {}'.format(getip.getip(), port))
        self.device = device
        self.device_name = device_name
        self.stop_server = False
        thread = threading.Thread(target=self.events_server)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.stop_server = True

# HANDLE INCOMING MESSAGE
    def events_server(self):
        try:
            from StringIO import StringIO ## for Python 2
        except ImportError:
            from io import StringIO ## for Python 3
        import sys
        import getip

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((getip.getip(), self.port))
            #print (socket.gethostname())
            #sock.bind((socket.gethostname(),12345))
            #sock.bind((getip.getip(),12345))
            sock.listen(1)
            device = self.device

            while True:
                print ('\nWaiting on connection')
                connection, client_address = sock.accept()
                print ('Client ' + str(client_address) + ' connected')

                while True:
                    m = connection.recv(128)
                    m = m.decode("utf-8")
                    if len(m) == 0:
                        break
                    print ('Event: ' + m)
                    
                    mystdout = StringIO()
                    sys.stdout = mystdout
                    command = m.replace(self.device_name, 'device')
                    #exec(command)
                    exec('exec_output =' + command + '; print (exec_output)')
                    #result = copy.copy(mystdout.getvalue())
                    result = str(locals()['exec_output'])
                    print ('result: ', result)
                    mystdout.flush()
                    sys.stdout = sys.__stdout__
                    send_result = bytes(command.replace('device', self.device_name) + ' => ' + result, 'utf-8')
                    connection.sendall(send_result)
                    print ('result: ', result)
                    mystdout.close()

                print ('Connection closed')
                if self.stop_server:
                    self.stop_server = False
                    return
