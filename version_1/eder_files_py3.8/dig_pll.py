class Dig_Pll(object):

    __instance = None 
    freq   = None           # dig_pll frequency calculated from settings
                            # in fast_clk_ctrl
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Dig_Pll, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import register
        import eder_status
        import evk_logger
        import ref

        self.regs   = register.Register()
        self.status = eder_status.EderStatus()
        self.logger = evk_logger.EvkLogger()
        self.ref    = ref.Ref()

    def reset(self):
        self.status.clr_init_bit('DIGPLL')

    def get(self):
        fast_clk_ctrl_reg = self.regs.rd('fast_clk_ctrl') & 0x10
        if fast_clk_ctrl_reg == 0x10:
            self.freq = self.ref.get() * 5
        elif fast_clk_ctrl_reg == 0x00:
            self.freq = self.ref.get() * 4
        return self.freq

    def cycles(self, time_in_us):
        return int(time_in_us*self.get()/1e6+0.5)-1

    
