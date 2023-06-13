class Temp(object):

    __instance = None

    adc_max      = 4095
    adc_scale    = 3
    unit_offs    = {'K':0, 'C':-273}

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Temp, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import adc
        import eder_status
        import evk_logger
        import register
        self.regs   = register.Register()
        self.adc = adc.Adc()
        self.status = eder_status.EderStatus()
        self.logger = evk_logger.EvkLogger()

        if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            #ADC reference measured for 12 units at T = 0 degrees,
            #Use 1.217 for other voltage measurements (found at T = 25 degrees)
            self.adc_ref_volt = 1.213                                    # [V]
            self.temp_k       = 3.6805e-3                                # [V/K]
            self.temp_offs    = 0.2052                                   # [1/V]
        else: # Eder B
            self.adc_ref_volt = 1.228                                    # [V]
            self.temp_k       = 4e-3                                     # [V/K]
            self.temp_offs    = 41e-3                                    # [K/V]

        self.temp_scale   = self.adc_scale*self.adc_ref_volt/self.adc_max/self.temp_k    # [K]
        self.temp_comp    = self.temp_offs/self.temp_k                         # [K]
        self.temp_calib_offset = 0

    def reset(self):
        self.status.clr_init_bit(self.status.TEMP_INIT)

    def init(self):
        self.adc.init()
        if self.status.init_bit_is_set(self.status.TEMP_INIT) == False:
            self.status.set_init_bit(self.status.TEMP_INIT)
            self.logger.log_info('Chip TEMP init.',2)
        else:
            self.logger.log_info('Chip TEMP already initialized.',2)

    def set_calib_offset(self, temp_calib_offset):
        self.temp_calib_offset = temp_calib_offset
        self.logger.log_info('temp_calib_offset: ' + str(self.temp_calib_offset), 2)

    def run_raw(self):
        if self.status.init_bit_is_set(self.status.TEMP_INIT) == False:
            self.init()
        self.adc.start(0x83,None,4)
        temp = self.adc.mean()
        self.adc.stop()
        return temp

    def run(self,unit='K'):
        return self.run_raw()*self.temp_scale - self.temp_comp + self.unit_offs[unit] + self.temp_calib_offset

