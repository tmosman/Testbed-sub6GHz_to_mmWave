class Tx(object):

    __instance = None
    trx_tx_on_default = 0x1FFFFF
    trx_ctrl = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Tx, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance


    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import evk_configuration
        import alc
        import bf
        import register
        import memory
        import gpio
        import tx_dco
        import evk_logger
        import eder_status
        import fileHandler as json
        self.json = json
        try:
            import config
            self.config = config
        except:
            pass
        self.evk_config = evk_configuration.EvkConfiguration()
        self.beambook_path = self.evk_config.get_beambook_path()
        self.regs   = register.Register()
        self.mems   = memory.Memory()
        self.gpio   = gpio.EderGpio(self.regs.evkplatform_type)
        self.alc    = alc.Alc(self)
        self.bf     = bf.Bf(bf.Bf.TX)
        self.dco    = tx_dco.TxDco()
        self.logger = evk_logger.EvkLogger()
        self.status = eder_status.EderStatus()
        self.freq = 0

    def __default(self):
        self.regs.wr('trx_tx_on',self.regs.value('trx_tx_on'))
        self.regs.wr('trx_tx_off',self.regs.value('trx_tx_off'))
        self.regs.wr('bias_ctrl',self.regs.value('bias_ctrl'))
        self.regs.wr('bias_tx',self.regs.value('bias_tx'))
        self.regs.clr('bias_lo',0x08)
        self.regs.wr('tx_ctrl',self.regs.value('tx_ctrl'))
        self.regs.wr('tx_bb_gain',self.regs.value('tx_bb_gain'))
        self.regs.wr('tx_bb_phase',self.regs.value('tx_bb_phase'))
        self.regs.wr('tx_bb_iq_gain',self.regs.value('tx_bb_iq_gain'))
        self.regs.wr('tx_bfrf_gain',self.regs.value('tx_bfrf_gain'))


    def set_beam(self, beam=None):
        restore_trx_ctrl = self.regs.rd('trx_ctrl')
        self.regs.wr('trx_ctrl', 0x02)
        if beam != None:
            self.bf.awv.set(beam)
        else:
            self.bf.awv.set(self.bf.awv.get()&0x3f)
        self.regs.wr('trx_ctrl',restore_trx_ctrl)


    def reset(self):
        self.__default()
        self.status.clr_init_bit(self.status.TX_INIT)
        self.trx_tx_on_default = 0x1FFFFF
        self.trx_ctrl = None
        self.freq = 0
        self.logger.log_info('TX Reset',2)


    def init(self, trx_tx_on=trx_tx_on_default):
        if self.status.init_bit_is_set(self.status.TX_INIT) == False:
            self.regs.wr('trx_tx_on',trx_tx_on)
            if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
                self.regs.wr('bias_tx', 0x96AA)
            else:
                self.regs.wr('bias_tx', 0xAEAA)
            self.regs.wr('bias_ctrl', 0x7F)
            self.regs.set('bias_lo', 0x0A)
            self.regs.wr('tx_ctrl', 0x18)
            self.regs.wr('tx_bb_gain', 0x00)
            self.regs.wr('tx_bb_phase', 0x00)
            self.regs.wr('tx_bb_iq_gain', 0xFF)
            self.regs.wr('tx_bfrf_gain', 0x77)
            # Check if a setting file exists
            try:
                filename = self.config.__path__[0] + '\\tx_default.json'
                self.loadGainSettings(filename)
            except:
                pass
            self.set_beam(32)
            self.status.set_init_bit(self.status.TX_INIT)
            self.logger.log_info('TX Initialised',2)

    def loadGainSettings(self, file_name):
        settings_loaded = False
        try:
            config = self.json.read(file_name)
            reduced_config = {}

            # Currently only selected registers will be restored
            restored_registers = ['tx_bb_phase','tx_bb_gain','tx_bb_iq_gain','tx_bfrf_gain','rx_gain_ctrl_bfrf','rx_gain_ctrl_bb1',
                                  'rx_gain_ctrl_bb2','rx_gain_ctrl_bb3','trx_tx_on','trx_rx_on']
            for register_name in restored_registers:
                try:
                    reduced_config[register_name] = config[register_name]
                except:
                    pass
            self.regs.dump_wr(reduced_config)
            settings_loaded = True
        except IOError:
            pass
        return settings_loaded


    def setup(self, freq, beam=None, trx_tx_on=trx_tx_on_default):
        self.freq = freq
        # Import beamforming table and write to memory
        # TODO: Here we should prepare for writing the beambook
        # freq 0.0 and temp 0.0 resets bf_tx_awv
        self.freq = freq
        self.logger.log_info('Loading beambook',2)
        self.bf.awv.setup(freq)
        self.bf.idx.setup(self.beambook_path + '/bf_tx_awv_idx')
        self.init(trx_tx_on)
        self.set_beam(beam)
        self.logger.log_info('TX Setup completed (without DCO calibration)',2)


    def enable(self, beam=None,debug=1):
        if self.trx_ctrl == None:
            if (self.regs.rd('trx_ctrl') & 0x08):
                self.trx_ctrl = 'HW'
            else:
                self.trx_ctrl = 'SW'

        if self.trx_ctrl == 'HW':
            self.gpio.set_tx_mode()
        else:
            self.regs.set('trx_ctrl', 0x02)

        self.set_beam(beam)
        if debug > 0:
            self.logger.log_info('TX enabled',2)
        
    def is_enabled(self):
        return self.is_enable()
    
    def is_enable(self):
        if (self.regs.rd('trx_ctrl') & 0x08):
            self.trx_ctrl = 'HW'
        else:
            self.trx_ctrl = 'SW'

        if self.trx_ctrl == 'HW':
            tx_mode = self.regs.rd('gpio_tx_rx_sw_ctrl') & 0x10
        else:
            tx_mode = self.regs.rd('trx_ctrl') & 0x02

        if tx_mode:
            return True
        else:
            return False


    def disable(self,debug=1):
        if self.trx_ctrl == None:
            if (self.regs.rd('trx_ctrl') & 0x08):
                self.trx_ctrl = 'HW'
            else:
                self.trx_ctrl = 'SW'

        self.regs.clr('trx_ctrl', 0x02)
        if debug > 0:
            self.logger.log_info('TX disabled',2)


    def hw_sw_enable(self):
        self.regs.set('trx_ctrl', 0x08)
        self.trx_sw_ctrl = 'HW'

    def hw_sw_disable(self):
        self.regs.clr('trx_ctrl',0x8)
        self.trx_sw_ctrl = 'SW'

    def low_power_mode(self, on):
        if on == True:
            self.regs.wr('bias_tx', 0xAA11)
        else:
            self.regs.wr('bias_tx', 0xAAAA)
