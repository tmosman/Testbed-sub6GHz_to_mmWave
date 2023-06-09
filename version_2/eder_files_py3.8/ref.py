class Ref(object):

    __instance = None 

    freq = 45e6               # XO reference frequency
    freq_alt = 40e6           # Alternative XO reference frequency
    freq_sel_limit = (freq + freq_alt)/2


    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Ref, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import register
        import eder_status
        import evk_logger
        self.regs = register.Register()
        self.status = eder_status.EderStatus()
        self.logger = evk_logger.EvkLogger()

    def reset(self):
        self.status.clr_init_bit(self.status.REF_INIT)

    def init(self, freq=None):
        if self.status.init_bit_is_set(self.status.REF_INIT) == False:
            self.regs.set('bias_ctrl',0x1c)
            self.regs.set('bias_pll',0x07)
            self.regs.set('pll_en',0x08)
            
            #self.regs.set('pll_ld_mux_ctrl', 1)
            #self.regs.wr('fast_clk_ctrl',0x21)
            self.regs.wr('fast_clk_ctrl',0x20)
            self.regs.wr('pll_ref_in_lvds_en',0x01)

            freq = self.set(freq)
            if freq >= self.freq_sel_limit:
                self.regs.set('fast_clk_ctrl',0x20)
            else:
                self.regs.clr('fast_clk_ctrl',0x20)

            self.logger.log_info("Reference frequency: %.2f MHz" % (freq/1e6),2)
            self.logger.log_info('Chip REF init.',2)
            self.status.set_init_bit(self.status.REF_INIT)
        else:
            self.logger.log_info("Reference frequency: %.2f MHz" % (self.get()/1e6),2)
            self.logger.log_info('Chip REF already initialized.',2)


    def cycles(self, time_in_us):
        return int(time_in_us*self.freq/1e6+0.5)-1


    def set(self, freq=None):
        if freq != None:
            self.freq = freq
            self.reset()
            self.init()
        return self.freq

    def get(self):
        return self.freq


    def monitor(self, src_on=True):
        if (src_on == True) or (src_on == 1) or (src_on == 'on') or (src_on == 'enable'):
            self.regs.clr('pll_ld_mux_ctrl',0x07)
            self.regs.set('pll_ld_mux_ctrl',0x02)
        else:
            self.regs.clr('pll_ld_mux_ctrl',0x07)

