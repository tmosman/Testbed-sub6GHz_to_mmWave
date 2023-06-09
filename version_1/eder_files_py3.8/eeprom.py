#!/usr/bin/python

from threading import Lock
import evkplatform

try:
    import smbus
except ImportError:
    pass

import time

RFM_DATA_MAGIC_NUM_ADDR = 0x00
RFM_ID_BASE_ADDR        = 0x01
PB_ID_BASE_ADDR         = 0x05

class Eeprom(object):
    __instance = None

    def __new__(cls, board_type='MB1'):
        if cls.__instance is None:
            cls.__instance = super(Eeprom, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, board_type='MB1'):
        if self.__initialized:
            return
        self.__initialized = True
        self.board_type = board_type
        self.lock = Lock()
        if board_type=='MB1':
            self.evkplatform = evkplatform.EvkPlatform()
            self.eeprom_address = 0x53
            self.temp_sens_address = 0x1b
            self.wait_time = 0.01
        else:
            self.i2cbus=smbus.SMBus(1)
            self.eeprom_address = 0x50
            self.temp_sens_address = 0x18


    def read_pcb_temp(self):
        self.lock.acquire()
        if self.board_type == 'MB0':
            temp_reg = self.i2cbus.read_i2c_block_data(0x18, 5, 2)
            temperature = (temp_reg[0]<<8) + temp_reg[1]
            temperature=((1<<13)-1)& temperature
            if temperature & 0x1000:
                temperature = -temperature
            temperature = round(temperature /16.1, 2)
        else:
            try:
                temperature = round(self.evkplatform.get_pcb_temp(), 2)
            except:
                self.lock.release()
                return -300
        self.lock.release()
        return temperature
        
    def write_rfm_data(self, rfm_id, pb_id):
        self.lock.acquire()
        if self.board_type == 'MB1':
            wait_time = 0.01
            if isinstance(rfm_id, int):
                pass
            else:
                if rfm_id[0:2].upper() == 'SN':
                    rfm_id = rfm_id[2:]
                try:
                    rfm_id = int(rfm_id)
                except:
                    rfm_id = -1

            if rfm_id > 0xFFFFFFFF:
                rfm_id = -1
            if rfm_id != -1:
                # Valid RFM ID
                self.evkplatform.drv.writeeprom(RFM_ID_BASE_ADDR, (rfm_id & 0xff))
                time.sleep(wait_time)
                self.evkplatform.drv.writeeprom(RFM_ID_BASE_ADDR + 1, ((rfm_id & 0xff00) >> 8))
                time.sleep(wait_time)
                self.evkplatform.drv.writeeprom(RFM_ID_BASE_ADDR + 2, ((rfm_id & 0xff0000) >> 16))
                time.sleep(wait_time)
                self.evkplatform.drv.writeeprom(RFM_ID_BASE_ADDR + 3, ((rfm_id & 0xff000000) >> 24))
                time.sleep(wait_time)
            else:
                print ('    rfm_id not valid')
                self.lock.release()
                return

            if isinstance(pb_id, int):
                pass
            else:
                if pb_id[0:2].upper() == 'PB':
                    pb_id = pb_id[2:]
                try:
                    pb_id = int(pb_id)
                except:
                    pb_id = -1

            if pb_id > 0xFFFFFFFF:
                pb_id = -1
            if pb_id != -1:
                # Valid RFM ID
                self.evkplatform.drv.writeeprom(PB_ID_BASE_ADDR, (pb_id & 0xff))
                time.sleep(wait_time)
                self.evkplatform.drv.writeeprom(PB_ID_BASE_ADDR + 1, ((pb_id & 0xff00) >> 8))
                time.sleep(wait_time)
                self.evkplatform.drv.writeeprom(PB_ID_BASE_ADDR + 2, ((pb_id & 0xff0000) >> 16))
                time.sleep(wait_time)
                self.evkplatform.drv.writeeprom(PB_ID_BASE_ADDR + 3, ((pb_id & 0xff000000) >> 24))
                time.sleep(wait_time)
            else:
                print ('    pb_id not valid')
                self.lock.release()
                return

            self.evkplatform.drv.writeeprom(RFM_DATA_MAGIC_NUM_ADDR, 0xCD) # Mark section as valid
            time.sleep(wait_time)
            self.lock.release()

    def read_rfm_data(self):
        self.lock.acquire()
        if self.board_type == 'MB1':
            valid_flag = self.evkplatform.drv.readeprom(RFM_DATA_MAGIC_NUM_ADDR)
            if valid_flag == 0xCD: # Magic number for valid data
                rfm_id = self.evkplatform.drv.readeprom(RFM_ID_BASE_ADDR) + (self.evkplatform.drv.readeprom(RFM_ID_BASE_ADDR + 1) << 8) + \
                         (self.evkplatform.drv.readeprom(RFM_ID_BASE_ADDR + 2) << 16) + (self.evkplatform.drv.readeprom(RFM_ID_BASE_ADDR + 3) << 24)
                rfm_id = 'SN' + str(rfm_id).zfill(4)
                pb_id = self.evkplatform.drv.readeprom(PB_ID_BASE_ADDR) + (self.evkplatform.drv.readeprom(PB_ID_BASE_ADDR + 1) << 8) + \
                         (self.evkplatform.drv.readeprom(PB_ID_BASE_ADDR + 2) << 16) + (self.evkplatform.drv.readeprom(PB_ID_BASE_ADDR + 3) << 24)
                pb_id = 'PB' + str(pb_id).zfill(6)
            chip_data = {'rfm_id': rfm_id, 'pb_id': pb_id}
        else:
            chip_data = {'rfm_id': None, 'pb_id': None}
        self.lock.release()
        return chip_data

    def read_data(self, address, size, datatype='ascii'):
        self.lock.acquire()
        if self.board_type == 'MB1':
            if datatype=='ascii':
                data = []
                for i in range(0, size):
                    read_data = None
                    num_of_retries = 0
                    while (read_data == None) and (num_of_retries < 100):
                        time.sleep(0.0005)
                        read_data = self.evkplatform.drv.readeprom(address+i)
                        num_of_retries = num_of_retries + 1
                    data = data + [read_data]
                str_data = ''.join(chr(i) for i in data)
                data = {'raw': data, 'string': str_data}
            else:
                data = bytearray(size)
                for i in range(0, size):
                    read_data = None
                    num_of_retries = 0
                    while (read_data == None) and (num_of_retries < 100):
                        time.sleep(0.0005)
                        read_data = self.evkplatform.drv.readeprom(address+i)
                        num_of_retries = num_of_retries + 1
                    data[i] = read_data
            self.lock.release()
            return data
        self.lock.release()
        return None

    def write_data(self, address, data):
        self.lock.acquire()
        if self.board_type == 'MB1':
            if isinstance(data, str):
                data = [ord(c) for c in data]
            elif isinstance(data, list):
                pass
            elif isinstance(data, int):
                data = [data]

            try:
                size = len(data)
                for i in range(0,size):
                    res = None
                    num_of_retries = 0
                    while res == None and num_of_retries < 100:
                        res = self.evkplatform.drv.writeeprom(address+i, data[i])
                        time.sleep(0.005)
                        num_of_retries = num_of_retries + 1
                    #print ('address {} OK with {} re-tries'.format(address+i, num_of_retries))
            except:
                print ('Error: data must be a list')
        else:
            print ('Function not supported for platform')
        self.lock.release()
