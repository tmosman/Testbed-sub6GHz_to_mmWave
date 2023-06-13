import time
import sys
import keyboard

class Alc(object):
    # tx_bfrf_gain
    # tx_bf_pdet_mux
    # tx_alc_ctrl
    # tx_alc_loop_cnt
    # tx_alc_start_delay
    # tx_alc_meas_delay
    # tx_alc_bfrf_gain_max
    # tx_alc_bfrf_gain_min
    # tx_alc_step_max
    # tx_alc_pdet_lo_th
    # tx_alc_pdet_hi_offs_th
    # tx_alc_bfrf_gain (RO)
    # tx_alc_pdet (RO)

    __instance         = None
    __is_started       = False
    __last_gain_mode   = None

    GAIN_MODE_BITS     = 0x60
    TX_PAUSE_ADJUST    = 0x00
    TX_ACTIVE_ADJUST   = 0x20
    TX_INACTIVE_ADJUST = 0x40
    TX_BOTH_ADJUST     = 0x60
    ENABLE             = 0x01
    START              = 0x02
    TEMP_COMP_EN       = 0x10
    RF_B4_BF           = 0x80

    def __new__(cls, parent):
        if cls.__instance is None:
            cls.__instance = super(Alc, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, parent):
        if self.__initialized:
            return
        import dig_pll
        import temp
        import adc
        import amux
        import register
        import eeprom_prod_data
        import evk_logger
        self.eeprom_prod_data = eeprom_prod_data.EepromProdData()
        self.dig_pll = dig_pll.Dig_Pll()
        self.regs   = register.Register()
        self.amux   = amux.Amux(self.regs)
        self.adc    = adc.Adc()
        self.temp   = temp.Temp()
        self.logger = evk_logger.EvkLogger()
        self.parent = parent
        self.__initialized = True

    def init(self):
        alc_ctrl = self.TEMP_COMP_EN | self.RF_B4_BF | self.TX_INACTIVE_ADJUST # 0xD0
        alc_data = self.eeprom_prod_data.get_alc_data()
        if alc_data != None:
            self.logger.log_info('ALC calibration data found in EEPROM', 2)
            channel = self.find_closest_channel(self.parent.freq)
            self.regs.wr('tx_bfrf_gain', alc_data[3*(channel-1) + 2])
            self.regs.wr('tx_alc_pdet_lo_th', alc_data[3*(channel-1) + 1])
            self.regs.wr('tx_alc_pdet_hi_offs_th', alc_data[3*(channel-1) + 0])
        else:
            self.regs.wr('tx_alc_pdet_lo_th', 0x80)
            self.regs.wr('tx_alc_pdet_hi_offs_th', 0x04)
        self.regs.wr('tx_alc_ctrl', alc_ctrl)
        self.regs.wr('tx_alc_loop_cnt', 0x00)
        self.regs.wr('tx_alc_start_delay', self.dig_pll.cycles(2))   # 2 us
        self.regs.wr('tx_alc_meas_delay',  self.dig_pll.cycles(1))   # 1 us
        self.regs.wr('tx_alc_bfrf_gain_max', 0xff)
        self.regs.wr('tx_alc_bfrf_gain_min', 0x00)
        self.regs.wr('tx_alc_step_max', 0x13)
        self.regs.set('tx_bf_pdet_mux', 0x80)
        self.__is_started = False

    
    def enable(self):
        self.regs.set('tx_alc_ctrl', 0x01)

    def disable(self):
        self.regs.clr('tx_alc_ctrl', 0x03)
        self.__is_started = False


    def start(self):
        if (self.regs.rd('tx_alc_ctrl') & 0x01) == 0x01:
            self.regs.tgl('tx_alc_ctrl', 0x02)
        else:
            self.regs.clr('tx_alc_ctrl', 0x03)
            self.regs.set('tx_alc_ctrl', 0x03)
        self.__is_started = True

    def stop(self):
        if (self.regs.rd('tx_alc_ctrl') & 0x01) == 0x01:
            self.regs.clr('tx_alc_ctrl', 0x03)
            self.regs.set('tx_alc_ctrl', 0x01)
        else:
            self.regs.clr('tx_alc_ctrl', 0x03)
        self.__is_started = False

    def is_started(self):
        return self.__is_started
    
    def is_enabled(self):
        return self.is_enable()
    
    def is_enable(self):
        if self.regs.rd('tx_alc_ctrl') & 0x01:
            return True
        else:
            return False

    def status(self):
        self.logger.log_info('tx_alc_bfrf_gain : ' + hex(self.regs.rd('tx_alc_bfrf_gain')),2)
        self.logger.log_info('tx_alc_pdet      : ' + hex(self.regs.rd('tx_alc_pdet')),2)

    def setup_dump(self):
        self.logger.log_info('tx_alc_ctrl            : ' + hex(self.regs.rd('tx_alc_ctrl')),2)
        self.logger.log_info('tx_alc_loop_cnt        : ' + hex(self.regs.rd('tx_alc_loop_cnt')),2)
        self.logger.log_info('tx_alc_start_delay     : ' + hex(self.regs.rd('tx_alc_start_delay')),2)
        self.logger.log_info('tx_alc_meas_delay      : ' + hex(self.regs.rd('tx_alc_meas_delay')),2)
        self.logger.log_info('tx_alc_bfrf_gain_max   : ' + hex(self.regs.rd('tx_alc_bfrf_gain_max')),2)
        self.logger.log_info('tx_alc_bfrf_gain_min   : ' + hex(self.regs.rd('tx_alc_bfrf_gain_min')),2)
        self.logger.log_info('tx_alc_step_max        : ' + hex(self.regs.rd('tx_alc_step_max')),2)
        self.logger.log_info('tx_alc_pdet_lo_th      : ' + hex(self.regs.rd('tx_alc_pdet_lo_th')),2)
        self.logger.log_info('tx_alc_pdet_hi_offs_th : ' + hex(self.regs.rd('tx_alc_pdet_hi_offs_th')),2)
        self.logger.log_info('tx_alc_bfrf_gain (RO)  : ' + hex(self.regs.rd('tx_alc_bfrf_gain')),2)
        self.logger.log_info('tx_alc_pdet      (RO)  : ' + hex(self.regs.rd('tx_alc_pdet')),2)
        self.logger.log_info('tx_bf_pdet_mux         : ' + hex(self.regs.rd('tx_bf_pdet_mux')),2)


    def gain_mode_set(self, mode=None):
        self.__last_gain_mode = self.gain_mode_get()
        if mode == None:
            mode = self.TX_INACTIVE_ADJUST
        self.regs.clr('tx_alc_ctrl', self.GAIN_MODE_BITS)
        self.regs.set('tx_alc_ctrl', mode)
        return mode

    def gain_mode_get(self):
        return self.regs.rd('tx_alc_ctrl') & self.GAIN_MODE_BITS

    def gain_mode_print(self):
        res = self.gain_mode_get()
        if res == self.TX_PAUSE_ADJUST:
            res = 'TX_PAUSE_ADJUST'
        elif res == self.TX_ACTIVE_ADJUST:
            res = 'TX_ACTIVE_ADJUST'
        elif res == self.TX_INACTIVE_ADJUST:
            res = 'TX_INACTIVE_ADJUST'
        elif res == self.TX_BOTH_ADJUST:
            res = 'TX_BOTH_ADJUST'
        else:
            res = 'No proper gain mode!'
        return res

    def pause(self):
        self.gain_mode_set(self.TX_PAUSE_ADJUST)

    def resume(self):
        self.gain_mode_set(self.__last_gain_mode)        

    def pdet_src_set(self, pdet):
        self.regs.wr('tx_bf_pdet_mux',0x80|pdet)
        return self.regs.rd('tx_bf_pdet_mux')

    def pdet_src_get(self):
        return self.regs.rd('tx_bf_pdet_mux')


    def pdet_th(self, tx_alc_pdet_lo_th=None, tx_alc_pdet_hi_offs_th=None):
        if tx_alc_pdet_lo_th != None:
            self.regs.wr('tx_alc_pdet_lo_th', tx_alc_pdet_lo_th)
        if tx_alc_pdet_hi_offs_th != None:
            self.regs.wr('tx_alc_pdet_hi_offs_th', tx_alc_pdet_hi_offs_th)
        return self.regs.rd('tx_alc_pdet_lo_th'), self.regs.rd('tx_alc_pdet_hi_offs_th')


    def pdet_th_lo_trim(self,src=None, count=1000, debug=None):
        if debug:
            self.logger.log_info('tx_alc_pdet_lo_th      : ' + hex(self.regs.rd('tx_alc_pdet_lo_th')),2)

        # Store for restore
        enabled   = self.is_enabled()
        started   = self.is_started()
        gain_mode = self.gain_mode_get()
        src1,src2 = self.amux.get()
        if src == None:
            src = self.regs.rd('tx_bf_pdet_mux')
        self.amux.set(self.amux.amux_tx_pdet, 0x80|src)

        # Set TX_PAUSE_ADJUST mode to check pdet-flags
        self.gain_mode_set(self.TX_PAUSE_ADJUST)
        if not started:
            self.start()
        pdet_th = 0
        for i in range(7, -1, -1):
            pdet_th += (1<<i)
            self.regs.wr('tx_alc_pdet_lo_th', pdet_th)
            lo_cnt = 0
            for j in range(0, count):
                if (self.regs.rd('tx_alc_pdet') & 0x01 == 0x01):
                    lo_cnt += 1
            if debug:
                self.logger.log_info('pdet_lo_th, lo_cnt: ' + hex(pdet_th) + ', ' + str(lo_cnt),4)
            if lo_cnt > 0:
                pdet_th -= (1<<i)
        self.regs.wr('tx_alc_pdet_lo_th', pdet_th)
        if debug:
            lo_cnt = 0
            for j in range(0, count):
                if (self.regs.rd('tx_alc_pdet') & 0x01 == 0x01):
                    lo_cnt += 1
            self.logger.log_info('pdet_lo_th, lo_cnt: ' + hex(pdet_th) + ', ' + str(lo_cnt),4)

        # Restore from store
        self.amux.set(src1,src2)
        self.gain_mode_set(gain_mode)
        if not started:
            self.stop()
        if not enabled:
            self.disable()
                
        return pdet_th


    def pdet_th_hi_trim(self,src=None, count=1000, debug=None):
        if debug:
            self.logger.log_info('tx_alc_pdet_hi_offs_th : ' + hex(self.regs.rd('tx_alc_pdet_hi_offs_th')),2)

        # Store for restore
        enabled   = self.is_enabled()
        started   = self.is_started()
        gain_mode = self.gain_mode_get()
        src1,src2 = self.amux.get()
        if src == None:
            src = self.regs.rd('tx_bf_pdet_mux')
        self.amux.set(self.amux.amux_tx_pdet, 0x80|src)

        # Set TX_PAUSE_ADJUST mode to check pdet-flags
        self.gain_mode_set(self.TX_PAUSE_ADJUST)
        if not started:
            self.start()
        pdet_th = 31
        for i in range(4, -1, -1):
            pdet_th -= (1<<i)
            self.regs.wr('tx_alc_pdet_hi_offs_th', pdet_th)
            hi_cnt = 0
            for j in range(0, count):
                if (self.regs.rd('tx_alc_pdet') & 0x02 == 0x02):
                    hi_cnt += 1
            if debug:
                self.logger.log_info('pdet_hi_offs_th, hi_cnt: ' + hex(pdet_th) + ', ' + str(hi_cnt),4)
            if hi_cnt > 0:
                pdet_th += (1<<i)
        self.regs.wr('tx_alc_pdet_hi_offs_th', pdet_th)
        if debug:
            hi_cnt = 0
            for j in range(0, count):
                if (self.regs.rd('tx_alc_pdet') & 0x02 == 0x02):
                    hi_cnt += 1
            self.logger.log_info('pdet_hi_offs_th, hi_cnt: ' + hex(pdet_th) + ', ' + str(hi_cnt),4)

        # Restore from store
        self.amux.set(src1,src2)
        self.gain_mode_set(gain_mode)
        if not started:
            self.stop()
        if not enabled:
            self.disable()
                
        return pdet_th



    def pdet_cnt(self, pdet_src=None, count=1000, debug=None):
        src1,src2 =  self.amux.get()
        if pdet_src == None:
            pdet_src = self.regs.rd('tx_bf_pdet_mux')
        self.amux.set(self.amux.amux_tx_pdet, 0x80|pdet_src)
        lo_cnt=0
        ok_cnt=0
        hi_cnt=0
        for j in range(0, count):
            status = self.regs.rd('tx_alc_pdet')
            if (status & 0x01 == 0x01):
                lo_cnt += 1
            if (status & 0x02 == 0x02):
                hi_cnt += 1
            if (status & 0x03 == 0x00):
                ok_cnt += 1
            if debug:
                self.logger.log_info("{:02X} {:d} {:d} {:d}".format(status,lo_cnt,ok_cnt,hi_cnt))
        self.amux.set(src1,src2)
        return lo_cnt, ok_cnt, hi_cnt


    def pdet_dump(self):
        bist_amux_ctrl = self.regs.rd('bist_amux_ctrl')
        tx_bf_pdet_mux = self.regs.rd('tx_bf_pdet_mux')
        self.logger.log_info("                                                    Tx Antenna                                                      ")
        self.logger.log_info("             0      1      2      3      4      5      6      7      8      9     10     11     12     13     14     15   ")
        row0_string = 'Pdet     :'
        row1_string = 'Pdet_peak:'
        row2_string = 'ALC Hi/Lo:'
        for pdet in range(0, 16):
            self.adc.start(self.amux.amux_tx_pdet, 0x80|pdet, 7)
            adc_pdet = self.adc.mean()
            self.adc.stop()
            self.adc.start(0x80|self.amux.amux_tx_env_pdet, 0x80|pdet, 7)
            adc_env_pdet = self.adc.mean()
            self.adc.stop()
            row0_string += ' {:0{}d}  '.format(adc_pdet,4)
            row1_string += ' {:0{}d}  '.format(adc_env_pdet,4)
            row2_string += '  {:0{}b}   '.format(self.regs.rd('tx_alc_pdet'),2)
        self.logger.log_info(row0_string)
        self.logger.log_info(row1_string)
        self.logger.log_info(row2_string)
        self.regs.wrrd('bist_amux_ctrl',bist_amux_ctrl)
        self.regs.wrrd('tx_bf_pdet_mux',tx_bf_pdet_mux)


    def pdet_meas(self,pdet):
        bist_amux_ctrl = self.regs.rd('bist_amux_ctrl')
        tx_bf_pdet_mux = self.regs.rd('tx_bf_pdet_mux')
        self.adc.start(self.amux.amux_tx_pdet, 0x80|pdet, 7)
        adc_pdet = self.adc.mean()
        self.adc.stop()
        self.regs.wrrd('bist_amux_ctrl',bist_amux_ctrl)
        self.regs.wrrd('tx_bf_pdet_mux',tx_bf_pdet_mux)
        return adc_pdet

    def pdet_peak_meas(self,pdet):
        bist_amux_ctrl = self.regs.rd('bist_amux_ctrl')
        tx_bf_pdet_mux = self.regs.rd('tx_bf_pdet_mux')
        self.adc.start(0x80|self.amux.amux_tx_env_pdet, 0x80|pdet, 7)
        adc_pdet = self.adc.mean()
        self.adc.stop()
        self.regs.wrrd('bist_amux_ctrl',bist_amux_ctrl)
        self.regs.wrrd('tx_bf_pdet_mux',tx_bf_pdet_mux)
        return adc_pdet



    def monitor(self,pdet):
        import evkplatform

        self.evkplatform = evkplatform.EvkPlatform()

        self.logger.log_info("Controls:",2)
        self.logger.log_info("q - Exit monitor",2)
        self.logger.log_info("e - Toggle Tx enable/disable",2)
        self.logger.log_info("d - Toggle Tx ALC regulate during Tx On/Tx off",2)
        self.logger.log_info("a - Toggle Tx ALC enable/disable",2)
        self.logger.log_info("s - Toggle Tx ALC start/stop",2)
        self.logger.log_info("r - Increase Tx BF gain",2)
        self.logger.log_info("c - Decrease Tx BF gain",2)
        self.logger.log_info("t - Increase Tx RF gain",2)
        self.logger.log_info("v - Decrease Tx RF gain",2)
        self.logger.log_info("y - Increase low threshold level",2)
        self.logger.log_info("b - Decrease low threshold level",2)
        self.logger.log_info("u - Increase high threshold level",2)
        self.logger.log_info("n - Decrease high threshold level",2)
        self.logger.log_info("Tx En  ALC En  ALC Reg  ALC start  BFRF gain  ALC gain  lo th  hi th  pdet_ind  pdet_adc  pdet_peak_adc  temp (C)",2)
        self.logger.log_info("=====  ======  =======  =========  =========  ========  =====  =====  ========  ========  =============  ========",2)
        run = True
        self.regs.clr('trx_ctrl', 3)
        self.regs.set('trx_ctrl', 8)
        while run:
            tx_is_enabled  = self.parent.is_enabled()
            alc_is_enabled = self.is_enabled()
            alc_is_started = self.is_started()
            alc_reg_tx_on  = (self.regs.rd('tx_alc_ctrl') & 0x60)>>5
            lo_th, hi_th   = self.pdet_th()
            bfrf_gain      = self.regs.rd('tx_bfrf_gain')
            alc_gain       = self.regs.rd('tx_alc_bfrf_gain')
            pdet_ind       = self.regs.rd('tx_alc_pdet')
            pdet_adc       = self.pdet_meas(pdet)
            pdet_peak_adc  = self.pdet_peak_meas(pdet)
            temp           = self.temp.run('C')
            sys.stdout.write("    {:d}       {:d}       {:d}         {:d}        {:#04x}       {:#04x}     {:3d}    {:2d}        {:1d}       {:4d}         {:4d}        {:3.2f}    \r"
                             .format(tx_is_enabled,alc_is_enabled,alc_reg_tx_on,alc_is_started,bfrf_gain,alc_gain,lo_th,hi_th,pdet_ind,pdet_adc,pdet_peak_adc,temp))
            sys.stdout.flush()
            if keyboard.is_pressed('e'):
                if tx_is_enabled:
                    self.evkplatform.drv.settxrxsw(0)
                else:
                    self.evkplatform.drv.settxrxsw(1)
            if keyboard.is_pressed('a'):
                if alc_is_enabled:
                    self.disable()
                else:
                    self.enable()
            if keyboard.is_pressed('s'):
                if alc_is_started:
                    self.stop()
                else:
                    self.start()
            if keyboard.is_pressed('d'):
                if (alc_reg_tx_on & 1):
                    self.regs.clr('tx_alc_ctrl',0x20)
                else:
                    self.regs.set('tx_alc_ctrl',0x20)
            if keyboard.is_pressed('r'):
                if (bfrf_gain & 0xF0) < 0xF0:
                    self.regs.wr('tx_bfrf_gain',bfrf_gain + 0x10)
            if keyboard.is_pressed('c'):
                if (bfrf_gain & 0xF0) > 0x00:
                    self.regs.wr('tx_bfrf_gain',bfrf_gain - 0x10)
            if keyboard.is_pressed('t'):
                if (bfrf_gain & 0x0F) < 0x0F:
                    self.regs.wr('tx_bfrf_gain',bfrf_gain + 0x01)
            if keyboard.is_pressed('v'):
                if (bfrf_gain & 0x0F) > 0x00:
                    self.regs.wr('tx_bfrf_gain',bfrf_gain - 0x01)
            if keyboard.is_pressed('y'):
                if lo_th < 0xFF:
                    self.pdet_th(lo_th + 1)
            if keyboard.is_pressed('b'):
                if lo_th > 0:
                    self.pdet_th(lo_th - 1)
            if keyboard.is_pressed('u'):
                if hi_th < 0x1F:
                    self.pdet_th(None,hi_th + 1)
            if keyboard.is_pressed('n'):
                if hi_th > 0:
                    self.pdet_th(None,hi_th - 1)
            if keyboard.is_pressed('q'):
                run = False
            time.sleep(0.1)

        sys.stdout.write("\n")
        sys.stdout.flush()

    def find_closest_channel(self, freq):
        channel_list = {1: 58.32e9, 2: 60.48e9, 3: 62.64e9, 4: 64.80e9, 5: 66.96e9, 6: 69.12e9}
        closest_channel = 1
        lowest_freq_diff = 1e11 
        for channel in channel_list:
            if abs(freq - channel_list[channel]) <= lowest_freq_diff:
                closest_channel = channel
                lowest_freq_diff = abs(freq - channel_list[channel])
        return closest_channel
