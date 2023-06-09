class TrxSoftSw(object):
    
    import common
    import dig_pll

    trx_soft_rx_on_enables = [0x14, 0x14, 0x14, 0x14, 0x1e, 0x1e, 0x1e, 0x1e]
    trx_soft_tx_on_enables = [0x06, 0x06, 0x16, 0x16, 0x16, 0x1e, 0x1e, 0x1e]

    def __init__(self):
        import register
        import evk_logger
        self.regs = register.Register()
        self.dig_pll = self.dig_pll.Dig_Pll()
        self.logger  = evk_logger.EvkLogger()
        
    def init(self, max_state=7, delay=0.015, bf_on_grp_sel=0x12345678):
        self.logger.log_info('')
        self.logger.log_info('Softswitch settings',2)
        self.logger.log_info('State:                    0     1     2     3     4     5     6     7 ', 4)
        self.logger.log_info('trx_soft_rx_on_enables:  {}  {}  {}  {}  {}  {}  {}  {}'.format( TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_rx_on_enables[0],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_rx_on_enables[1],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_rx_on_enables[2],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_rx_on_enables[3],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_rx_on_enables[4],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_rx_on_enables[5],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_rx_on_enables[6],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_rx_on_enables[7],2) )  \
                                                                                        ,4 )
        self.logger.log_info('trx_soft_tx_on_enables:  {}  {}  {}  {}  {}  {}  {}  {}'.format( TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_tx_on_enables[0],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_tx_on_enables[1],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_tx_on_enables[2],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_tx_on_enables[3],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_tx_on_enables[4],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_tx_on_enables[5],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_tx_on_enables[6],2),  \
                                                                                        TrxSoftSw.common.fhex(TrxSoftSw.trx_soft_tx_on_enables[7],2) )  \
                                                                                        ,4 )
        self.logger.log_info('max_state: {}'.format(max_state),4)
        self.logger.log_info('delay: {}us   {} cycles'.format(delay, self.dig_pll.cycles(delay)),4)
        self.logger.log_info('bf_on_grp_sel: {}'.format(hex(bf_on_grp_sel)),4)
        self.logger.log_info('')

        self.regs.wr('trx_soft_delay', self.dig_pll.cycles(delay))
        self.regs.wr('trx_soft_max_state', max_state)
        self.regs.wr('trx_soft_tx_on_enables', self.common.intlist2int(self.trx_soft_tx_on_enables))
        self.regs.wr('trx_soft_rx_on_enables', self.common.intlist2int(self.trx_soft_rx_on_enables))
        self.regs.wr('trx_soft_bf_on_grp_sel', bf_on_grp_sel)

    def enable(self, txrx_soft_sw):
        if txrx_soft_sw == 'rx':
            self.regs.set('trx_soft_ctrl', 1)
        elif txrx_soft_sw == 'tx':
            self.regs.set('trx_soft_ctrl', 2)
        elif txrx_soft_sw == 'txrx':
            self.regs.set('trx_soft_ctrl', 3)

    def disable(self, txrx_soft_sw):
        if txrx_soft_sw == 'rx':
            self.regs.clr('trx_soft_ctrl', 1)
        elif txrx_soft_sw == 'tx':
            self.regs.clr('trx_soft_ctrl', 2)
        elif txrx_soft_sw == 'txrx':
            self.regs.clr('trx_soft_ctrl', 3)
