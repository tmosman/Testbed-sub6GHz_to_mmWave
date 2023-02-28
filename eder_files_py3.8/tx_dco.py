import sys

class TxDco(object):
    import time

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(TxDco, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        import register
        import rx_iq_meas
        import temp
        import eder_status
        import evk_logger
        self.__initialized = True
        self.regs = register.Register()
        self.rx_iq_meas = rx_iq_meas.RxIQMeas()
        self.temp = temp.Temp()
        self.status = eder_status.EderStatus()
        self.logger = evk_logger.EvkLogger()
        
    def run(self, do_print=False):
        wait_time = 0.001
        result_ok = True
        import rf_rx as rx
        import rf_tx as tx
        tx = tx.Tx()
        rx = rx.Rx()

        # Store current gain settings
        trx_tx_on_stored = self.regs.rd('trx_tx_on')
        tx_bb_iq_gain_stored = self.regs.rd('tx_bb_iq_gain')
        tx_bb_gain_stored = self.regs.rd('tx_bb_gain')
        tx_bfrf_gain_stored = self.regs.rd('tx_bfrf_gain')
        trx_rx_on_stored = self.regs.rd('trx_rx_on')
        bias_lo_stored = self.regs.rd('bias_lo')
        tx_beam_store = tx.bf.awv.get()&0x3f
   
        rx_gain_ctrl_bb1_stored = self.regs.rd('rx_gain_ctrl_bb1')
        rx_gain_ctrl_bb2_stored = self.regs.rd('rx_gain_ctrl_bb2')
        rx_gain_ctrl_bb3_stored = self.regs.rd('rx_gain_ctrl_bb3')
        rx_gain_ctrl_bfrf_stored = self.regs.rd('rx_gain_ctrl_bfrf')
        rx_bb_test_ctrl_stored = self.regs.rd('rx_bb_test_ctrl')
        trx_ctrl_stored = self.regs.rd('trx_ctrl')
        bias_rx_stored = self.regs.rd('bias_rx')

        self.logger.log_info('freq: ' + str(tx.freq))
        
        tx.disable()
        rx.disable()
        rx.init(0x1F0000)
        self.regs.wr('trx_ctrl', 0x01)

        import numpy as np

        self.regs.wr('rx_gain_ctrl_bb1', 0xFF)
        self.regs.wr('rx_gain_ctrl_bb2', 0xFF)
        self.regs.wr('rx_gain_ctrl_bb3', 0x77)

        tx_rx_rf_gain = 0xff
        self.regs.wr('rx_gain_ctrl_bfrf', tx_rx_rf_gain & 0x0F)
        self.regs.wr('tx_bfrf_gain', (tx_rx_rf_gain >> 4) & 0x0F)

        rx.enable()
        if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            rx.drv_dco.run()
        rx.dco.run()
        #rx.dco.report('sys')

        rx.lna_state(0)
        
        self.regs.wr('trx_tx_on', 0x1F0000)
        self.regs.wr('bias_lo', 0x2A)
        self.regs.set('trx_ctrl', 0x03)


        #STEP 1: create parameters for calibration
        errorTXmax = 0         # maximum allowed error
        lower_limit= 4.0
        currentE   = 100       # place holder for error value
        stepI      = 6         # optimization step for I
        stepQ      = 6         # optimization step for Q
        MAX_INIT_ERROR = 2000  # Maximum initial error before starting loop
        max_err_divider = 45

        highest_corner_i = 0
        highest_corner_q = 0
        highest_e = 0
        previous_setting = [-1, -1]
        repeated_setting = 0

        # Check DCO at corners
        for currentI in range(0, 0x80, 0x7F):
            for currentQ in range(0, 0x80, 0x7F):
                self.regs.wr('tx_bb_i_dco', currentI)
                self.regs.wr('tx_bb_q_dco', currentQ)
                #time.sleep(wait_time)

                TRASH = tx.dco.rx_iq_meas.meas_vdiff()
                valI_lb  = TRASH['idiff']
                valQ_lb  = TRASH['qdiff']

                currentE = abs(valI_lb + 1j*valQ_lb)
                #self.logger.log_info('tx_bb_i_dco: 0x{0:02X}  tx_bb_q_dco: 0x{1:02X}  error: {2}'.format(int(currentI), int(currentQ), currentE))
                if currentE > highest_e:
                    highest_e = currentE
                    highest_corner_i = currentI
                    highest_corner_q = currentQ

        currentI = highest_corner_i
        currentQ = highest_corner_q
        currentE = 5000

        # Find max error
        self.regs.wr('tx_bb_i_dco', currentI)
        self.regs.wr('tx_bb_q_dco', currentQ)
        self.regs.set('tx_ctrl', 0x40)

        while currentE > MAX_INIT_ERROR:
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI_lb  = TRASH['idiff']
            valQ_lb  = TRASH['qdiff']

            self.regs.clr('tx_ctrl', 0x40)

            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']

            self.regs.set('tx_ctrl', 0x40)

            currentE = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))


            if currentE > MAX_INIT_ERROR:
                if tx_rx_rf_gain > 0x11:
                    if tx_rx_rf_gain&0x0f > 3:
                        tx_rx_rf_gain = tx_rx_rf_gain - 3
                    elif tx_rx_rf_gain&0x0f > 1:
                        tx_rx_rf_gain = tx_rx_rf_gain - 1
                    elif tx_rx_rf_gain&0xf0 > 0x20:
                        tx_rx_rf_gain = tx_rx_rf_gain - 0x20
                    elif tx_rx_rf_gain&0xf0 > 0x10:
                        tx_rx_rf_gain = tx_rx_rf_gain - 0x10
                    else:
                        break

                    self.regs.wr('rx_gain_ctrl_bfrf', tx_rx_rf_gain & 0x0F)
                    self.regs.wr('tx_bfrf_gain', (tx_rx_rf_gain >> 4) & 0x0F)
                else:
                    break

        self.logger.log_info('TX RF gain: ' + hex(tx_rx_rf_gain >> 4))
        self.logger.log_info('RX RF gain: ' + hex(tx_rx_rf_gain & 0x0F))
        print ('currentE: ' + str(currentE))

        errorTXmax = currentE / max_err_divider

        currentI   = 0x10
        currentQ   = 0x10

        max_no_of_iterations = 40
        update_errorTXmax = False

        #STEP 4: run the search using modified 2D Newton-Rhapson method
        while (currentE >= errorTXmax) and (currentE > lower_limit) :
            if currentE <= 100:
                stepI = 2
                stepQ = 2
            else:
                stepI = 6
                stepQ = 6

            # get rxDCoI & rxDCoQ @ I+step,Q and calculate the ERROR
            self.regs.wrrd('tx_bb_i_dco',currentI+stepI)
            self.regs.wrrd('tx_bb_q_dco',currentQ)
            #time.sleep(wait_time)
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI_lb  = TRASH['idiff']
            valQ_lb  = TRASH['qdiff']

            self.regs.clr('tx_ctrl', 0x40)
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            self.regs.set('tx_ctrl', 0x40)


            errorIP = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

            # get rxDCoI & rxDCoQ @ I-step,Q and calculate the ERROR
            self.regs.wrrd('tx_bb_i_dco',currentI-stepI)
            self.regs.wrrd('tx_bb_q_dco',currentQ)
            #time.sleep(wait_time)
            
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI_lb  = TRASH['idiff']
            valQ_lb  = TRASH['qdiff']

            self.regs.clr('tx_ctrl', 0x40)
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            self.regs.set('tx_ctrl', 0x40)

            errorIN = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

            # get rxDCoI & rxDCoQ @ I,Q+step and calculate the ERROR
            self.regs.wrrd('tx_bb_i_dco',currentI)
            self.regs.wrrd('tx_bb_q_dco',currentQ+stepQ)
            #time.sleep(wait_time)
            
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI_lb  = TRASH['idiff']
            valQ_lb  = TRASH['qdiff']

            self.regs.clr('tx_ctrl', 0x40)
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            self.regs.set('tx_ctrl', 0x40)

            errorQP = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

            # get rxDCoI & rxDCoQ @ I,Q-step and calculate the ERROR
            self.regs.wrrd('tx_bb_i_dco',currentI)
            self.regs.wrrd('tx_bb_q_dco',currentQ-stepQ)
            #time.sleep(wait_time)
            
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI_lb  = TRASH['idiff']
            valQ_lb  = TRASH['qdiff']

            self.regs.clr('tx_ctrl', 0x40)
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            self.regs.set('tx_ctrl', 0x40)

            errorQN = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

            # calculate the gradients for N-R iteration
            if (errorIP == errorIN) or (errorQP == errorQN):
            	continue
            slopeIQ = 1.5/((errorIP-errorIN) + 1j*(errorQP-errorQN))
            if (np.real(slopeIQ) == 0) or (np.imag(slopeIQ) == 0):
            	continue
            slopeI  =  1/np.real(slopeIQ)
            slopeQ  = -1/np.imag(slopeIQ)

            # calculate next I values for N-R iteration
            currentI = currentI + round(-1*currentE/slopeI)
            #print ('****')
            #print (currentI)
            if currentI   > 127:
                currentI = 0x28
            elif currentI <  0:
                currentI = 0x64
            #print currentI

            # calculate next Q values for N-R iteration
            #currentQ = currentQ + round(-2*currentE/slopeQ)
            currentQ = currentQ + round(-1*currentE/slopeQ)
            #print ('****')
            #print (currentQ)
            if currentQ   > 127:
                currentQ = 0x28
            elif currentQ <  0:
                currentQ = 0x64

            #print (currentQ)

            # measure new ERROR
            self.regs.wr('tx_bb_i_dco',currentI)
            self.regs.wr('tx_bb_q_dco',currentQ)
            #time.sleep(wait_time)
            
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI_lb  = TRASH['idiff']
            valQ_lb  = TRASH['qdiff']

            self.regs.clr('tx_ctrl', 0x40)
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            self.regs.set('tx_ctrl', 0x40)

            currentE = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

            self.logger.log_info('tx_bb_i_dco: 0x{0:02X}  tx_bb_q_dco: 0x{1:02X}  error: {2}'.format(int(currentI), int(currentQ), currentE))

            if update_errorTXmax:
                update_errorTXmax = False
                errorTXmax = currentE / max_err_divider
                if errorTXmax < 45.0: errorTXmax = 45.0
                print ('New errorTXmax: ' + str(errorTXmax))

            if previous_setting == [currentI, currentQ]:
                repeated_setting = repeated_setting + 1
            else:
                repeated_setting = 0
                previous_setting = [currentI, currentQ]

            if (currentE > MAX_INIT_ERROR) or (repeated_setting > 2) or (max_no_of_iterations == 10):
                if repeated_setting > 2:
                    repeated_setting = 0
                update_errorTXmax = True
                if tx_rx_rf_gain > 0x11:
                    max_no_of_iterations = 20

                    if tx_rx_rf_gain&0x0f > 3:
                        tx_rx_rf_gain = tx_rx_rf_gain - 3
                    elif tx_rx_rf_gain&0x0f > 1:
                        tx_rx_rf_gain = tx_rx_rf_gain - 1
                    elif tx_rx_rf_gain&0xf0 > 0x20:
                        tx_rx_rf_gain = tx_rx_rf_gain - 0x20
                    elif tx_rx_rf_gain&0xf0 > 0x10:
                        tx_rx_rf_gain = tx_rx_rf_gain - 0x10
                    else:
                        break

                    self.regs.wr('rx_gain_ctrl_bfrf', tx_rx_rf_gain & 0x0F)
                    self.regs.wr('tx_bfrf_gain', (tx_rx_rf_gain >> 4) & 0x0F)
                self.logger.log_info('TX RF gain: ' + hex(tx_rx_rf_gain >> 4))
                self.logger.log_info('RX RF gain: ' + hex(tx_rx_rf_gain & 0x0F))

            max_no_of_iterations = max_no_of_iterations - 1
            if max_no_of_iterations == 0:
                currentI = 0
                currentQ = 0
                self.logger.log_error('TX LO leakage calibration failed')
                result_ok = False
                break

        if result_ok:
            best_i_dac = currentI
            best_q_dac = currentQ

            for gain_inc_count in range(0,5):
                if tx_rx_rf_gain&0x0f < 0x0f:
                    tx_rx_rf_gain = tx_rx_rf_gain + 1
                elif tx_rx_rf_gain&0xf0 < 0xf0:
                    tx_rx_rf_gain = tx_rx_rf_gain + 0x10
                else:
                    break

            print (hex(tx_rx_rf_gain))

            self.regs.wr('rx_gain_ctrl_bfrf', tx_rx_rf_gain & 0x0F)
            self.regs.wr('tx_bfrf_gain', (tx_rx_rf_gain >> 4) & 0x0F)

            best_i_dac = 0
            best_q_dac = 0
            prev_e = 1000
            # Check around the to make sure we have optimal values
            for curr_i in range(int(currentI - 1), int(currentI + 2)):
                for curr_q in range(int(currentQ - 1), int(currentQ + 2)):
                    self.regs.wr('tx_bb_i_dco', curr_i)
                    self.regs.wr('tx_bb_q_dco', curr_q)
                    #time.sleep(wait_time)

                    TRASH = tx.dco.rx_iq_meas.meas_vdiff()
                    valI_lb  = TRASH['idiff']
                    valQ_lb  = TRASH['qdiff']

                    self.regs.clr('tx_ctrl', 0x40)
                    TRASH = tx.dco.rx_iq_meas.meas_vdiff()
                    valI  = TRASH['idiff']
                    valQ  = TRASH['qdiff']
                    self.regs.set('tx_ctrl', 0x40)

                    currentE = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

                    if currentE <= prev_e:
                        prev_e = currentE
                        best_i_dac = curr_i
                        best_q_dac = curr_q

            self.regs.wr('tx_bb_i_dco', best_i_dac)
            self.regs.wr('tx_bb_q_dco', best_q_dac)

            if ((int(best_i_dac) == 0) or (int(best_q_dac) == 0)):
                self.logger.log_info('TX LO leakage calibration failed')
                result_ok = False
            else:
                self.logger.log_info('TX LO leakage calibration complete.')
                self.logger.log_info('tx_bb_i_dco: ' + hex(best_i_dac))
                self.logger.log_info('tx_bb_q_dco: ' + hex(best_q_dac))

        self.regs.clr('tx_ctrl', 0x40)

        #STEP 5: print final I & Q values, final ERROR and number of iterations
        rx.disable()

        # Write back stored gain settings
        rx.status.clr_init_bit(rx.status.RX_INIT)
        self.regs.wr('trx_tx_on', trx_tx_on_stored)
        self.regs.wr('tx_bb_iq_gain', tx_bb_iq_gain_stored)
        self.regs.wr('tx_bb_gain', tx_bb_gain_stored)
        self.regs.wr('tx_bfrf_gain', tx_bfrf_gain_stored)
        self.regs.wr('trx_rx_on', trx_rx_on_stored)
        self.regs.wr('bias_lo', bias_lo_stored)
        self.regs.wr('rx_gain_ctrl_bb1', rx_gain_ctrl_bb1_stored)
        self.regs.wr('rx_gain_ctrl_bb2', rx_gain_ctrl_bb2_stored)
        self.regs.wr('rx_gain_ctrl_bb3', rx_gain_ctrl_bb3_stored)
        self.regs.wr('rx_gain_ctrl_bfrf', rx_gain_ctrl_bfrf_stored)
        self.regs.wr('rx_bb_test_ctrl',rx_bb_test_ctrl_stored)
        self.regs.wr('trx_ctrl', trx_ctrl_stored)
        self.regs.wr('bias_rx',bias_rx_stored)
        tx.set_beam(tx_beam_store)

        return result_ok

    def sweep_run(self):
        import rf_rx as rx
        import rf_tx as tx
        tx = tx.Tx()
        rx = rx.Rx()

        print ('freq: ' + str(tx.freq))

        tx.disable()
        rx.disable()
        rx.init(0x1F0000)
        self.regs.wr('trx_ctrl', 0x01)

        self.regs.wr('rx_gain_ctrl_bb1', 0xFF)
        self.regs.wr('rx_gain_ctrl_bb2', 0xFF)
        self.regs.wr('rx_gain_ctrl_bb3', 0x77)

        tx_rx_rf_gain = 0xf9
        self.regs.wr('rx_gain_ctrl_bfrf', tx_rx_rf_gain & 0x0F)
        self.regs.wr('tx_bfrf_gain', (tx_rx_rf_gain >> 4) & 0x0F)

        rx.enable()
        if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            rx.drv_dco.run()
        rx.dco.run()

        rx.lna_state(0)

        self.regs.wr('trx_tx_on', 0x1F0000)
        self.regs.wr('bias_lo', 0x2A)
        self.regs.set('trx_ctrl', 0x03)

        self.regs.set('tx_ctrl', 0x40)

        self.regs.wr('rx_gain_ctrl_bfrf', tx_rx_rf_gain & 0x0F)
        self.regs.wr('tx_bfrf_gain', (tx_rx_rf_gain >> 4) & 0x0F)
        self.logger.log_info('TX RF gain: ' + hex(tx_rx_rf_gain >> 4))
        self.logger.log_info('RX RF gain: ' + hex(tx_rx_rf_gain & 0x0F))

        for currentI in range(0, 0x80, 4):
            for currentQ in range(0, 0x80, 4):
                self.regs.wrrd('tx_bb_i_dco',currentI)
                self.regs.wrrd('tx_bb_q_dco',currentQ)
                TRASH = tx.dco.rx_iq_meas.meas_vdiff()
                valI_lb  = TRASH['idiff']
                valQ_lb  = TRASH['qdiff']

                self.regs.clr('tx_ctrl', 0x40)
                TRASH = tx.dco.rx_iq_meas.meas_vdiff()
                valI  = TRASH['idiff']
                valQ  = TRASH['qdiff']
                self.regs.set('tx_ctrl', 0x40)

                currentE = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))
                if sys.version_info.major > 2:
                    exec("print (str(currentE) + ', ',end='')")
                else:
                    exec("print str(currentE) + ', ',")
            print ('')
