from common import *

class Agc(object):

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Agc, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        self.internal_agc_on = False
        import register
        import eder_status
        import evk_logger
        self.bb_gain_lvl_table = dict()
        self.rf_gain_lvl_table = dict()
        self.regs = register.Register()
        self.status = eder_status.EderStatus()
        self.logger = evk_logger.EvkLogger()

    def reset(self):
        self.status.clr_init_bit(self.status.AGC_INIT)
        self.bb_gain_lvl_table = dict()
        self.rf_gain_lvl_table = dict()
        self.regs.wr('gpio_agc_rst_ctrl', 0b0000)

    def _import_file(self, fname, table):
        try:
            f = open(fname)
        except IOError:
            self.logger.log_info(fname + ' not found!')
            return
        line = '#'
        while line[0]=='#':
            # Ignore the header.
            # Header should always start with '#'
            line = f.readline()

        while True:
            if line == '':
                break
            line = line.replace('\n', '')
            line = line.replace('\r', '')
            line = line.split(',')
            table[line[0]] = line[1:len(line)]
            line = f.readline()
        f.close()

    def _strhexlist2intlist(self, strhexlist):
        int_list=[]
        for i in strhexlist:
            int_list.append(int(i,16))
        return int_list


    def init(self):
        if self.status.init_bit_is_set(self.status.AGC_INIT) == False:
            self.status.set_init_bit(self.status.AGC_INIT)
            self.logger.log_info('Chip agc init.',2)
        else:
            self.logger.log_info('Chip agc already initialized.',2)

    # Controls
    def enable(self):
        self.regs.set('rx_bb_en',0x40)
        self.regs.wr('agc_en',0x11)
        
    def disable(self):
        self.regs.clr('rx_bb_en',0x40)
        self.regs.wr('agc_en',0x00)

    def start(self):
        self.regs.tgl('agc_ctrl',1)

    def rst(self):
        self.regs.tgl('agc_ctrl',2)
        
        
        
    # Reporting
    def status(self):
        return self.regs.rd('agc_status'), self.regs.rd('agc_status_detector')

    def get_gain(self):
        return self.regs.rd('agc_gain_db'), self.regs.rd('agc_gain_bits')



    # Gain level handling
    def import_bb_gain_lvl_file(self, fname):
        self._import_file(fname, self.bb_gain_lvl_table)

    def import_rf_gain_lvl_file(self, fname):
        self._import_file(fname, self.rf_gain_lvl_table)


    def set_bb_gain_lvl(self, index):
        if isinstance(index,list) or isinstance(index,tuple):
            self.regs.wr('agc_bb_gain_1db_lvl',intlist2int(index,16))
        else:
            self.regs.wr('agc_bb_gain_1db_lvl',intlist2int(self._strhexlist2intlist(self.bb_gain_lvl_table[str(index)])))
        return

    def set_rf_gain_lvl(self, index):
        if isinstance(index,list) or isinstance(index,tuple):
            self.regs.wr('agc_bf_rf_gain_lvl',intlist2int(index))
        else:
            self.regs.wr('agc_bf_rf_gain_lvl', intlist2int(self._strhexlist2intlist(self.rf_gain_lvl_table[str(index)])))
        return

    def set_gain_lvl(self, temperature):
        """Sets BB, BF and RF gains corresponding to the specified temperature.
           Temperature is given in Celsius and will be converted to multiple of 5.
        """
        if isinstance(temperature,list) or isinstance(temperature,tuple):
            gain_list = temperature
            if len(gain_list) == 10:
                self.set_rf_gain_lvl(gain_list[0:4])            
                self.set_bb_gain_lvl(gain_list[4:10])            
            if len(gain_list) == 2:
                self.set_rf_gain_lvl(gain_list[0])            
                self.set_bb_gain_lvl(gain_list[1])            
            if len(gain_list) == 6:
                self.set_bb_gain_lvl(gain_list)            
            if len(gain_list) == 4:
                self.set_rf_gain_lvl(gain_list)            
        else:
            if self.bb_gain_lvl_table == {} or self.rf_gain_lvl_table == {}:
                self.logger.log_info('Both agc_bb_gain_1db and agc_bf_rf_gain should be imported.')
            else:
                self.set_bb_gain_lvl(int(5 * round(float(temperature)/5)))
                self.set_rf_gain_lvl(int(5 * round(float(temperature)/5)))


    def get_gain_lvl(self):
        return int2intlist(self.regs.rd('agc_bf_rf_gain_lvl'),256,4), int2intlist(self.regs.rd('agc_bb_gain_1db_lvl'),16,6)

    def enable_int(self, on):
        if on == True:
            self.rx_gain_ctrl_mode = self.regs.rd('rx_gain_ctrl_mode')
            self.agc_ext_ctrl = self.regs.rd('agc_ext_ctrl')
            self.agc_int_en_ctrl = self.regs.rd('agc_int_en_ctrl')
            self.regs.clr('rx_gain_ctrl_mode', 0x13)
            self.regs.set('rx_gain_ctrl_mode', 1)
            self.regs.wr('agc_ext_ctrl', 0)
            self.regs.wr('agc_int_en_ctrl', 0x17)
            self.regs.wr('agc_int_pdet_th', 0x0065556688)
            self.regs.wr('agc_int_start_del', 100)
            self.regs.wr('agc_int_timeout', 250)
            self.internal_agc_on = True
        elif on == False:
            self.regs.wr('rx_gain_ctrl_mode', self.rx_gain_ctrl_mode)
            self.regs.wr('agc_ext_ctrl', self.agc_ext_ctrl)
            self.regs.wr('agc_int_en_ctrl', self.agc_int_en_ctrl)
            self.internal_agc_on = False

    def start_int(self):
        if self.internal_agc_on == True:
            self.regs.tgl('agc_int_ctrl', 2)
            self.regs.tgl('agc_int_ctrl', 1)
        else:
            print ('Internal AGC should be Enabled first')

    def reduced_ref_clk(self, on):
        if on == True:
            self.pll_ld_mux_ctrl = self.regs.rd('pll_ld_mux_ctrl')
            self.fast_clk_ctrl = self.regs.rd('fast_clk_ctrl')
            self.regs.clr('pll_ld_mux_ctrl', 0x0f)
            self.regs.set('pll_ld_mux_ctrl', 0x02)
            self.regs.wr('fast_clk_ctrl', 0x01)
        elif on == False:
            try:
                self.regs.wr('pll_ld_mux_ctrl', self.pll_ld_mux_ctrl)
                self.regs.wr('fast_clk_ctrl', self.fast_clk_ctrl)
            except:
                pass
