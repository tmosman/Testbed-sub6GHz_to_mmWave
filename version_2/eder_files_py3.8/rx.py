class Rx(object):

    __instance = None
    trx_rx_on_default = 0x1FFFFF
    trx_ctrl = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Rx, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import evk_configuration
        import bf
        import agc
        import pll
        import rx_dco
        import rx_drv_dco
        import temp
        import register
        import memory
        import gpio
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
        self.regs = register.Register()
        self.mems = memory.Memory()
        self.gpio  = gpio.EderGpio(self.regs.evkplatform_type)
        self.bf   = bf.Bf(bf.Bf.RX)
        self.agc  = agc.Agc()
        self.pll  = pll.Pll()
        self.dco = rx_dco.RxDco()
        self.drv_dco = rx_drv_dco.RxDrvDco()
        self.temp = temp.Temp()
        self.logger = evk_logger.EvkLogger()
        self.status = eder_status.EderStatus()
        if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            self.lna_state(0)
        #

    def __default(self):
        self.regs.wr('trx_rx_on',self.regs.value('trx_rx_on'))
        self.regs.wr('bias_rx',self.regs.value('bias_rx'))
        self.regs.clr('bias_lo',0x20)
        self.regs.wr('rx_bb_biastrim',self.regs.value('rx_bb_biastrim'))
        self.regs.wr('rx_dco_en',self.regs.value('rx_dco_en'))
        self.regs.wr('rx_gain_ctrl_bb1',self.regs.value('rx_gain_ctrl_bb1'))
        self.regs.wr('rx_gain_ctrl_bb2',self.regs.value('rx_gain_ctrl_bb2'))
        self.regs.wr('rx_gain_ctrl_bb3',self.regs.value('rx_gain_ctrl_bb3'))
        self.regs.wr('rx_gain_ctrl_bfrf',self.regs.value('rx_gain_ctrl_bfrf'))
        self.dco.default()

    def set_beam(self, beam=None):
        restore_trx_ctrl = self.regs.rd('trx_ctrl')
        self.regs.wr('trx_ctrl', 0x01)
        if beam != None:
            self.bf.awv.set(beam)
        else:
            self.bf.awv.set(self.bf.awv.get()&0x3f)
        self.regs.wr('trx_ctrl',restore_trx_ctrl)

    def get_beam(self):
        return (self.bf.awv.get() & 0x3f)

    def reset(self):
        self.__default()
        self.status.clr_init_bit(self.status.RX_INIT)
        self.trx_rx_on_default = 0x1FFFFF
        self.trx_sw_ctrl = None
        self.logger.log_info('RX Reset',2)
    

    def init(self, trx_rx_on=trx_rx_on_default):
        if self.status.init_bit_is_set(self.status.RX_INIT) == False:
            self.regs.wr('trx_rx_on', trx_rx_on)
            if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
                self.regs.wr('bias_rx',0xAA9)
            else:
                self.regs.wr('bias_rx',0xAAA)
            self.regs.set('bias_ctrl',0x7F)
            self.regs.set('bias_lo',0x22)
            self.regs.wr('rx_bb_biastrim',0x00)
            self.regs.wr('rx_gain_ctrl_mode', 0x13)
            self.regs.wr('rx_dco_en',0x01)
            self.regs.wr('rx_gain_ctrl_bb1',0x77)
            self.regs.wr('rx_gain_ctrl_bb2',0x11) 
            self.regs.wr('rx_gain_ctrl_bb3',0x77)
            self.regs.wr('rx_gain_ctrl_bfrf',0x66)
            # Check if a setting file exists
            try:
                filename = self.config.__path__[0] + '\\rx_default.json'
                self.loadGainSettings(filename)
            except:
                pass
            self.set_beam(32)
            self.status.set_init_bit(self.status.RX_INIT)
            self.logger.log_info('RX Initialised',2)

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

    def setup(self, freq, beam=None, trx_rx_on=trx_rx_on_default):
        self.freq = freq
        # Import beamforming table and write to memory
        # TODO: Here we should prepare for writing the beambook
        # freq 0.0 and temp 0.0 fills bf_rx_awv with zeros
        self.logger.log_info('Loading beambook',2)
        self.bf.awv.setup(freq)
        self.bf.idx.setup(self.beambook_path + '/bf_rx_awv_idx')
        self.init(trx_rx_on)
        self.set_beam(beam)

        import time
        print ('Wait for temperature stabilization')
        previous_temp = 0
        current_temp = self.temp.run()

        while (current_temp - previous_temp) > 0.1:
                previous_temp = current_temp
                time.sleep(5)
                current_temp = self.temp.run()
                print ('temp: {0} C'.format(round(current_temp-273.15,2)))

        self.logger.log_info('Temperature stabilized',2)

        if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            self.drv_dco.run()

        self.dco.run()
        self.logger.log_info('RX Setup completed',2)

    def setup_no_dco_cal(self, freq, beam=None, trx_rx_on=trx_rx_on_default):
        self.freq = freq
        self.logger.log_info('Loading beambook',2)
        self.bf.awv.setup(freq)
        self.bf.idx.setup(self.beambook_path + '/bf_rx_awv_idx')
        self.init(trx_rx_on)
        self.set_beam(beam)
        self.logger.log_info('RX Setup completed',2)



    def enable(self, beam=None):
        if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            self.lna_state(1)
        if self.trx_ctrl == None:
            if (self.regs.rd('trx_ctrl') & 0x08):
                self.trx_ctrl = 'HW'
            else:
                self.trx_ctrl = 'SW'

        if self.trx_ctrl == 'HW':
            self.gpio.set_rx_mode()
        else:
            self.regs.set('trx_ctrl', 0x01)

        self.set_beam(beam)
        self.logger.log_info('RX enabled',2)

            

    def disable(self):
        if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            self.lna_state(0)
        if self.trx_ctrl == None:
            if (self.regs.rd('trx_ctrl') & 0x08):
                self.trx_ctrl = 'HW'
            else:
                self.trx_ctrl = 'SW'

        self.regs.clr('trx_ctrl', 0x01)
        self.logger.log_info('RX disabled',2)


    def hw_sw_enable(self):
        self.regs.set('trx_ctrl',0x08)
        self.trx_sw_ctrl = 'HW'

    def hw_sw_disable(self):
        self.regs.clr('trx_ctrl',0x08)
        self.trx_sw_ctrl = 'SW'

    def lna_state(self, state=None):
        if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            if state == None:
                return self.regs.rd('rx_drv_dco')&1
            else:
                if state == 1:
                    self.regs.set('rx_drv_dco', 1)
                elif state == 0:
                    self.regs.clr('rx_drv_dco', 1)
                return state
        else:
            return None

    def gain_set(self, stage, gain):
        if isinstance(stage,list):
            gain  = stage
            
            if len(gain) == 2:
                stage = '12'
            if len(gain) == 3:
                stage = '123'
            if len(gain) == 4:
                stage = 'bfrf123'
            
        if stage == 'rf':
            gain_rd = self.regs.rd('rx_gain_ctrl_bfrf')
            self.regs.wr('rx_gain_ctrl_bfrf', (gain_rd & 0xF0) | (gain & 0x0F))
        if stage == 'bf':
            gain_rd = self.regs.rd('rx_gain_ctrl_bfrf')
            self.regs.wr('rx_gain_ctrl_bfrf', (gain_rd & 0x0F) | ((gain & 0x0F)<<4))
        if stage == 'bfrf':
            self.regs.wr('rx_gain_ctrl_bfrf', gain)
        if stage == '1':
            self.regs.wr('rx_gain_ctrl_bb1', (gain & 0x0F) | ((gain & 0x0F)<<4))
        if stage == '2':
            self.regs.wr('rx_gain_ctrl_bb2', (gain & 0x0F) | ((gain & 0x0F)<<4))
        if stage == '3':
            self.regs.wr('rx_gain_ctrl_bb3', (gain & 0x0F) | ((gain & 0x0F)<<4))
        if stage == '12':
            self.regs.wr('rx_gain_ctrl_bb1', (gain[0] & 0x0F) | ((gain[0] & 0x0F)<<4))
            self.regs.wr('rx_gain_ctrl_bb2', (gain[1] & 0x0F) | ((gain[1] & 0x0F)<<4))
        if stage == '123':
            self.regs.wr('rx_gain_ctrl_bb1', (gain[0] & 0x0F) | ((gain[0] & 0x0F)<<4))
            self.regs.wr('rx_gain_ctrl_bb1', (gain[1] & 0x0F) | ((gain[1] & 0x0F)<<4))
            self.regs.wr('rx_gain_ctrl_bb1', (gain[2] & 0x0F) | ((gain[2] & 0x0F)<<4))
        if stage == 'bfrf123':
            self.regs.wr('rx_gain_ctrl_bfrf', gain[0])
            self.regs.wr('rx_gain_ctrl_bb1', (gain[1] & 0x0F) | ((gain[1] & 0x0F)<<4))
            self.regs.wr('rx_gain_ctrl_bb2', (gain[2] & 0x0F) | ((gain[2] & 0x0F)<<4))
            self.regs.wr('rx_gain_ctrl_bb3', (gain[3] & 0x0F) | ((gain[3] & 0x0F)<<4))
            
    def gain_get(self, stage=None):
        if stage == None:
            stage = 'bfrf123'
        if stage == 'rf':
            return self.regs.rd('rx_gain_ctrl_bfrf') & 0x0F
        if stage == 'bf':
            return (self.regs.rd('rx_gain_ctrl_bfrf') & 0xF0)>>4
        if stage == 'bfrf':
            return self.regs.rd('rx_gain_ctrl_bfrf')
        if stage == '1':
            return (self.regs.rd('rx_gain_ctrl_bb1') & 0xF0) >> 4, (self.regs.rd('rx_gain_ctrl_bb1') & 0x0F)
        if stage == '2':
            return (self.regs.rd('rx_gain_ctrl_bb2') & 0xF0) >> 4, (self.regs.rd('rx_gain_ctrl_bb2') & 0x0F)
        if stage == '3':
            return (self.regs.rd('rx_gain_ctrl_bb3') & 0xF0) >> 4, (self.regs.rd('rx_gain_ctrl_bb3') & 0x0F)
        if stage == '12':
            return self.regs.rd('rx_gain_ctrl_bb1'), self.regs.rd('rx_gain_ctrl_bb2')
        if stage == '123':
            return self.regs.rd('rx_gain_ctrl_bb1'), self.regs.rd('rx_gain_ctrl_bb2'), self.regs.rd('rx_gain_ctrl_bb3'), self.regs.rd('rx_bb_i_vga_1db')
        if stage == 'bfrf123':
            return self.regs.rd('rx_gain_ctrl_bfrf'), self.regs.rd('rx_gain_ctrl_bb1'), self.regs.rd('rx_gain_ctrl_bb2'), self.regs.rd('rx_gain_ctrl_bb3')

    def low_power_mode(self, on):
        if on == True:
            self.regs.wr('bias_rx',0xA51)
        else:
            self.regs.wr('bias_rx',0xAAA)

