import time
import sys

class Mbist(object):

    __instance = None
    import math

    def __new__(cls, board_type='Unspecified'):
        if cls.__instance is None:
            cls.__instance = super(Mbist, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, board_type='Unspecified'):
        if self.__initialized:
            return
        import pll
        import adc
        import temp
        import rf_rx as rx
        import rf_tx as tx
        import gpio
        import register
        import memory
        import evk_logger
        self.board_type = board_type
        self.pll  = pll.Pll()
        self.adc    = adc.Adc()
        self.temp = temp.Temp()
        self.rx = rx.Rx()
        self.tx = tx.Tx()
        self.gpio = gpio.EderGpio(self.board_type)
        self.regs   = register.Register(self.board_type)
        self.mems = memory.Memory(self.board_type)
        self.logger = evk_logger.EvkLogger()
        self.__initialized = True

    def reset(self):
        self.pll.reset()
        self.adc.reset()
        self.temp.reset()
        self.rx.reset()
        self.tx.reset()
        self.gpio.reset(100)
        self.logger.log_info('Mbist Chip reset.',2)


    def init(self, minimal=True):
        if minimal == True:
            self.pll.init()
            self.temp.init()
        else:
            self.pll.init()
            self.temp.init()
            

    def run(self, port='all', reset=False, init=False, minimal=True):
        if (port == 'a') or (port == 0):
            port = (0,)
        elif (port == 'b') or (port == 1):
            port = (1,)
        elif (port == 'all') or (port == 'both'):
            port = (0, 1)
        elif (port != 0) and (port != 1):
            print ("Port must be 0 or 'a' or 1 or 'b' or 'all' or 'both'")
            return NULL
        if reset:
            self.reset()
        if init:
            self.init(minimal)

        result = True
        for p_sel in port:
            print ('---------------------------------------------------------')
            print ('                 ' + str(p_sel))
            print ('---------------------------------------------------------')
            bf_rx_mbist_done = self.mems.mbist.rd('bf_rx_mbist_done')
            bf_tx_mbist_done = self.mems.mbist.rd('bf_tx_mbist_done')
            result = result and (bf_rx_mbist_done == 0) and (bf_tx_mbist_done == 0)
            print ('[RX] done ' + hex(bf_rx_mbist_done) + ' (should be 0x0)')
            print ('[TX] done ' + hex(bf_tx_mbist_done) + ' (should be 0x0)')
        
            bf_rx_mbist_result = self.mems.mbist.rd('bf_rx_mbist_result')
            bf_tx_mbist_result = self.mems.mbist.rd('bf_tx_mbist_result')
            result = result and (bf_rx_mbist_result == 0) and (bf_tx_mbist_result == 0)
            print ('[RX] result ' + hex(bf_rx_mbist_result) + ' (should be 0x0)')
            print ('[TX] result ' + hex(bf_tx_mbist_result) + ' (should be 0x0)')
        
            self.mems.mbist.wr('bf_rx_mbist_2p_sel', p_sel)
            self.mems.mbist.wr('bf_tx_mbist_2p_sel', p_sel)
            self.mems.mbist.wr('bf_rx_mbist_en',0xFFFF)
            self.mems.mbist.wr('bf_tx_mbist_en',0xFFFF)
        
            bf_rx_mbist_done = self.mems.mbist.rd('bf_rx_mbist_done')
            bf_tx_mbist_done = self.mems.mbist.rd('bf_tx_mbist_done')
            result = result and (bf_rx_mbist_done == 0xffff) and (bf_tx_mbist_done == 0xffff)
            print ('[RX] done ' + hex(bf_rx_mbist_done) + ' (should be 0xffff)')
            print ('[TX] done ' + hex(bf_tx_mbist_done) + ' (should be 0xffff)')

            bf_rx_mbist_result = self.mems.mbist.rd('bf_rx_mbist_result')
            bf_tx_mbist_result = self.mems.mbist.rd('bf_tx_mbist_result')
            result = result and (bf_rx_mbist_result == 0) and (bf_tx_mbist_result == 0)
            print ('*** MBIST Result ***')
            print ('[RX] result ' + hex(bf_rx_mbist_result) + ' (should be 0x0)')
            print ('[TX] result ' + hex(bf_tx_mbist_result) + ' (should be 0x0)')

            self.mems.mbist.wr('bf_rx_mbist_en',0x0000)
            self.mems.mbist.wr('bf_tx_mbist_en',0x0000)
            print

        print ('---------------------------------------------------------')
        if result == True:
            print ('MBIST             [OK]')
        else:
            print ('MBIST RX:0x{0:04X} TX:0x{1:04X} [FAIL]'.format(bf_rx_mbist_result, bf_tx_mbist_result))
        if reset:
            self.reset()
        return result
