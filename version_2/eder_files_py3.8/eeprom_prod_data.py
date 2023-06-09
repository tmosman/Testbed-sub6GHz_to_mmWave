import sys
import time
import struct
import crcmod
import fileHandler

class EepromProdData(object):

    __instance = None

    __eeprom_data = {'00_manufacturer': {'type':'ascii',  'value': 'SIVERS',            'addr':0,   'size':16 },
                     '01_product_id'  : {'type':'ascii',  'value': '',                  'addr':16,  'size':16 },
                     '02_orig_rev_id' : {'type':'ascii',  'value': '',                  'addr':32,  'size':16 },
                     '03_serial_no'   : {'type':'ascii',  'value': ''  ,                'addr':48,  'size':32 },
                     '04_temp_tlv'    : {'type':'binary', 'value': 0  ,                 'addr':80,  'size':1  },
                     '05_temp_data'   : {'type':'binary', 'value': 0  ,                 'addr':81,  'size':1  },
                     '06_temp_crc'    : {'type':'binary', 'value': 0  ,                 'addr':82,  'size':1  },
                     '07_alc_tlv'     : {'type':'binary', 'value': 0  ,                 'addr':83,  'size':1  },
                     '08_alc_ver'     : {'type':'binary', 'value': 0  ,                 'addr':84,  'size':1  },
                     '09_alc_data'    : {'type':'binary', 'value': bytearray(18) ,      'addr':85,  'size':18 },
                     '10_alc_crc'     : {'type':'binary', 'value': 0  ,                 'addr':103, 'size':2  },
                     '11_reserved_1'  : {'type':'binary', 'value': bytearray(23) ,      'addr':105, 'size':23 },
                     '12_cur_rev_id'  : {'type':'ascii',  'value': '' ,                 'addr':128, 'size':16 },
                     '13_reserved_2'  : {'type':'binary', 'value': bytearray(28) ,     'addr':144, 'size':28  },
                     '14_reserved_3'  : {'type':'binary', 'value': bytearray(28) ,     'addr':172, 'size':28  },
                     '15_reserved_4'  : {'type':'binary', 'value': bytearray(28) ,     'addr':200, 'size':28  },
                     '16_reserved_5'  : {'type':'binary', 'value': bytearray(28) ,     'addr':228, 'size':28  },
                    }

    __chunk_size = 8

    def __new__(cls, evkplatform_type='MB1'):
        if cls.__instance is None:
            cls.__instance = super(EepromProdData, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, evkplatform_type='MB1'):
        if self.__initialized:
            return
        self.__initialized = True
        self.evkplatform_type = evkplatform_type
        if evkplatform_type != 'MB1':
            try:
                import smbus
            except:
                smbus = None
                print('smbus not installed!')
            if smbus != None:
                try:
                    self.bus=smbus.SMBus(1)
                except:
                    pass
            else:
                self.bus = None
        else:
            import eeprom
            self.eeprom = eeprom.Eeprom(self.evkplatform_type)
        import evk_configuration
        self.evk_config = evk_configuration.EvkConfiguration()
        self.fileHandler = fileHandler
        self.write_data=[0]*256

    def load_eeprom_data(self, generate_hex_file=False):
        self.write_data = self.read()
        num_of_retries = 4
        while (self.write_data == []) and (num_of_retries > 0):
            print (num_of_retries)
            num_of_retries = num_of_retries - 1
            self.write_data = self.read()
        self._convert_to_eeprom_data()
        if generate_hex_file:
            with open('config/eeprom.hex', "w") as hex_file:
                for l in range(0,256,16):
                    line = '{:04x}   '.format(l)
                    for i in range(0,16):
                        line = line + '{:02x} '.format(self.write_data[l+i])
                    hex_file.writelines(line+'\n')

    def print_eeprom_data(self):
        print (self.__eeprom_data)

    def _convert_to_eeprom_data(self):
        for section in sorted(self.__eeprom_data):
            if self.__eeprom_data[section]['type'] == 'ascii':
                value = ''
                for n in range(self.__eeprom_data[section]['addr'], self.__eeprom_data[section]['addr'] + self.__eeprom_data[section]['size']):
                    value = value + chr(self.write_data[n])
                self.__eeprom_data[section]['value'] = value
            else:
                value = bytearray(self.__eeprom_data[section]['size'])
                for n in range(self.__eeprom_data[section]['addr'], self.__eeprom_data[section]['addr'] + self.__eeprom_data[section]['size']):
                    value[n-self.__eeprom_data[section]['addr']] = self.write_data[n]
                self.__eeprom_data[section]['value'] = value

    def _convert_to_write_data(self):
        for section in sorted(self.__eeprom_data):
            if self.__eeprom_data[section]['type'] == 'ascii':
                z = [ord(c) for c in self.__eeprom_data[section]['value']]
                if len(z) < self.__eeprom_data[section]['size']:
                    z = z + [0]*(self.__eeprom_data[section]['size'] - len(z))
                for n in range(self.__eeprom_data[section]['addr'], self.__eeprom_data[section]['addr'] + self.__eeprom_data[section]['size']):
                    self.write_data[n] = z[n - self.__eeprom_data[section]['addr']]
            else: # Binary
                if isinstance(self.__eeprom_data[section]['value'], int):
                    if self.__eeprom_data[section]['size'] < 5:
                        value = struct.unpack('4B', struct.pack('<I', self.__eeprom_data[section]['value']))
                        value_list = []
                        for i in range(self.__eeprom_data[section]['size'], 0, -1):
                            value_list = value_list + [value[i-1]]
                        value = value_list
                    else:
                        value = [self.__eeprom_data[section]['value']]
                        if len(value) < self.__eeprom_data[section]['size']:
                            value = value + [0]*(self.__eeprom_data[section]['size']-len(value))
                else:
                    value = self.__eeprom_data[section]['value']
                for n in range(self.__eeprom_data[section]['addr'], self.__eeprom_data[section]['addr'] + self.__eeprom_data[section]['size']):
                    self.write_data[n] = value[n - self.__eeprom_data[section]['addr']]


    def write_complete(self):
        if self.evkplatform_type == 'MB1':
            self.eeprom.write_data(0, self.write_data)
        else:
            if self.bus != None:
                block_32 = len(self.write_data) // self.__chunk_size
                remain = len(self.write_data) % self.__chunk_size
                for i in range(0, block_32):
                    self.bus.write_i2c_block_data(0x50, self.__chunk_size*i, self.write_data[self.__chunk_size*i:(self.__chunk_size*i)+self.__chunk_size])
                    time.sleep(0.1)
                if remain > 0:
                    self.bus.write_i2c_block_data(0x50, self.__chunk_size*block_32, self.write_data[self.__chunk_size*block_32:(self.__chunk_size*block_32)+remain])
                    time.sleep(0.1)
            else:
                print(self.write_data)

    def read(self):
        if self.evkplatform_type == 'MB1':
            data = self.eeprom.read_data(0, len(self.write_data))
            try:
                return data['raw']
            except:
                return []
        else:
            if self.bus != None:
                data = []
                block_32 = len(self.write_data) // self.__chunk_size
                remain = len(self.write_data) % self.__chunk_size
                for i in range(0, block_32):
                    data = data + self.bus.read_i2c_block_data(0x50, self.__chunk_size*i, self.__chunk_size)
                if remain > 0:
                    data = data + self.bus.read_i2c_block_data(0x50, self.__chunk_size*block_32, remain)
                return data
        return self.write_data

    def verify_ok(self):
        try:
            if self.write_data == self.read():
                return True
            else:
                return False
        except:
            print ('Error while verifying EEPROM data')
            return False

    def set_attrib(self, attrib, value):
        if isinstance(attrib, str):
            if isinstance(value, int):
                value = [value]
            if isinstance(value, str):
                if self.__eeprom_data[attrib]['type'] == 'ascii':
                    if len(value) <= self.__eeprom_data[attrib]['size']:
                        self.__eeprom_data[attrib]['value'] = value
                        self._convert_to_write_data()
                else:
                    print ("Error: value must be a list")
            elif isinstance(value, list):
                if self.__eeprom_data[attrib]['type'] == 'binary':
                    if len(value) < self.__eeprom_data[attrib]['size']:
                        value = value + [0]*(self.__eeprom_data[attrib]['size']-len(value))
                    value = bytearray(value)
                    self.__eeprom_data[attrib]['value'] = value
                    self._convert_to_write_data()
                else:
                    print ("Error: value must be a string")
        else:
            print ("Error: Check attribute and value")

    def write_attrib(self, attrib, value):
        if isinstance(attrib, str):
            if isinstance(value, int):
                value = [value]
            if isinstance(value, str):
                if self.__eeprom_data[attrib]['type'] == 'ascii':
                    if len(value) <= self.__eeprom_data[attrib]['size']:
                        if len(value) < self.__eeprom_data[attrib]['size']:
                            value = value + '\x00'*(self.__eeprom_data[attrib]['size'] - len(value))
                        data = value
                        self.__eeprom_data[attrib]['value'] = value
                        self._convert_to_write_data()
                else:
                    print ("Error: value must be a list")
            elif isinstance(value, list):
                if self.__eeprom_data[attrib]['type'] == 'binary':
                    if len(value) > self.__eeprom_data[attrib]['size']:
                        print ('Error: value size exceeds allocated EEPROM size')
                    if len(value) < self.__eeprom_data[attrib]['size']:
                        value = value + [0]*(self.__eeprom_data[attrib]['size']-len(value))
                    data = value
                    value = bytearray(value)
                    self.__eeprom_data[attrib]['value'] = value
                    self._convert_to_write_data()
                else:
                    print ("Error: value must be a string")

            ## Write to EEPROM
            if self.evkplatform_type == 'MB1':
                self.eeprom.write_data(self.__eeprom_data[attrib]['addr'], data)
            else:
                blocks = len(data) // self.__chunk_size
                remain = len(data) % self.__chunk_size
                for i in range(0, blocks):
                    self.bus.write_i2c_block_data(0x50, self.__eeprom_data[attrib]['addr']+(self.__chunk_size*i), data[self.__chunk_size*i:(self.__chunk_size*i)+self.__chunk_size])
                    time.sleep(0.1)
                if remain > 0:
                    self.bus.write_i2c_block_data(0x50, self.__eeprom_data[attrib]['addr']+(self.__chunk_size*blocks), data[self.__chunk_size*blocks:(self.__chunk_size*blocks)+remain+1])
                    time.sleep(0.1)
        else:
            print ('Error: Check attribute and value')

    def read_attrib(self, attrib):
        data = {}
        matched_attribs = [[key, value] for key, value in self.__eeprom_data.items() if attrib in key.lower()]
        for i in range(len(matched_attribs)):
            if self.evkplatform_type == 'MB1':
                datatype = self.__eeprom_data[matched_attribs[i][0]]['type']
                datasize = self.__eeprom_data[matched_attribs[i][0]]['size']
                address  = self.__eeprom_data[matched_attribs[i][0]]['addr']
                #data[matched_attribs[i][0]] = self.eeprom.read_data(address, datasize, datatype)['string'].strip('\x00')
                data[matched_attribs[i][0]] = self.eeprom.read_data(address, datasize, datatype)
                #print(data)
        return data

    def get_attrib(self, attrib):
        try:
            value = self.__eeprom_data[attrib]['value']
            if self.__eeprom_data[attrib]['type'] == 'ascii':
                value = value.strip('\x00')
            else:
                value = list(value)
        except:
            value = None
        return value

    def get_temp_data(self):
        if self.get_attrib('04_temp_tlv')[0] == 0x02:
            temp_data = self.get_attrib('05_temp_data')[0]
            crc16 = crcmod.predefined.Crc('crc-ccitt-false')
            if sys.version_info.major > 2: # Python 3.8
                crc16.update(bytearray(b'\x02'))
                crc16.update(bytearray(temp_data.to_bytes(1, byteorder='big')))
            else: # Python 2.7
                crc16.update(chr(0x02))
                crc16.update(chr(temp_data))
            calculated_crc = ((crc16.crcValue&0xff00)>>8) ^ (crc16.crcValue&0x00ff)
            eeprom_temp_crc = self.get_attrib('06_temp_crc')[0]
            if calculated_crc == eeprom_temp_crc:
                return temp_data
            else:
                print ('Error: temp_crc not correct.')
        return None

    def get_alc_data(self):
        if self.get_attrib('07_alc_tlv')[0] == 0x35:
            alc_data = self.get_attrib('09_alc_data')
            alc_ver = self.get_attrib('08_alc_ver')[0]
            alc_crc = self.get_attrib('10_alc_crc')
            alc_crc = (alc_crc[1]<<8) + alc_crc[0]
            crc16 = crcmod.predefined.Crc('crc-ccitt-false')
            if sys.version_info.major > 2: # Python 3.8
                crc16.update(bytearray(b'\x35'))
                crc16.update(bytearray(bytes(chr(alc_ver), encoding='utf8')))
                crc16.update(bytearray(alc_data))
            else:
                crc16.update(chr(0x35))
                crc16.update(chr(alc_ver))
                crc16.update(str(bytearray(alc_data)))
            if crc16.crcValue == alc_crc:
                return alc_data
            else:
                print ('Error: alc_crc not correct.')
        return None

    def dump(self,indent=10, return_list=False):
        content = []
        try:
            print('')
            content.append('')
            title = ' '*indent + 'Unit EEPROM content'
            content.append(title)
            separator = ' '*indent + '='*40
            print(title)
            print(separator)
            content.append(separator)
            print('')
            content.append('')
            eeprom_raw_data = self.write_data
            index_in_raw_data = 0
            for section in sorted(self.__eeprom_data):
                text = ''
                if self.__eeprom_data[section]['type'] == 'ascii':
                    for i in range(0,self.__eeprom_data[section]['size']):
                        text = text + chr(eeprom_raw_data[index_in_raw_data])
                        index_in_raw_data = index_in_raw_data + 1
                else:
                    for i in range(0,self.__eeprom_data[section]['size']):
                        #text = text + format(eeprom_raw_data[index_in_raw_data], 'x')+ ' '
                        text = text + hex(eeprom_raw_data[index_in_raw_data]) + ' '
                        index_in_raw_data = index_in_raw_data + 1
                print(' '*indent + section + ' '*(22-len(section)) + text)
                content.append(' '*indent + section + ' '*(22-len(section)) + text)
        except:
            print('Failed EEPROM read!')
            content.append('Failed EEPROM read!')
        if return_list:
            return content

    def write_temp_crc(self):
        crc16 = crcmod.predefined.Crc('crc-ccitt-false')

        if sys.version_info.major > 2: # Python 3.8
            crc16.update(bytes(chr(self.read_attrib('04_temp_tlv')['04_temp_tlv'][0]), encoding='utf8'))
            temp_data = self.read_attrib('05_temp_data')['05_temp_data'][0]
            crc16.update(bytearray(temp_data.to_bytes(1, byteorder='big')))
        else: # Python 2.7
            crc16.update(chr(self.read_attrib('04_temp_tlv')['04_temp_tlv'][0]))
            crc16.update(chr(self.read_attrib('05_temp_data')['05_temp_data'][0]))

        crcValue = ((crc16.crcValue&0xff00)>>8) ^ (crc16.crcValue&0x00ff)
        self.write_attrib('06_temp_crc', crcValue)
        self._convert_to_write_data()

    def set_temp_crc(self):
        crc16 = crcmod.predefined.Crc('crc-ccitt-false')

        if sys.version_info.major > 2: # Python 3.8
            crc16.update(bytes(chr(self.__eeprom_data['04_temp_tlv']['value'][0]), encoding='utf8'))
            temp_data = self.__eeprom_data['05_temp_data']['value'][0]
            crc16.update(bytearray(temp_data.to_bytes(1, byteorder='big')))
        else: # Python 2.7
            crc16.update(chr(self.__eeprom_data['04_temp_tlv']['value'][0]))
            crc16.update(chr(self.__eeprom_data['05_temp_data']['value'][0]))

        crcValue = ((crc16.crcValue&0xff00)>>8) ^ (crc16.crcValue&0x00ff)
        self.set_attrib('06_temp_crc', crcValue)
        self._convert_to_write_data()

    def write_alc_crc(self):
        crc16 = crcmod.predefined.Crc('crc-ccitt-false')

        if sys.version_info.major > 2: # Python 3.8
            crc16.update(bytes(chr(self.read_attrib('07_alc_tlv')['07_alc_tlv'][0]), encoding='utf8'))
            crc16.update(bytearray(bytes(chr(self.read_attrib('08_alc_ver')['08_alc_ver'][0]), encoding='utf8')))
            crc16.update(bytearray(self.read_attrib('09_alc_data')['09_alc_data']))
        else:
            crc16.update(chr(self.read_attrib('07_alc_tlv')['07_alc_tlv'][0]))
            crc16.update(chr(self.read_attrib('08_alc_ver')['08_alc_ver'][0]))
            crc16.update(str(self.read_attrib('09_alc_data')['09_alc_data']))
        self.write_attrib('10_alc_crc', [crc16.crcValue&0x00ff, (crc16.crcValue&0xff00)>>8])
        self._convert_to_write_data()

    def set_alc_crc(self):
        crc16 = crcmod.predefined.Crc('crc-ccitt-false')

        if sys.version_info.major > 2: # Python 3.8
            crc16.update(bytes(chr(self.__eeprom_data['07_alc_tlv']['value'][0]), encoding='utf8'))
            crc16.update(bytearray(bytes(chr(self.__eeprom_data['08_alc_ver']['value'][0]), encoding='utf8')))
            crc16.update(bytearray(self.__eeprom_data['09_alc_data']['value']))
        else:
            crc16.update(chr(self.__eeprom_data['07_alc_tlv']['value'][0]))
            crc16.update(chr(self.__eeprom_data['08_alc_ver']['value'][0]))
            crc16.update(str(self.__eeprom_data['09_alc_data']['value']))
        #print(hex(crc16.crcValue))
        self.set_attrib('10_alc_crc', [crc16.crcValue&0x00ff, (crc16.crcValue&0xff00)>>8])
        self._convert_to_write_data()

    def write_from_file(self, file_name=None):
        import json
        if file_name == None:
            file_name = self.evk_config.get_config_path() + '/eeprom_data.json'
        else:
            file_name = self.evk_config.get_config_path() + '/' + file_name
        print ('Writing EEPROM data from {} ...'.format(file_name))
        try:
            with open(file_name) as f:
                data = json.load(f)
            for attrib in data:
                #self.set_attrib(str(attrib), str(data[attrib]))
                try:
                    if isinstance(data[attrib], unicode):
                        data[attrib] = str(data[attrib])
                except:
                    if isinstance(data[attrib], str):
                        data[attrib] = str(data[attrib])
                self.set_attrib(str(attrib), data[attrib])
            self.set_temp_crc()
            self.set_alc_crc()
            self.write_complete()
        except:
            print ('Error reading EEPROM config file')
        self.load_eeprom_data()
        self.dump()

    def init_eeprom(self, product_id, serial_number=None):
        """Initializes the BFM EEPROM by writing the content from a template file for the product ID.

        Args:
            product_id (string): Specify the BFM product ID
            serial_number (string_, optional): If specified writes the serial number to EEPROM. Defaults to None.
        """
        file_name = product_id.lower() + '_eeprom_data.json'
        self.write_from_file(file_name)
        if serial_number != None:
            self.write_attrib('03_serial_no', serial_number)
        print ('EEPROM initialization complete.')

