class RxDrvDco(object):

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(RxDrvDco, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        import register
        import rf_rx as rx
        import rx_iq_meas
        import eder_status
        import evk_logger
        self.__initialized = True
        self.regs = register.Register()
        self.iq_meas = rx_iq_meas.RxIQMeas()
        self.rx = rx.Rx()
        self._decToVolt = self.iq_meas._decToVolt
        self.status  = eder_status.EderStatus()
        self.logger  = evk_logger.EvkLogger()

    def init(self):
        if self.status.init_bit_is_set(self.status.RXDRVDCO_INIT) == False:
            self.iq_meas.init()
            self.status.set_init_bit(self.status.RXDRVDCO_INIT)

    def default(self):
        self.regs.clr('rx_drv_dco', 0x000FFF00)

    def reset(self):
        self.default()
        self.iq_meas.reset()
        self.status.clr_init_bit(self.status.RXDRVDCO_INIT)

    def set_drv_offset(self, chan, offset):
        if chan == 'i' or chan == 'I':
            self.regs.clr('rx_drv_dco', 0b11111100000000000000)
            self.regs.set('rx_drv_dco', (offset & 0x3f) << 14)
        elif chan == 'q' or chan == 'Q':
            self.regs.clr('rx_drv_dco', 0b11111100000000)
            self.regs.set('rx_drv_dco', (offset & 0x3f) << 8)

    def get_drv_offset(self, chan):
        if chan == 'i' or chan == 'I':
            return (self.regs.rd('rx_drv_dco')>>14)&0x3f
        elif chan == 'q' or chan == 'Q':
            return (self.regs.rd('rx_drv_dco')>>8)&0x3f

    def dco_split(self, rx_drv_dco_reg):
        return {'sign':(rx_drv_dco_reg>>5)&0x1, 'offset':rx_drv_dco_reg&0x1f}
    
    def dco(self, sign, offset):
            return ((sign&0x1)<<5) + offset&0x1f

    def print_report(self, meas):
        dco_i = self.get_drv_offset('i')
        dco_q = self.get_drv_offset('q')

        self.logger.log_info('rx_drv_i_dco  : {:#05x} ({:#03x},{:#04x})'
                             .format(dco_i,self.dco_split(dco_i)['sign'],self.dco_split(dco_i)['offset']),2)
        self.logger.log_info('rx_drv_q_dco  : {:#05x} ({:#03x},{:#04x})'
                             .format(dco_q,self.dco_split(dco_q)['sign'],self.dco_split(dco_q)['offset']),2)
        self.logger.log_info('V_i_diff      : {:<4.2f} mV'.format(self._decToVolt(meas['idiff'])/(-2.845)*1000),2)
        self.logger.log_info('V_q_diff      : {:<4.2f} mV'.format(self._decToVolt(meas['qdiff'])/(-2.845)*1000),2)
        self.logger.log_info('V_i_com       : {:<1.3f} V'.format(self._decToVolt(meas['icm'])),2)
        self.logger.log_info('V_q_com       : {:<1.3f} V'.format(self._decToVolt(meas['qcm'])),2)

        
    def report(self, meas_type='sys'):
        self.print_report(self.iq_meas.meas(32,meas_type))

    def rx_drv_dco_cal(self, iq, mtype='sys'):
        if iq == 'i':
            diff = 'idiff'
        elif iq == 'q':
            diff = 'qdiff'
        else:
            print ('Invalid argument.')
            return

        sign = lambda x: x and (1, -1)[x < 0]

        selected_sign = -1

        START = 0
        MID = 1
        END = 2

        for offset_sign in range(0,2):
            self.set_drv_offset(iq, (offset_sign<<5))
            measured_values_0 = self.iq_meas.meas(meas_type=mtype)
            self.set_drv_offset(iq, (offset_sign<<5)|0x1f)
            measured_values_1 = self.iq_meas.meas(meas_type=mtype)
            if sign(measured_values_0[diff]) != sign(measured_values_1[diff]):
                selected_sign = offset_sign
                break

        if selected_sign == -1:
            self.logger.log_error('RX DRV DCO calibration failed!',2)
            return 0

        rx_drv_dco = [0,0,0]
        dco_diff = [0,0,0]

        rx_drv_dco[START] = 0
        rx_drv_dco[END] = 0x1F

        average = (rx_drv_dco[START] + rx_drv_dco[END]) / 2
        rx_drv_dco[MID] = int(round(average, 0))

        self.set_drv_offset(iq, (selected_sign<<5)|rx_drv_dco[START])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[START] = measured_values[diff]

        self.set_drv_offset(iq, (selected_sign<<5)|rx_drv_dco[MID])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[MID] = measured_values[diff]

        self.set_drv_offset(iq, (selected_sign<<5)|rx_drv_dco[END])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[END] = measured_values[diff]

        while (abs(rx_drv_dco[START]-rx_drv_dco[MID]) > 1) or (abs(rx_drv_dco[MID]-rx_drv_dco[END]) > 1):
            if sign(dco_diff[START]) == sign(dco_diff[MID]):
                rx_drv_dco[START] = rx_drv_dco[MID]
                average = (rx_drv_dco[START] + rx_drv_dco[END]) / 2
                rx_drv_dco[MID] = int(round(average, 0))
                dco_diff[START] = dco_diff[MID]
                self.set_drv_offset(iq, (selected_sign<<5)|rx_drv_dco[MID])
                measured_values = self.iq_meas.meas(meas_type=mtype)
                dco_diff[MID] = measured_values[diff]
            elif sign(dco_diff[END]) == sign(dco_diff[MID]):
                rx_drv_dco[END] = rx_drv_dco[MID]
                average = (rx_drv_dco[START] + rx_drv_dco[END]) / 2
                rx_drv_dco[MID] = int(round(average, 0))
                dco_diff[END] = dco_diff[MID]
                self.set_drv_offset(iq, (selected_sign<<5)|rx_drv_dco[MID])
                measured_values = self.iq_meas.meas(meas_type=mtype)
                dco_diff[MID] = measured_values[diff]
            else:
                # mid_dco diff is 0'
                # Doubble check
                if dco_diff[MID] == 0:
                    self.set_drv_offset(iq, (selected_sign<<5)|rx_drv_dco[MID])
                    break
                else:
                    print (iq)
                    self.logger.log_info('Something went wrong!!!!',2)
                    return 0

        dco_diff = list(map(abs, dco_diff))
        i = dco_diff.index(min(dco_diff))
        self.set_drv_offset(iq, (selected_sign<<5)|rx_drv_dco[i])

        return (selected_sign<<5)|rx_drv_dco[i]

    def run(self, trx_ctrl=0x00, rx_dco_en=0x01, trx_rx_on=0x1E0000, trx_rx_off=0x1E0000, gain=((0,0),0x11,0x11,0x77), verbose=1):
        if verbose >= 0:
            self.logger.log_info('Rx DRV DCO calibration')
        if verbose >= 1:
            self.logger.log_info('Rx DRV DCO status before calibration start:')
            self.report()

        # Backup register values
        trx_ctrl_save   = self.regs.rd('trx_ctrl')
        rx_dco_en_save  = self.regs.rd('rx_dco_en')
        trx_rx_on_save  = self.regs.rd('trx_rx_on')
        trx_rx_off_save = self.regs.rd('trx_rx_off')
        bfrf_gain       = self.regs.rd('rx_gain_ctrl_bfrf')
        bb1_gain        = self.regs.rd('rx_gain_ctrl_bb1')
        bb2_gain        = self.regs.rd('rx_gain_ctrl_bb2')
        bb3_gain        = self.regs.rd('rx_gain_ctrl_bb3')
        rx_bb_i_dco     = self.regs.rd('rx_bb_i_dco')
        rx_bb_q_dco     = self.regs.rd('rx_bb_q_dco')
        
        # Modify control registers
        self.regs.wr('trx_ctrl',    trx_ctrl)
        self.regs.wr('trx_rx_on',   trx_rx_on)
        self.regs.wr('trx_rx_off',  trx_rx_off)
        self.regs.wr('rx_dco_en',   rx_dco_en)
        self.regs.wr('rx_bb_i_dco', 0x40)
        self.regs.wr('rx_bb_q_dco', 0x40)
        if verbose >= 1:
            self.logger.log_info('Change Control settings:')
            self.logger.log_info('trx_ctrl      : {:#04x}     => {:#04x}'.format(trx_ctrl_save,self.regs.rd('trx_ctrl')),2)
            self.logger.log_info('rx_dco_en     : {:#04x}     => {:#04x}'.format(rx_dco_en_save,self.regs.rd('rx_dco_en')),2)
            self.logger.log_info('trx_rx_on     : {:#08x} => {:#08x}'.format(trx_rx_on_save,self.regs.rd('trx_rx_on')),2)
            self.logger.log_info('trx_rx_off    : {:#08x} => {:#08x}'.format(trx_rx_off_save,self.regs.rd('trx_rx_off')),2)
            self.logger.log_info('rx_bb_i_dco   : {:#05x}    => {:#05x}'.format(rx_bb_i_dco,self.regs.rd('rx_bb_i_dco')),2)
            self.logger.log_info('rx_bb_q_dco   : {:#05x}    => {:#05x}'.format(rx_bb_q_dco,self.regs.rd('rx_bb_q_dco')),2)
            self.logger.log_info('Rx DRV DCO status after control register change:')
            self.report()

        # Modify gain registers
        if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            lna_state = self.rx.lna_state()
            self.rx.lna_state(0)

        bfrf = bfrf_gain
        if gain[0][0] != None:
            bfrf = (bfrf & 0x0F) | (gain[0][0]<<4)
        if gain[0][1] != None:
            bfrf = (bfrf & 0xF0) | gain[0][1]
        self.regs.wr('rx_gain_ctrl_bfrf',bfrf)
        if gain[1] != None:
            self.regs.wr('rx_gain_ctrl_bb1', gain[1])
        if gain[2] != None:
            self.regs.wr('rx_gain_ctrl_bb2', gain[2])
        if gain[3] != None:
            self.regs.wr('rx_gain_ctrl_bb3', gain[3])
        if verbose >= 1:
            self.logger.log_info('Change Rx Gain settings:')
            self.logger.log_info('Rx BFRF gain  : {:#04x} => {:#04x}'.format(bfrf_gain,self.regs.rd('rx_gain_ctrl_bfrf')),2)
            self.logger.log_info('Rx BB1 gain   : {:#04x} => {:#04x}'.format(bb1_gain,self.regs.rd('rx_gain_ctrl_bb1')),2)
            self.logger.log_info('Rx BB2 gain   : {:#04x} => {:#04x}'.format(bb2_gain,self.regs.rd('rx_gain_ctrl_bb2')),2)
            self.logger.log_info('Rx BB3 gain   : {:#04x} => {:#04x}'.format(bb3_gain,self.regs.rd('rx_gain_ctrl_bb3')),2)
            if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
                self.logger.log_info('Rx LNA enable : {:#04x} => {:#04x}'.format(lna_state,self.rx.lna_state()),2)
            self.logger.log_info('Rx DRV DCO status after Rx gain change:')
            self.report(meas_type='sys')


        if verbose >= 0:
            self.logger.log_info('Rx DRV DCO status before calibration:')
            self.report()

        rx_drv_i_dco = self.rx_drv_dco_cal('i', 'sys')
        rx_drv_q_dco = self.rx_drv_dco_cal('q', 'sys')

        if verbose >= 0:
            self.logger.log_info('Rx DRV DCO status after calibration:')
            self.report()


        # Restore modified gain registers
        if verbose >= 1:
            self.logger.log_info('Restoring Rx Gain settings:')
            self.logger.log_info('Rx BFRF gain  : {:#04x} => {:#04x}'.format(self.regs.rd('rx_gain_ctrl_bfrf'),bfrf_gain),2)
            self.logger.log_info('Rx BB1 gain   : {:#04x} => {:#04x}'.format(self.regs.rd('rx_gain_ctrl_bb1'),bb1_gain),2)
            self.logger.log_info('Rx BB2 gain   : {:#04x} => {:#04x}'.format(self.regs.rd('rx_gain_ctrl_bb2'),bb2_gain),2)
            self.logger.log_info('Rx BB3 gain   : {:#04x} => {:#04x}'.format(self.regs.rd('rx_gain_ctrl_bb3'),bb3_gain),2)
            if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
                self.logger.log_info('Rx LNA enable : {:#04x} => {:#04x}'.format(self.rx.lna_state(),lna_state),2)
        if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            self.rx.lna_state(lna_state)
        self.regs.wr('rx_gain_ctrl_bfrf', bfrf_gain)
        self.regs.wr('rx_gain_ctrl_bb1', bb1_gain)
        self.regs.wr('rx_gain_ctrl_bb2', bb2_gain)
        self.regs.wr('rx_gain_ctrl_bb3', bb3_gain)
        if verbose >= 2:
            self.logger.log_info('Rx DRV DCO status after Rx Gain restore:')
            self.report(meas_type='sys')

        # Restore modified control registers
        if verbose >= 1:
            self.logger.log_info('Restoring control settings:')
            self.logger.log_info('trx_ctrl      : {:#04x}     => {:#04x}'.format(self.regs.rd('trx_ctrl'),trx_ctrl_save),2)
            self.logger.log_info('rx_dco_en     : {:#04x}     => {:#04x}'.format(self.regs.rd('rx_dco_en'),rx_dco_en_save),2)
            self.logger.log_info('trx_rx_on     : {:#08x} => {:#08x}'.format(self.regs.rd('trx_rx_on'),trx_rx_on_save),2)
            self.logger.log_info('trx_rx_off    : {:#08x} => {:#08x}'.format(self.regs.rd('trx_rx_off'),trx_rx_off_save),2)
            self.logger.log_info('rx_bb_i_dco   : {:#05x}    => {:#05x}'.format(self.regs.rd('rx_bb_i_dco'),rx_bb_i_dco),2)
            self.logger.log_info('rx_bb_q_dco   : {:#05x}    => {:#05x}'.format(self.regs.rd('rx_bb_q_dco'),rx_bb_q_dco),2)
        self.regs.wr('trx_ctrl',    trx_ctrl_save)
        self.regs.wr('trx_rx_on',   trx_rx_on_save)
        self.regs.wr('trx_rx_off',  trx_rx_off_save)
        self.regs.wr('rx_dco_en',   rx_dco_en_save)
        self.regs.wr('rx_bb_i_dco', rx_bb_i_dco)
        self.regs.wr('rx_bb_q_dco', rx_bb_q_dco)
        
        if verbose >= 1:
            self.logger.log_info('Rx DRV DCO status after register restore:')
            self.report()

        if verbose >= 0:
            self.logger.log_info('Rx DRV DCO calibration done')
        return rx_drv_i_dco, rx_drv_q_dco



    # FOR TEST ONLY
    def sweep_drv_reg(self, iq='i'):
        trx_ctrl = self.regs.rd('trx_ctrl')
        if trx_ctrl & 0x1:
            self.regs.set('trx_rx_on', 0x040000)
        else:
            self.regs.set('trx_rx_off', 0x1f0000)
        self.regs.wr('rx_dco_en',0x01)
        if iq == 'q':
            self.regs.wr('rx_bb_q_dco', 0x40)
        else:
            self.regs.wr('rx_bb_i_dco', 0x40)
        for i in range(0,2):
            print ('**'+str(i))
            for j in range(0, 0x20):
                if iq == 'q':
                    self.set_drv_offset('q', (i<<5)|j)
                else:
                    self.set_drv_offset('i', (i<<5)|j)
                measured_values = self.iq_meas.meas(meas_type='sys')
                if iq == 'q':
                    print (hex(self.regs.rd('rx_drv_dco')) + ',' + hex((i<<5)|j) + ',' + str(measured_values['qdiff']))
                else:
                    print (hex(self.regs.rd('rx_drv_dco')) + ',' + hex((i<<5)|j) + ',' + str(measured_values['idiff']))

    # FOR TEST ONLY
    def sweep_drv_reg_0002(self, iq='i'):
        if iq == 'q':
            self.regs.wr('rx_bb_q_dco', 0x40)
        else:
            self.regs.wr('rx_bb_i_dco', 0x40)
        for i in range(0,2):
            print ('**'+str(i))
            for j in range(0, 0x20):
                if iq == 'q':
                    self.set_drv_offset('q', (i<<5)|j)
                else:
                    self.set_drv_offset('i', (i<<5)|j)
                measured_values = self.iq_meas.meas(meas_type='sys')
                if iq == 'q':
                    print (hex(self.regs.rd('rx_drv_dco')) + ',' + hex((i<<5)|j) + ',' + str(measured_values['qdiff']))
                else:
                    print (hex(self.regs.rd('rx_drv_dco')) + ',' + hex((i<<5)|j) + ',' + str(measured_values['idiff']))
