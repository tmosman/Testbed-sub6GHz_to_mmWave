from threading import Lock

class EvkPlatform(object):

    __instance = None

    import time

    SIG_MB1 = {
        'AGC_GAIN_0' : (1,0),
        'AGC_GAIN_1' : (1,1),
        'AGC_GAIN_2' : (1,2),
        'AGC_GAIN_3' : (1,3),
        'AGC_GAIN_4' : (1,4),
        'AGC_GAIN_5' : (1,5),
        'AGC_GAIN_6' : (1,6),
        'AGC_IRQ'    : (1,7),

        'AGC_CMD_0'  : (2,0),
        'AGC_CMD_1'  : (2,1),
        'AGC_CMD_2'  : (2,2),
        'AGC_CLK'    : (2,3),
        'TX_RX_SW'   : (2,4),
        'BF_RTN'     : (2,5),
        'BF_INC'     : (2,6),
        'BF_RST'     : (2,7),
    }

    def __new__(cls, platform_type='MB1'):
        if cls.__instance is None:
            cls.__instance = super(EvkPlatform, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
    
    def __init__(self, platform_type='MB1'):
        if self.__initialized:
            return
        self.__initialized = True
        if platform_type == 'MB1':
            try:
                import mb1
                self.drv = mb1
                self.gpio_map = self.SIG_MB1
            except ImportError as e:
                print('mb1 module NOT installed.')
        self.lock = Lock()

    def init(self, Id, rfm_type='siv_rfm'):
        return self.drv.init(Id, rfm_type)

    def spi_xfer(self, data):
        self.lock.acquire()
        res = self.drv.xfer(data)
        self.lock.release()
        return res

    def get_pcb_temp(self):
        self.lock.acquire()
        res = self.drv.getpcbtemp()
        self.lock.release()
        return res

    def eeprom_write(self, address, data_byte):
        self.drv.writeeprom(address, data_byte)

    def eeprom_read(self, address):
        return self.drv.readeprom(address)

    def reset(self, rst_time_in_ms=1):
        self.drv.setrstn(0)
        self.time.sleep(0.001*rst_time_in_ms)
        self.drv.setrstn(1)

    def setvcm(self, vcm_mV):
        self.drv.setvcm(vcm_mV)

    def gpio_o(self, gpio_name, out_value):
        gpio_num = self.gpio_map[gpio_name]
        if gpio_num[0] == 1:
            gpio_value = self.drv.getgpio1()
            if out_value == 1:
                mask = (1 << gpio_num[1])
                gpio_value = gpio_value | mask
            elif oval == 0:
                mask = ~(1 << gpio_num[1])
                gpio_value = gpio_value & mask
            self.drv.setgpio1(gpio_value)
        elif gpio_num[0] == 2:
            gpio_value = self.drv.getgpio2()
            if out_value == 1:
                mask = (1 << gpio_num[1])
                gpio_value = gpio_value | mask
            elif oval == 0:
                mask = ~(1 << gpio_num[1])
                gpio_value = gpio_value & mask
            self.drv.setgpio2(gpio_value)

    def settxrxsw(self, value):
        self.drv.settxrxsw(value)

    def txrxsw_disable(self):
        self.drv.settxrxsw_input()