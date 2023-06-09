class RxDco(object):

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(RxDco, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        import register
        import rx_iq_meas
        import rf_rx as rx
        import eder_status
        import evk_logger
        self.__initialized = True
        self.regs    = register.Register()
        self.iq_meas = rx_iq_meas.RxIQMeas()
        self.rx = rx.Rx()
        self._decToVolt = self.iq_meas._decToVolt
        self.status  = eder_status.EderStatus()
        self.logger  = evk_logger.EvkLogger()

    def init(self):
        if self.status.init_bit_is_set(self.status.RXDCO_INIT) == False:
            self.iq_meas.init()
            self.status.set_init_bit(self.status.RXDCO_INIT)

    def default(self):
        self.regs.wr('rx_bb_q_dco',self.regs.value('rx_bb_q_dco'))
        self.regs.wr('rx_bb_i_dco',self.regs.value('rx_bb_i_dco'))

    def reset(self):
        self.default()
        self.iq_meas.reset()
        self.status.clr_init_bit(self.status.RXDCO_INIT)


    def dco_split(self,dco_reg):
        return {'mult':(dco_reg>>12)&0x3, 'shift':(dco_reg>>8)&0x3, 'val':dco_reg&0x7f}
    
    def dco(self, mult, shift, val):
            return (mult<<12) + (shift<<8) + val

    def print_report(self, meas):
        trx_ctrl=self.regs.rd('trx_ctrl')
        self.regs.wr('trx_ctrl', 0x01)		
        dco_i = self.regs.rd('rx_bb_i_dco')
        dco_q = self.regs.rd('rx_bb_q_dco')
        self.logger.log_info('rx_bb_i_dco   : {:#05x} ({:#03x},{:#03x},{:#04x})'
                             .format(dco_i,self.dco_split(dco_i)['mult'],self.dco_split(dco_i)['shift'],self.dco_split(dco_i)['val']),2)
        self.logger.log_info('rx_bb_q_dco   : {:#05x} ({:#03x},{:#03x},{:#04x})'
                             .format(dco_q,self.dco_split(dco_q)['mult'],self.dco_split(dco_q)['shift'],self.dco_split(dco_q)['val']),2)
        self.logger.log_info('V_i_diff      : {:<4.2f} mV'.format(self._decToVolt(meas['idiff'])/(-2.845)*1000),2)
        self.logger.log_info('V_q_diff      : {:<4.2f} mV'.format(self._decToVolt(meas['qdiff'])/(-2.845)*1000),2)
        self.logger.log_info('V_i_com       : {:<1.3f} V'.format(self._decToVolt(meas['icm'])),2)
        self.logger.log_info('V_q_com       : {:<1.3f} V'.format(self._decToVolt(meas['qcm'])),2)
        self.regs.wr('trx_ctrl', trx_ctrl)


    def report(self, meas_type='sys'):
        self.print_report(self.iq_meas.meas(32,meas_type))


    def run_dco_cal(self, iq, mtype='sys'):

        if iq == 'i':
            register = 'rx_bb_i_dco'
            diff = 'idiff'
        elif iq == 'q':
            register = 'rx_bb_q_dco'
            diff = 'qdiff'
        else:
            self.logger.log_error('Invalid argument.')
            return -1, -1

        sign = lambda x: x and (1, -1)[x < 0]

        selected_mult = -1
        selected_shift = -1
        for mult in range(0,4):
            if selected_mult != -1:
                break
            for shift in range(0,3):
                self.regs.wr(register, (mult<<12) + (shift<<8))
                measured_values_0 = self.iq_meas.meas(meas_type=mtype)
                self.regs.wr(register, (mult<<12)+(shift<<8)+0x7F)
                measured_values_1 = self.iq_meas.meas(meas_type=mtype)
                if sign(measured_values_0[diff]) != sign(measured_values_1[diff]):
                    selected_mult = mult
                    selected_shift = shift
                    break

        if selected_mult == -1:
            self.logger.log_info('RX DCO calibration failed!')
            return 0,0

        START = 0
        MID = 1
        END = 2

        rx_bb_dco = [0,0,0]
        dco_diff = [0,0,0]

        rx_bb_dco[START] = 0
        rx_bb_dco[END] = 0x7F

        average = (rx_bb_dco[START] + rx_bb_dco[END]) / 2
        rx_bb_dco[MID] = int(round(average, 0))

        self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[START])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[START] = measured_values[diff]

        self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[MID])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[MID] = measured_values[diff]

        self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[END])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[END] = measured_values[diff]

        while (abs(rx_bb_dco[START]-rx_bb_dco[MID]) > 1) or (abs(rx_bb_dco[MID]-rx_bb_dco[END]) > 1):
            if sign(dco_diff[START]) == sign(dco_diff[MID]):
                rx_bb_dco[START] = rx_bb_dco[MID]
                average = (rx_bb_dco[START] + rx_bb_dco[END]) / 2
                rx_bb_dco[MID] = int(round(average, 0))
                dco_diff[START] = dco_diff[MID]
                self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[MID])
                measured_values = self.iq_meas.meas(meas_type=mtype)
                dco_diff[MID] = measured_values[diff]
            elif sign(dco_diff[END]) == sign(dco_diff[MID]):
                rx_bb_dco[END] = rx_bb_dco[MID]
                average = (rx_bb_dco[START] + rx_bb_dco[END]) / 2
                rx_bb_dco[MID] = int(round(average, 0))
                dco_diff[END] = dco_diff[MID]
                self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[MID])
                measured_values = self.iq_meas.meas(meas_type=mtype)
                dco_diff[MID] = measured_values[diff]
            else:
                # mid_dco diff is 0'
                # Doubble check
                if dco_diff[MID] == 0:
                    self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[MID])
                    break
                else:
                    self.logger.log_error('Something went wrong!!!')
                    return 0, 0
            #print rx_bb_dco
            #print dco_diff
            
        dco_diff_abs = list(map(abs, dco_diff))
        i = dco_diff_abs.index(min(dco_diff_abs))
            
        self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[i])
        return (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[i], dco_diff[i]


    def int_run(self, meas_type='sys'):
        rx_bb_i_dco, dco_i = self.run_dco_cal('i', meas_type)
        rx_bb_q_dco, dco_q = self.run_dco_cal('q', meas_type)
        return rx_bb_i_dco, rx_bb_q_dco, dco_i, dco_q

    def lab_run(self):
        self.rx.drv_dco.run(gain=((0,0),0x11,0x11,0x77), trx_ctrl=0x00, rx_dco_en=0x01, trx_rx_on=0x1E0000, trx_rx_off=0x1E0000, verbose=1)
        self.run(trx_ctrl=0x01, rx_dco_en=0x01, trx_rx_on=0x1FFFFF, trx_rx_off=0x1FFFFF, gain=((None,None),None,None,None), beam=self.rx.get_beam(), lna=1, verbose=1)

    def run(self, trx_ctrl=0x01, rx_dco_en=0x01, trx_rx_on=None, trx_rx_off=None, gain=((None,None),None,None,None), beam=63, lna=0, verbose=1):
        if verbose >= 0:
            self.logger.log_info('Rx BB DCO calibration')
        if verbose >= 1:
            self.logger.log_info('Rx BB DCO status before calibration start:')
            self.report(meas_type='sys')

        # Backup register values
        trx_ctrl_save   = self.regs.rd('trx_ctrl')
        rx_dco_en_save  = self.regs.rd('rx_dco_en')
        trx_rx_on_save  = self.regs.rd('trx_rx_on')
        trx_rx_off_save = self.regs.rd('trx_rx_off')
        bfrf_gain       = self.regs.rd('rx_gain_ctrl_bfrf')
        bb1_gain        = self.regs.rd('rx_gain_ctrl_bb1')
        bb2_gain        = self.regs.rd('rx_gain_ctrl_bb2')
        bb3_gain        = self.regs.rd('rx_gain_ctrl_bb3')
        beam_save       = self.rx.get_beam()
        
        # Modify control registers
        self.regs.wr('trx_ctrl',   trx_ctrl)
        self.regs.wr('rx_dco_en',  rx_dco_en)
        if trx_rx_on != None:
            self.regs.wr('trx_rx_on',  trx_rx_on)
        if trx_rx_off != None:
            self.regs.wr('trx_rx_off', trx_rx_off)
        if verbose >= 1:
            self.logger.log_info('Change Control settings:')
            self.logger.log_info('trx_ctrl      : {:#04x}     => {:#04x}'.format(trx_ctrl_save,self.regs.rd('trx_ctrl')),2)
            self.logger.log_info('rx_dco_en     : {:#04x}     => {:#04x}'.format(rx_dco_en_save,self.regs.rd('rx_dco_en')),2)
            self.logger.log_info('trx_rx_on     : {:#08x} => {:#08x}'.format(trx_rx_on_save,self.regs.rd('trx_rx_on')),2)
            self.logger.log_info('trx_rx_off    : {:#08x} => {:#08x}'.format(trx_rx_off_save,self.regs.rd('trx_rx_off')),2)
            self.logger.log_info('Rx BB DCO status after control register change:')
            self.report(meas_type='sys')

        # Modify gain registers
        if self.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            lna_state = self.rx.lna_state()
            self.rx.lna_state(lna)
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
            self.logger.log_info('Rx BB DCO status after Rx gain change:')
            self.report(meas_type='sys')

        # Modify beam
        self.rx.set_beam(beam)
        if verbose >= 1:
            self.logger.log_info('Change Rx beam:')
            self.logger.log_info('Rx beam       : {:#04x} => {:#04x}'.format(beam_save,self.rx.get_beam()),2)
            self.logger.log_info('Rx BB DCO status after Rx beam change:')
            self.report(meas_type='sys')


        if verbose >= 0:
            self.logger.log_info('Rx BB DCO status before calibration:')
            self.report(meas_type='sys')

        # Run calibration
        rx_bb_i_dco, rx_bb_q_dco, dco_i, dco_q = self.int_run()
        
        if verbose >= 0:
            self.logger.log_info('Rx BB DCO status after calibration:')
            self.report(meas_type='sys')

        # Restore beam
        if verbose >= 1:
            self.logger.log_info('Restore Rx beam:')
            self.logger.log_info('Rx beam       : {:#04x} => {:#04x}'.format(self.rx.get_beam(),beam_save),2)
        self.rx.set_beam(beam_save)
        if verbose >= 2:
            self.logger.log_info('Rx BB DCO status after Rx beam restore:')
            self.report(meas_type='sys')

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
            self.logger.log_info('Rx BB DCO status after Rx Gain restore:')
            self.report(meas_type='sys')

        # Restore modified control registers
        if verbose >= 1:
            self.logger.log_info('Restoring control settings:')
            self.logger.log_info('trx_ctrl      : {:#04x}     => {:#04x}'.format(self.regs.rd('trx_ctrl'),trx_ctrl_save),2)
            self.logger.log_info('trx_rx_on     : {:#08x} => {:#08x}'.format(self.regs.rd('trx_rx_on'),trx_rx_on_save),2)
            self.logger.log_info('trx_rx_off    : {:#08x} => {:#08x}'.format(self.regs.rd('trx_rx_off'),trx_rx_off_save),2)
        self.regs.wr('trx_ctrl',   trx_ctrl_save)
        self.regs.wr('trx_rx_on',  trx_rx_on_save)
        self.regs.wr('trx_rx_off', trx_rx_off_save)
        if verbose >= 1:
            self.logger.log_info('Rx BB DCO status after register restore:')
            self.report(meas_type='sys')

        if verbose >= 0:
            self.logger.log_info('Rx BB DCO calibration done')
        return rx_bb_i_dco, rx_bb_q_dco, dco_i, dco_q

