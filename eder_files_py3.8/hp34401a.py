import visa

class Hp34401A(object):
    def __init__(self, address):
        self.rm = visa.ResourceManager()
        self.mm = self.rm.open_resource(address)
        self.mm.write('*IDN?')
        print ('Connected to ' + self.mm.read())

    def voltage(self):
        self.mm.write('MEAS:VOLT:DC?')
        return self.mm.read()
