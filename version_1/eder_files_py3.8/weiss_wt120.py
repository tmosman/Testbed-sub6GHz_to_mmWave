import getpass
import sys
import telnetlib

class WeissWt120(object):

    def __init__(self, ip_address):
        self.tc = telnetlib.Telnet(ip_address, 2049)

    def get_capability(self):
        self.tc.write('$01?\r')
        print self.tc.read_until('THIS_IS_IT', 2)

    def read_status(self):
        self.tc.write('$01I\r')
        return self.tc.read_until('\r', 2)

    def read_current_temp(self):
        status = self.read_status()
        #print status
        target_temp, current_temp, rest = status.split()
        current_temp = float(current_temp)
        return current_temp

    def read_target_temp(self):
        status = self.read_status()
        print status
        target_temp, current_temp, rest = status.split()
        target_temp = float(target_temp)
        return target_temp

    def start(self, temperature):
        self.tc.write('$01E {:f} 010000 \r'.format(round(temperature,1)))
        print self.tc.read_until('\r', 2)

    def set_temp(self, temperature):
        self.start(temperature)

    def stop(self):
        self.tc.write('$01E 0020.0 000000 \r')
        print self.tc.read_until('\r', 2)

    def start_temp(self, temp=20):
        #buf = '\x021T{:4.1f}R0100000000000000000000000000000'.format(temp)
        buf = '\x021T{:4.1f}F000.0R010000'.format(temp)
        buf = buf + self._checksum(buf) + '\x03'
        self.tc.write(buf)
        res = self.tc.read_until('\x03', 2)
        try:
            print (res[0:len(res)-3])
        except:
            print ('No response!')

    def read_status_2(self):
        buf = '\x021?'
        buf = buf + self._checksum(buf) + '\x03'
        self.tc.write(buf)
        res = self.tc.read_until('\x03', 2)
        try:
            print (res[0:len(res)-3])
        except:
            print ('No response!')

    def start_prog(self, prog):
        self.tc.write('$01P{:4d}\r'.format(prog))
        print self.tc.read_until('\r', 2)

    def stop_prog(self):
        self.tc.write('$01P0000\r')
        print self.tc.read_until('\r', 2)

    def _checksum(self, buf):
        ascii = '0123456789ABCDEF'
        res = [0,0,0]
        sum = 256
        for c in buf:
            sum = sum - ord(c)
            if sum < 0: sum = sum + 256

        a1 = (sum & 0xf0) >> 4
        a2 = sum & 0x0f
        res[0] = ascii[a1]
        res[1] = ascii[a2]

        return res[0]+res[1]

