class Test(object):

    import math
    import time
    import threading

    def __init__(self, eder):
	    self.eder = eder

    def run_all(self):
        self.check_spi()
        self.check_i2c()
        self.check_45mhz()
        self.mbist()
		
    def check_spi(self):
        if self.eder.check():
            print ('SPI check         [OK]')
            return True
        print ('SPI check         [FAIL]')
        return False
		
    def check_i2c(self):
        temp = self.eder.eeprom.read_pcb_temp()
        if temp > 0.0:
            print ('I2C check         [OK]')
            return True
        print ('I2C check         [FAIL]')
        return False
		
    def check_45mhz(self):
        temp = self.eder.temp.run()
        if temp > 0.0:
            print ('45MHz clock check [OK]')
            return True
        print ('45MHz clock check [FAIL]')
        return False
		
    def mbist(self, port):
        if (port != 0) and (port != 0):
            print ('Port must be 0 or 1')
            return NULL
        self.eder.reset()   
        self.eder.init()
        bf_rx_mbist_done = self.eder.mems.mbist.rd('bf_rx_mbist_done')  # Check that this is all zeroes
        print (bf_rx_mbist_done)
        bf_tx_mbist_done = self.eder.mems.mbist.rd('bf_tx_mbist_done')  # Check that this is all zeroes
        print (bf_tx_mbist_done)
        result = (bf_rx_mbist_done == 0) and (bf_tx_mbist_done == 0)

        bf_rx_mbist_result = self.eder.mems.mbist.rd('bf_rx_mbist_result')  # Check that this is all zeroes
        print (bf_rx_mbist_result)
        bf_tx_mbist_result = self.eder.mems.mbist.rd('bf_tx_mbist_result')  # Check that this is all zeroes
        print (bf_tx_mbist_result)
        result = result and (bf_rx_mbist_result == 0) and (bf_tx_mbist_result == 0)

        self.eder.mems.mbist.wr('bf_rx_mbist_2p_sel', port)
        self.eder.mems.mbist.wr('bf_tx_mbist_2p_sel', port)
        self.eder.mems.mbist.wr('bf_rx_mbist_en',0xFFFF)
        self.eder.mems.mbist.wr('bf_tx_mbist_en',0xFFFF)
        bf_rx_mbist_done = self.eder.mems.mbist.rd('bf_rx_mbist_done')  # Check that this is all ones
        print (bf_rx_mbist_done)
        bf_tx_mbist_done = self.eder.mems.mbist.rd('bf_tx_mbist_done')  # Check that this is all ones
        print (bf_tx_mbist_done)
        result = result and (bf_rx_mbist_done == 0xFFFF) and (bf_tx_mbist_done == 0xFFFF)
      
        bf_rx_mbist_result = self.eder.mems.mbist.rd('bf_rx_mbist_result')  # Check that this is all zeroes
        print (bf_rx_mbist_result)
        bf_tx_mbist_result = self.eder.mems.mbist.rd('bf_tx_mbist_result')  # Check that this is all zeroes
        print (bf_tx_mbist_result)
        result = result and (bf_rx_mbist_result == 0) and (bf_tx_mbist_result == 0)

        self.eder.reset()
        if result == True:
            print ('MBIST             [OK]')
            return True
        print ('MBIST RX:0x{0:04X} TX:0x{1:04X} [FAIL]'.format(bf_rx_mbist_result, bf_tx_mbist_result))
        return False



    # Internal AGC test

    def agc_test(self):
        import time

        self.eder.fpga_clk(1)

        self.eder.regs.wr('agc_en', 0x15)
        self.eder.regs.wr('agc_timeout', 200)
        self.eder.regs.wr('agc_use_agc_ctrls', 0x3F)
        self.eder.regs.wr('agc_detector_mask', 0x1F1F)
        self.eder.regs.wr('agc_bf_rf_gain_lvl', 0x55443322)
        self.eder.regs.wr('agc_bb_gain_1db_lvl', 0x654321)

        #self.eder.regs.wr('gpio_agc_done_ctrl', 0x02)

        self.eder.evkplatform.drv.setagcrst(1)
        time.sleep(0.01)
        self.eder.evkplatform.drv.setagcrst(0)

        self.eder.evkplatform.drv.setagcstart(1)
        time.sleep(0.01)
        self.eder.evkplatform.drv.setagcstart(0)

        agc_status = self.eder.evkplatform.drv.getagcstate()
        while (agc_status & 0x80) == 0:
            agc_status = self.eder.evkplatform.drv.getagcstate()
        
        print (hex(self.eder.evkplatform.drv.getagcstate()))




    # ADC Measurement tests

    def dco_beam_sweep(self, file_name='test_log.csv', num_samples=16, meas_type='bb'):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            #writer.writerow([meas_type, "", "", "", ""])
            writer.writerow([meas_type])
            writer.writerow(["Beam", " Temp."," V_i_diff[ADC]"," V_i_diff[V]", " V_q_diff[ADC]", " V_q_diff[V]", " V_i_com[ADC]", " V_i_com[V]", " V_q_com[ADC]", " V_q_com[V]"])
            dco_log.close()
        
        rx_bb_i_vga_1_2 = self.eder.regs.rd('rx_bb_i_vga_1_2')
        rx_bb_q_vga_1_2 = self.eder.regs.rd('rx_bb_q_vga_1_2')

        self.eder.regs.wr('rx_bb_i_vga_1_2', 0xf1)
        self.eder.regs.wr('rx_bb_q_vga_1_2', 0xf1)
        self.eder.rx.dco.run()

        #self.eder.regs.wr('rx_bb_i_vga_1_2', rx_bb_i_vga_1_2)
        #self.eder.regs.wr('rx_bb_q_vga_1_2', rx_bb_q_vga_1_2)

        self.eder.regs.wr('rx_bb_i_vga_1_2', 0xf3)
        self.eder.regs.wr('rx_bb_q_vga_1_2', 0xf3)

        for beam in range(0,64):
            self.eder.rx.set_beam(beam)
            time.sleep(0.1)
            self.dco_log(file_name, beam, num_samples, meas_type)

    def dco_beam_sweep_b(self, file_name='dco_beam_sweep_b.csv', numsamples=16):
        import time

        self.eder.regs.wr('trx_rx_on', 0x1fffff)
        time.sleep(5)
        self.eder.rx.drv_dco.run()
        self.eder.rx.dco.run()
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(["Beam", "Temp [deg. C]", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]"])
            dco_log.close()

            for beam in range(0,64):
                self.eder.rx.set_beam(beam)
                with open(file_name, 'ab') as dco_log:
                    writer = self.eder.csv.writer(dco_log)
                    time.sleep(0.1)
                    diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                    writer.writerow([beam, self.eder.temp.run()-273, diff['idiff'], diff['qdiff'], self._AdcToVolt(diff['idiff'])/(-2.845), self._AdcToVolt(diff['qdiff'])/(-2.845)])

            dco_log.close()

    def dco_beam_gain_sweep(self, file_name='test_log.csv', numsamples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(["BB1", "BB2", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]"])
            dco_log.close()

            bb1_gain_vector = [0xFF, 0xFF, 0xFF, 0xFF, 0x77, 0x33, 0x11]
            bb2_gain_vector = [0xFF, 0x77, 0x33, 0x11, 0x11, 0x11, 0x11]
            beam_vector = [0, 14, 28, 32, 36, 50, 63]

            for beam_index in range(0,7):
                self.eder.rx.set_beam(beam_vector[beam_index])
                with open(file_name, 'ab') as dco_log:
                    writer = self.eder.csv.writer(dco_log)
                    writer.writerow(['beam', beam_vector[beam_index]])
                    for bb_gain_index in range(0,7):  
                        self.eder.regs.wr('rx_gain_ctrl_bb1', bb1_gain_vector[bb_gain_index])
                        self.eder.regs.wr('rx_gain_ctrl_bb2', bb2_gain_vector[bb_gain_index])
                        time.sleep(0.1)
                        trx_rx_on = self.eder.regs.rd('trx_rx_on')
                        self.eder.regs.wr('trx_rx_on', 0x1F0000)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                        self.eder.regs.wr('trx_rx_on', trx_rx_on)
                        writer.writerow([bb1_gain_vector[bb_gain_index], bb2_gain_vector[bb_gain_index], diff['idiff'], diff['qdiff'], self._AdcToVolt(diff['idiff']), self._AdcToVolt(diff['qdiff'])])

            dco_log.close()
            self.eder.reset()
			
    def dco_beam_gain_sweep_0002(self, file_name='test_log.csv', numsamples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(["BB1", "BB2", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]"])
            dco_log.close()

            bb1_gain_vector = [0xFF, 0xFF, 0xFF, 0xFF, 0x77, 0x33, 0x11]
            bb2_gain_vector = [0xFF, 0x77, 0x33, 0x11, 0x11, 0x11, 0x11]
            beam_vector = [0, 14, 28, 32, 36, 50, 63]

            for beam_index in range(0,7):
                self.eder.rx.set_beam(beam_vector[beam_index])
                with open(file_name, 'ab') as dco_log:
                    writer = self.eder.csv.writer(dco_log)
                    writer.writerow(['beam', beam_vector[beam_index]])
                    for bb_gain_index in range(0,1):  
                        self.eder.regs.wr('rx_gain_ctrl_bb1', bb1_gain_vector[bb_gain_index])
                        self.eder.regs.wr('rx_gain_ctrl_bb2', bb2_gain_vector[bb_gain_index])
                        time.sleep(0.1)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                        writer.writerow([bb1_gain_vector[bb_gain_index], bb2_gain_vector[bb_gain_index], diff['idiff'], diff['qdiff'], self._AdcToVolt(diff['idiff']), self._AdcToVolt(diff['qdiff'])])

            dco_log.close()
            self.eder.reset()



    def dco_gain_sweep(self, file_name='test_log.csv', numsamples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(["BB1", "BB2", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]"])
            dco_log.close()

            bb1_gain_vector = [0xFF, 0xFF, 0xFF, 0xFF, 0x77, 0x33, 0x11]
            bb2_gain_vector = [0xFF, 0x77, 0x33, 0x11, 0x11, 0x11, 0x11]

            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                for bb_gain_index in range(0,7):  
                    self.eder.regs.wr('rx_gain_ctrl_bb1', bb1_gain_vector[bb_gain_index])
                    self.eder.regs.wr('rx_gain_ctrl_bb2', bb2_gain_vector[bb_gain_index])
                    time.sleep(0.1)
                    diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                    writer.writerow([bb1_gain_vector[bb_gain_index], bb2_gain_vector[bb_gain_index], diff['idiff'], diff['qdiff'], self._AdcToVolt(diff['idiff']), self._AdcToVolt(diff['qdiff'])])

            dco_log.close()
            self.eder.reset()
			
    def dco_gain_sweep_002(self, file_name='dco_gain_sweep_002.csv', numsamples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)

            bfrf_gain = 0xff
            bb1_gain = 0x11
            bb2_gain = 0x11
            bb3_gain = 0xff
            self.eder.regs.wr('rx_gain_ctrl_bfrf', bfrf_gain)
            self.eder.regs.wr('rx_gain_ctrl_bb1', bb1_gain)
            self.eder.regs.wr('rx_gain_ctrl_bb2', bb2_gain)
			
            self.eder.rx.dco.run()

            rx_bb_i_dco = self.eder.regs.rd('rx_bb_i_dco')
            rx_bb_q_dco = self.eder.regs.rd('rx_bb_q_dco')

            writer.writerow(['rx_bb_i_dco', hex(rx_bb_i_dco)])
            writer.writerow(['rx_bb_q_dco', hex(rx_bb_q_dco)])
            writer.writerow(["BB3", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]"])

            for bb3_gain in range(0xf,-1,-1):  
                self.eder.regs.wr('rx_gain_ctrl_bb3', (bb3_gain<<4)|bb3_gain)
                time.sleep(0.1)
                diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                writer.writerow([(bb3_gain<<4)|bb3_gain, diff['idiff'], diff['qdiff'], self._AdcToVolt(diff['idiff'])/(-2.845), self._AdcToVolt(diff['qdiff'])/(-2.845)])

            dco_log.close()
            #self.eder.reset()

    agc_gain_table = [[0xf, 0xf, 0xf, 0xf, 0xf],[0xf, 0xf, 0xf, 0xf, 0xe],[0xf, 0xf, 0xf, 0xf, 0xd],[0xf, 0xf, 0xf, 0xf, 0xc],[0xf, 0xf, 0xf, 0xf, 0xb],[0xf, 0xf, 0xf, 0xf, 0xa],[0xf, 0xf, 0xf, 0xf, 0x9],[0xf, 0xf, 0xf, 0xf, 0x8],[0xf, 0xf, 0xf, 0xf, 0x7],[0xf, 0xf, 0xf, 0xf, 0x6],
                      [0xf, 0xf, 0xf, 0xf, 0x5],[0xf, 0xf, 0xf, 0xf, 0x4],[0xf, 0xf, 0xf, 0xf, 0x3],[0xf, 0xf, 0xf, 0xf, 0x2],[0xf, 0xf, 0xf, 0xf, 0x1],[0xf, 0xf, 0xf, 0xf, 0x0],[0xf, 0xf, 0xf, 0x7, 0xf],[0xf, 0xf, 0xf, 0x7, 0xe],[0xf, 0xf, 0xf, 0x7, 0xd],[0xf, 0xf, 0xf, 0x7, 0xc],
                      [0xf, 0xf, 0xf, 0x7, 0xb],[0xf, 0xf, 0xf, 0x7, 0xa],[0xf, 0xf, 0xf, 0x7, 0x9],[0xf, 0xf, 0xf, 0x7, 0x8],[0xf, 0xf, 0xf, 0x7, 0x7],[0xf, 0xf, 0xf, 0x7, 0x6],[0xf, 0xf, 0xf, 0x7, 0x5],[0xf, 0xf, 0xf, 0x7, 0x4],[0xf, 0xf, 0xf, 0x7, 0x3],[0xf, 0xf, 0xf, 0x7, 0x2],
                      [0xf, 0xf, 0xf, 0x7, 0x1],[0xf, 0xf, 0xf, 0x7, 0x0],[0xf, 0xf, 0xf, 0x3, 0xf],[0xf, 0xf, 0xf, 0x3, 0xe],[0xf, 0xf, 0xf, 0x3, 0xd],[0xf, 0xf, 0xf, 0x3, 0xc],[0xf, 0xf, 0xf, 0x3, 0xb],[0xf, 0xf, 0xf, 0x3, 0xa],[0xf, 0xf, 0xf, 0x3, 0x9],[0xf, 0xf, 0xf, 0x3, 0x8],
                      [0xf, 0xf, 0xf, 0x3, 0x7],[0xf, 0xf, 0xf, 0x3, 0x6],[0xf, 0xf, 0xf, 0x3, 0x5],[0xf, 0xf, 0xf, 0x3, 0x4],[0xf, 0xf, 0xf, 0x3, 0x3],[0xf, 0xf, 0xf, 0x3, 0x2],[0xf, 0xf, 0xf, 0x3, 0x1],[0xf, 0xf, 0xf, 0x3, 0x0],[0xf, 0xf, 0xf, 0x1, 0xf],[0xf, 0xf, 0xf, 0x1, 0xe],
                      [0xf, 0xf, 0xf, 0x1, 0xd],[0xf, 0xf, 0xf, 0x1, 0xc],[0xf, 0xf, 0xf, 0x1, 0xb],[0xf, 0xf, 0xf, 0x1, 0xa],[0xf, 0xf, 0xf, 0x1, 0x9],[0xf, 0xf, 0xf, 0x1, 0x8],[0xf, 0xf, 0xf, 0x1, 0x7],[0xf, 0xf, 0xf, 0x1, 0x6],[0xf, 0xf, 0xf, 0x1, 0x5],[0xf, 0xf, 0xf, 0x1, 0x4],
                      [0xf, 0xf, 0xf, 0x1, 0x3],[0xf, 0xf, 0xf, 0x1, 0x2],[0xf, 0xf, 0xf, 0x1, 0x1],[0xf, 0xf, 0xf, 0x1, 0x0],[0xf, 0xf, 0x7, 0x1, 0xf],[0xf, 0xf, 0x7, 0x1, 0xe],[0xf, 0xf, 0x7, 0x1, 0xd],[0xf, 0xf, 0x7, 0x1, 0xc],[0xf, 0xf, 0x7, 0x1, 0xb],[0xf, 0xf, 0x7, 0x1, 0xa],
                      [0xf, 0xf, 0x7, 0x1, 0x9],[0xf, 0xf, 0x7, 0x1, 0x8],[0xf, 0xf, 0x7, 0x1, 0x7],[0xf, 0xf, 0x7, 0x1, 0x6],[0xf, 0xf, 0x7, 0x1, 0x5],[0xf, 0xf, 0x7, 0x1, 0x4],[0xf, 0xf, 0x7, 0x1, 0x3],[0xf, 0xf, 0x7, 0x1, 0x2],[0xf, 0xf, 0x7, 0x1, 0x1],[0xf, 0xf, 0x7, 0x1, 0x0],
                      [0xf, 0xf, 0x3, 0x1, 0xf],[0xf, 0xf, 0x3, 0x1, 0xe],[0xf, 0xf, 0x3, 0x1, 0xd],[0xf, 0xf, 0x3, 0x1, 0xc],[0xf, 0xf, 0x3, 0x1, 0xb],[0xf, 0xf, 0x3, 0x1, 0xa],[0xf, 0xf, 0x3, 0x1, 0x9],[0xf, 0xf, 0x3, 0x1, 0x8],[0xf, 0xf, 0x3, 0x1, 0x7],[0xf, 0xf, 0x3, 0x1, 0x6],
                      [0xf, 0xf, 0x3, 0x1, 0x5],[0xf, 0xf, 0x3, 0x1, 0x4],[0xf, 0xf, 0x3, 0x1, 0x3],[0xf, 0xf, 0x3, 0x1, 0x2],[0xf, 0xf, 0x3, 0x1, 0x1],[0xf, 0xf, 0x3, 0x1, 0x0],[0xf, 0xf, 0x1, 0x1, 0xf],[0xf, 0xf, 0x1, 0x1, 0xe],[0xf, 0xf, 0x1, 0x1, 0xd],[0xf, 0xf, 0x1, 0x1, 0xc],
                      [0xf, 0xf, 0x1, 0x1, 0xb],[0xf, 0xf, 0x1, 0x1, 0xa],[0xf, 0xf, 0x1, 0x1, 0x9],[0xf, 0xf, 0x1, 0x1, 0x8],[0xf, 0xf, 0x1, 0x1, 0x7],[0xf, 0xf, 0x1, 0x1, 0x6],[0xf, 0xf, 0x1, 0x1, 0x5],[0xf, 0xf, 0x1, 0x1, 0x4],[0xf, 0xf, 0x1, 0x1, 0x3],[0xf, 0xf, 0x1, 0x1, 0x2],
                      [0xf, 0xf, 0x1, 0x1, 0x1],[0xf, 0xf, 0x1, 0x1, 0x0],[0xf, 0xe, 0x1, 0x1, 0x1],[0xf, 0xe, 0x1, 0x1, 0x0],[0xf, 0xd, 0x1, 0x1, 0x1],[0xf, 0xd, 0x1, 0x1, 0x0],[0xf, 0xc, 0x1, 0x1, 0x1],[0xf, 0xc, 0x1, 0x1, 0x0],[0xf, 0xb, 0x1, 0x1, 0x1],[0xf, 0xb, 0x1, 0x1, 0x0],
                      [0xf, 0xa, 0x1, 0x1, 0x1],[0xf, 0xa, 0x1, 0x1, 0x0],[0xf, 0x9, 0x1, 0x1, 0x1],[0xf, 0x9, 0x1, 0x1, 0x0],[0xf, 0x8, 0x1, 0x1, 0x1],[0xf, 0x8, 0x1, 0x1, 0x0],[0xf, 0x7, 0x1, 0x1, 0x1],[0xf, 0x7, 0x1, 0x1, 0x0],[0xf, 0x6, 0x1, 0x1, 0x1],[0xf, 0x6, 0x1, 0x1, 0x0],
                      [0xf, 0x5, 0x1, 0x1, 0x1],[0xf, 0x5, 0x1, 0x1, 0x0],[0xf, 0x4, 0x1, 0x1, 0x1],[0xf, 0x4, 0x1, 0x1, 0x0],[0xf, 0x3, 0x1, 0x1, 0x1],[0xf, 0x3, 0x1, 0x1, 0x0],[0xf, 0x2, 0x1, 0x1, 0x1],[0xf, 0x2, 0x1, 0x1, 0x0],[0xf, 0x1, 0x1, 0x1, 0x1],[0xf, 0x1, 0x1, 0x1, 0x0],
                      [0xf, 0x0, 0x1, 0x1, 0x1],[0xf, 0x0, 0x1, 0x1, 0x0],[0xe, 0x0, 0x1, 0x1, 0x1],[0xe, 0x0, 0x1, 0x1, 0x0],[0xd, 0x0, 0x1, 0x1, 0x1],[0xd, 0x0, 0x1, 0x1, 0x0],[0xc, 0x0, 0x1, 0x1, 0x1],[0xc, 0x0, 0x1, 0x1, 0x0],[0xb, 0x0, 0x1, 0x1, 0x1],[0xb, 0x0, 0x1, 0x1, 0x0],
                      [0xa, 0x0, 0x1, 0x1, 0x1],[0xa, 0x0, 0x1, 0x1, 0x0],[0x9, 0x0, 0x1, 0x1, 0x1],[0x9, 0x0, 0x1, 0x1, 0x0],[0x8, 0x0, 0x1, 0x1, 0x1],[0x8, 0x0, 0x1, 0x1, 0x0],[0x7, 0x0, 0x1, 0x1, 0x1],[0x7, 0x0, 0x1, 0x1, 0x0],[0x6, 0x0, 0x1, 0x1, 0x1],[0x6, 0x0, 0x1, 0x1, 0x0],
                      [0x5, 0x0, 0x1, 0x1, 0x1],[0x5, 0x0, 0x1, 0x1, 0x0],[0x4, 0x0, 0x1, 0x1, 0x1],[0x4, 0x0, 0x1, 0x1, 0x0],[0x3, 0x0, 0x1, 0x1, 0x1],[0x3, 0x0, 0x1, 0x1, 0x0],[0x2, 0x0, 0x1, 0x1, 0x1],[0x2, 0x0, 0x1, 0x1, 0x0],[0x1, 0x0, 0x1, 0x1, 0x1],[0x1, 0x0, 0x1, 0x1, 0x0],
                      [0x0, 0x0, 0x1, 0x1, 0x1],[0x0, 0x0, 0x1, 0x1, 0x0],[0x0, 0x0, 0x0, 0x1, 0xf],[0x0, 0x0, 0x0, 0x1, 0xe],[0x0, 0x0, 0x0, 0x1, 0xd],[0x0, 0x0, 0x0, 0x1, 0xc],[0x0, 0x0, 0x0, 0x1, 0xb],[0x0, 0x0, 0x0, 0x1, 0xa],[0x0, 0x0, 0x0, 0x1, 0x9],[0x0, 0x0, 0x0, 0x1, 0x8],
                      [0x0, 0x0, 0x0, 0x1, 0x7],[0x0, 0x0, 0x0, 0x1, 0x6],[0x0, 0x0, 0x0, 0x1, 0x5],[0x0, 0x0, 0x0, 0x1, 0x4],[0x0, 0x0, 0x0, 0x1, 0x3],[0x0, 0x0, 0x0, 0x1, 0x2],[0x0, 0x0, 0x0, 0x1, 0x1],[0x0, 0x0, 0x0, 0x1, 0x0],[0x0, 0x0, 0x0, 0x0, 0xf],[0x0, 0x0, 0x0, 0x0, 0xe],
                      [0x0, 0x0, 0x0, 0x0, 0xd],[0x0, 0x0, 0x0, 0x0, 0xc],[0x0, 0x0, 0x0, 0x0, 0xb],[0x0, 0x0, 0x0, 0x0, 0xa],[0x0, 0x0, 0x0, 0x0, 0x9],[0x0, 0x0, 0x0, 0x0, 0x8],[0x0, 0x0, 0x0, 0x0, 0x7],[0x0, 0x0, 0x0, 0x0, 0x6],[0x0, 0x0, 0x0, 0x0, 0x5],[0x0, 0x0, 0x0, 0x0, 0x4],
                      [0x0, 0x0, 0x0, 0x0, 0x3],[0x0, 0x0, 0x0, 0x0, 0x2],[0x0, 0x0, 0x0, 0x0, 0x1],[0x0, 0x0, 0x0, 0x0, 0x0],[0x0, 0x0, 0x0, 0x0, 0x0],[0x0, 0x0, 0x0, 0x0, 0x0]]
    agc_table = [0,0,2,2,5,5,8,8,10,10,13,13,16,16,18,18,21,21,24,24,26,26,29,29,32,32,34,34,37,37,40,40,42,42,45,45,48,48,50,50,53,53,56,56,58,58,61,61,64,64,66,66,69,69,
                 72,72,74,74,77,77,80,80,82,82,85,85,88,88,90,90,93,93,96,96,98,98,101,101,104,104,106,106,109,109,112,112,114,114,117,117,120,120,122,122,125,125,128,128,130,
                 130,133,133,136,136,138,138,141,141,144,144,146,146,149,149,152,152,154,154,157,157,160,160,162,162,165,165,168,168,170,170,173,173,176,176,178,178,181,181,
                 184,184,186,186,189,189,192,192,194,194,197,197,200,200,202,202,203,203]
					  
    def dco_agc_gain_sweep(self, file_name='dco_agc_gain_sweep.csv', numsamples=16):
        import time

        #beam_vector = [0, 63, 31, 15]
        beam_vector = [63]

        for beam in beam_vector:
		
            calib_gain_index = 58
            self.eder.regs.wr('rx_gain_ctrl_bfrf', self.agc_gain_table[calib_gain_index][0]<<4|self.agc_gain_table[calib_gain_index][1])				
            self.eder.regs.wr('rx_gain_ctrl_bb1', self.agc_gain_table[calib_gain_index][2]<<4|self.agc_gain_table[calib_gain_index][2])
            self.eder.regs.wr('rx_gain_ctrl_bb2', self.agc_gain_table[calib_gain_index][3]<<4|self.agc_gain_table[calib_gain_index][3])
            self.eder.regs.wr('rx_gain_ctrl_bb3', self.agc_gain_table[calib_gain_index][4]<<4|self.agc_gain_table[calib_gain_index][4])

            self.eder.rx.dco.run(calib_beam=beam)
		
            #x = raw_input('Press ENTER to continue')
		
            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                writer.writerow(["Beam "+str(beam)])
                writer.writerow(["Gain index", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]", "BF", "RF", "BB1", "BB2", "BB3"])
                dco_log.close()

                with open(file_name, 'ab') as dco_log:
                    writer = self.eder.csv.writer(dco_log)
                    for gain_index in range(0, len(self.agc_gain_table)):
                        self.eder.regs.wr('rx_gain_ctrl_bfrf', self.agc_gain_table[gain_index][0]<<4|self.agc_gain_table[gain_index][1])				
                        self.eder.regs.wr('rx_gain_ctrl_bb1', self.agc_gain_table[gain_index][2]<<4|self.agc_gain_table[gain_index][2])
                        self.eder.regs.wr('rx_gain_ctrl_bb2', self.agc_gain_table[gain_index][3]<<4|self.agc_gain_table[gain_index][3])
                        self.eder.regs.wr('rx_gain_ctrl_bb3', self.agc_gain_table[gain_index][4]<<4|self.agc_gain_table[gain_index][4])
                        time.sleep(0.1)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                        writer.writerow([gain_index, diff['idiff'], diff['qdiff'], self.eder.rx.dco._decToVolt(diff['idiff'])/(-2.845), self.eder.rx.dco._decToVolt(diff['qdiff'])/(-2.845), self.agc_gain_table[gain_index][0], self.agc_gain_table[gain_index][1], self.agc_gain_table[gain_index][2], self.agc_gain_table[gain_index][3], self.agc_gain_table[gain_index][4]])

                dco_log.close()
        self.eder.reset()
		
    def dco_agc_gain_sweep_0002(self, file_name='dco_agc_gain_sweep_0002.csv', numsamples=16):
        import time

        #beam_vector = [0, 63]
        beam_vector = [63]

        for beam in beam_vector:
		
            calib_gain_index = 44
            self.eder.regs.wr('rx_gain_ctrl_bfrf', (self.agc_gain_table[self.agc_table[calib_gain_index]][0]<<4)|self.agc_gain_table[self.agc_table[calib_gain_index]][1])				
            self.eder.regs.wr('rx_gain_ctrl_bb1', (self.agc_gain_table[self.agc_table[calib_gain_index]][2]<<4)|self.agc_gain_table[self.agc_table[calib_gain_index]][2])
            self.eder.regs.wr('rx_gain_ctrl_bb2', (self.agc_gain_table[self.agc_table[calib_gain_index]][3]<<4)|self.agc_gain_table[self.agc_table[calib_gain_index]][3])
            self.eder.regs.wr('rx_gain_ctrl_bb3', (self.agc_gain_table[self.agc_table[calib_gain_index]][4]<<4)|self.agc_gain_table[self.agc_table[calib_gain_index]][4])

            self.eder.rx.dco.run(calib_beam=beam)
			
            #self.eder.regs.wr('rx_dco_en', 0)
            #self.eder.regs.wr('rx_bb_i_dco', 0x40)
            #self.eder.regs.wr('rx_bb_q_dco', 0x40)

            #x = raw_input('Press ENTER to continue')
		
            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                writer.writerow(["Beam "+str(beam)])
                rx_bb_i_dco = self.eder.regs.rd('rx_bb_i_dco')
                rx_bb_q_dco = self.eder.regs.rd('rx_bb_q_dco')
                writer.writerow(['rx_bb_i_dco', rx_bb_i_dco])
                writer.writerow(['rx_bb_q_dco', rx_bb_q_dco])
                gain_index_offset = 0
                writer.writerow(['gain_index_offset', gain_index_offset])
                writer.writerow(["Gain index", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]", "BF", "RF", "BB1", "BB2", "BB3"])
                dco_log.close()

                with open(file_name, 'ab') as dco_log:
                    writer = self.eder.csv.writer(dco_log)
                    for gain_index in range(0, len(self.agc_table)):
                        self.eder.regs.wr('rx_gain_ctrl_bfrf', (self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][0]<<4)|self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][1])			
                        self.eder.regs.wr('rx_gain_ctrl_bb1', (self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][2]<<4)|self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][2])
                        self.eder.regs.wr('rx_gain_ctrl_bb2', (self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][3]<<4)|self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][3])
                        self.eder.regs.wr('rx_gain_ctrl_bb3', (self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][4]<<4)|self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][4])
                        time.sleep(0.1)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                        writer.writerow([gain_index, diff['idiff'], 
                                        diff['qdiff'], 
                                        self.eder.rx.dco._decToVolt(diff['idiff'])/(-2.845), 
                                        self.eder.rx.dco._decToVolt(diff['qdiff'])/(-2.845), 
                                        self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][0], 
                                        self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][1], 
                                        self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][2], 
                                        self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][3], 
                                        self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][4]])

                dco_log.close()
        self.eder.reset()

    def mf_dco_agc_gain_sweep_0002(self, file_name='mf_dco_agc_gain_sweep_0002.csv', numsamples=16):
        import time

        calib_gain_index = 42
        self.eder.regs.wr('rx_gain_ctrl_bfrf', (self.agc_gain_table[self.agc_table[calib_gain_index]][0]<<4)|self.agc_gain_table[self.agc_table[calib_gain_index]][1])
        self.eder.regs.wr('rx_gain_ctrl_bb1', (self.agc_gain_table[self.agc_table[calib_gain_index]][2]<<4)|self.agc_gain_table[self.agc_table[calib_gain_index]][2])
        self.eder.regs.wr('rx_gain_ctrl_bb2', (self.agc_gain_table[self.agc_table[calib_gain_index]][3]<<4)|self.agc_gain_table[self.agc_table[calib_gain_index]][3])
        self.eder.regs.wr('rx_gain_ctrl_bb3', (self.agc_gain_table[self.agc_table[calib_gain_index]][4]<<4)|self.agc_gain_table[self.agc_table[calib_gain_index]][4])

        self.eder.rx.drv_dco.run()
        print ('Temperature before calibration: ' + str(self.eder.temp.run()-273))
        self.eder.rx.dco.run()
        print ('Temperature after calibration: ' + str(self.eder.temp.run()-273))
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            rx_bb_i_dco = self.eder.regs.rd('rx_bb_i_dco')
            rx_bb_q_dco = self.eder.regs.rd('rx_bb_q_dco')
            writer.writerow(['rx_bb_i_dco', rx_bb_i_dco])
            writer.writerow(['rx_bb_q_dco', rx_bb_q_dco])
            gain_index_offset = 0
            writer.writerow(['gain_index_offset', gain_index_offset])
            writer.writerow(["Gain index", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]", "BF", "RF", "BB1", "BB2", "BB3", "Temp."])
            dco_log.close()

            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                for gain_index in range(0, len(self.agc_table)):
                    self.eder.regs.wr('rx_gain_ctrl_bfrf', (self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][0]<<4)|self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][1])
                    self.eder.regs.wr('rx_gain_ctrl_bb1', (self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][2]<<4)|self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][2])
                    self.eder.regs.wr('rx_gain_ctrl_bb2', (self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][3]<<4)|self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][3])
                    self.eder.regs.wr('rx_gain_ctrl_bb3', (self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][4]<<4)|self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][4])
                    time.sleep(0.1)
                    diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                    writer.writerow([gain_index, diff['idiff'],
                                    diff['qdiff'],
                                    self.eder.rx.dco._decToVolt(diff['idiff'])/(-2.845),
                                    self.eder.rx.dco._decToVolt(diff['qdiff'])/(-2.845),
                                    self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][0],
                                    self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][1],
                                    self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][2],
                                    self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][3],
                                    self.agc_gain_table[self.agc_table[gain_index]+gain_index_offset][4],
                                    self.eder.temp.run()-273])

            dco_log.close()
        self.eder.reset()
		
    def dco_bb3_sweep_0003(self, file_name='dco_bb3_sweep_0003.csv', numsamples=16):
        import time

        beam_vector = [63]

        for beam in beam_vector:
		
            #calib_gain_index = 44
            #self.eder.regs.wr('rx_gain_ctrl_bfrf', self.agc_gain_table[self.agc_table[calib_gain_index]][0]<<4|self.agc_gain_table[self.agc_table[calib_gain_index]][1])
            #self.eder.regs.wr('rx_gain_ctrl_bb1', self.agc_gain_table[self.agc_table[calib_gain_index]][2]<<4|self.agc_gain_table[self.agc_table[calib_gain_index]][2])
            #self.eder.regs.wr('rx_gain_ctrl_bb2', self.agc_gain_table[self.agc_table[calib_gain_index]][3]<<4|self.agc_gain_table[self.agc_table[calib_gain_index]][3])
            #self.eder.regs.wr('rx_gain_ctrl_bb3', self.agc_gain_table[self.agc_table[calib_gain_index]][4]<<4|self.agc_gain_table[self.agc_table[calib_gain_index]][4])
			
            self.eder.regs.wr('rx_gain_ctrl_bfrf', 0xff)
            self.eder.regs.wr('rx_gain_ctrl_bb1', 0x11)
            self.eder.regs.wr('rx_gain_ctrl_bb2', 0x11)
            self.eder.regs.wr('rx_gain_ctrl_bb3', 0x00)

            self.eder.rx.dco.run(calib_beam=beam)

            #x = raw_input('Press ENTER to continue')
		
            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                writer.writerow(["Beam "+str(beam)])
                rx_gain_ctrl_bfrf = self.eder.regs.rd('rx_gain_ctrl_bfrf')
                rx_gain_ctrl_bb1 = self.eder.regs.rd('rx_gain_ctrl_bb1')
                rx_gain_ctrl_bb2 = self.eder.regs.rd('rx_gain_ctrl_bb2')
                rx_gain_ctrl_bb3 = self.eder.regs.rd('rx_gain_ctrl_bb3')
                writer.writerow(['rx_gain_ctrl_bfrf', rx_gain_ctrl_bfrf])
                writer.writerow(['rx_gain_ctrl_bb1', rx_gain_ctrl_bb1])
                writer.writerow(['rx_gain_ctrl_bb2', rx_gain_ctrl_bb2])
                writer.writerow(['rx_gain_ctrl_bb3', rx_gain_ctrl_bb3])
                rx_bb_i_dco = self.eder.regs.rd('rx_bb_i_dco')
                rx_bb_q_dco = self.eder.regs.rd('rx_bb_q_dco')
                writer.writerow(['rx_bb_i_dco', rx_bb_i_dco])
                writer.writerow(['rx_bb_q_dco', rx_bb_q_dco])
                writer.writerow(["BB3", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]"])
                dco_log.close()

                with open(file_name, 'ab') as dco_log:
                    writer = self.eder.csv.writer(dco_log)
                    for gain in range(0, 0x10):
                        self.eder.regs.wr('rx_gain_ctrl_bb3', gain<<4|gain)
                        time.sleep(0.1)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                        writer.writerow([gain<<4|gain,
                                        diff['idiff'],
                                        diff['qdiff'],
                                        self.eder.rx.dco._decToVolt(diff['idiff'])/(-2.845),
                                        self.eder.rx.dco._decToVolt(diff['qdiff'])/(-2.845),
                                        ])

                dco_log.close()
        self.eder.reset()
		
    def dco_bb2_sweep_0003(self, file_name='dco_bb2_sweep_0003.csv', numsamples=16):
        import time

        beam_vector = [63]

        for beam in beam_vector:
		
            #calib_gain_index = 44
            #self.eder.regs.wr('rx_gain_ctrl_bfrf', self.agc_gain_table[self.agc_table[calib_gain_index]][0]<<4|self.agc_gain_table[self.agc_table[calib_gain_index]][1])				
            #self.eder.regs.wr('rx_gain_ctrl_bb1', self.agc_gain_table[self.agc_table[calib_gain_index]][2]<<4|self.agc_gain_table[self.agc_table[calib_gain_index]][2])
            #self.eder.regs.wr('rx_gain_ctrl_bb2', self.agc_gain_table[self.agc_table[calib_gain_index]][3]<<4|self.agc_gain_table[self.agc_table[calib_gain_index]][3])
            #self.eder.regs.wr('rx_gain_ctrl_bb3', self.agc_gain_table[self.agc_table[calib_gain_index]][4]<<4|self.agc_gain_table[self.agc_table[calib_gain_index]][4])
			
            self.eder.regs.wr('rx_gain_ctrl_bfrf', 0x00)
            self.eder.regs.wr('rx_gain_ctrl_bb1', 0x11)
            self.eder.regs.wr('rx_gain_ctrl_bb2', 0x11)
            self.eder.regs.wr('rx_gain_ctrl_bb3', 0x00)

            self.eder.rx.dco.run(calib_beam=beam)

            #x = raw_input('Press ENTER to continue')
		
            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                writer.writerow(["Beam "+str(beam)])
                rx_gain_ctrl_bfrf = self.eder.regs.rd('rx_gain_ctrl_bfrf')
                rx_gain_ctrl_bb1 = self.eder.regs.rd('rx_gain_ctrl_bb1')
                rx_gain_ctrl_bb2 = self.eder.regs.rd('rx_gain_ctrl_bb2')
                rx_gain_ctrl_bb3 = self.eder.regs.rd('rx_gain_ctrl_bb3')
                writer.writerow(['rx_gain_ctrl_bfrf', rx_gain_ctrl_bfrf])
                writer.writerow(['rx_gain_ctrl_bb1', rx_gain_ctrl_bb1])
                writer.writerow(['rx_gain_ctrl_bb2', rx_gain_ctrl_bb2])
                writer.writerow(['rx_gain_ctrl_bb3', rx_gain_ctrl_bb3])
                rx_bb_i_dco = self.eder.regs.rd('rx_bb_i_dco')
                rx_bb_q_dco = self.eder.regs.rd('rx_bb_q_dco')
                writer.writerow(['rx_bb_i_dco', rx_bb_i_dco])
                writer.writerow(['rx_bb_q_dco', rx_bb_q_dco])
                writer.writerow(["BB2", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]"])
                dco_log.close()

                with open(file_name, 'ab') as dco_log:
                    writer = self.eder.csv.writer(dco_log)
                    bb2_range = [0x1, 0x3, 0x7, 0xf]
                    for gain in bb2_range:
                        self.eder.regs.wr('rx_gain_ctrl_bb2', gain<<4|gain)
                        time.sleep(0.1)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                        writer.writerow([gain<<4|gain, 
                                        diff['idiff'],
                                        diff['qdiff'],
                                        self.eder.rx.dco._decToVolt(diff['idiff'])/(-2.845),
                                        self.eder.rx.dco._decToVolt(diff['qdiff'])/(-2.845),
                                        ])

                dco_log.close()
        self.eder.reset()
		
    def dco_bb1_sweep_0003(self, file_name='dco_bb1_sweep_0003.csv', numsamples=16):
        import time

        beam_vector = [63]

        for beam in beam_vector:
		
            #calib_gain_index = 44
            #self.eder.regs.wr('rx_gain_ctrl_bfrf', self.agc_gain_table[self.agc_table[calib_gain_index]][0]<<4|self.agc_gain_table[self.agc_table[calib_gain_index]][1])				
            #self.eder.regs.wr('rx_gain_ctrl_bb1', self.agc_gain_table[self.agc_table[calib_gain_index]][2]<<4|self.agc_gain_table[self.agc_table[calib_gain_index]][2])
            #self.eder.regs.wr('rx_gain_ctrl_bb2', self.agc_gain_table[self.agc_table[calib_gain_index]][3]<<4|self.agc_gain_table[self.agc_table[calib_gain_index]][3])
            #self.eder.regs.wr('rx_gain_ctrl_bb3', self.agc_gain_table[self.agc_table[calib_gain_index]][4]<<4|self.agc_gain_table[self.agc_table[calib_gain_index]][4])
			
            self.eder.regs.wr('rx_gain_ctrl_bfrf', 0x00)
            self.eder.regs.wr('rx_gain_ctrl_bb1', 0x11)
            self.eder.regs.wr('rx_gain_ctrl_bb2', 0x11)
            self.eder.regs.wr('rx_gain_ctrl_bb3', 0x00)

            self.eder.rx.dco.run(calib_beam=beam)

            #x = raw_input('Press ENTER to continue')
		
            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                writer.writerow(["Beam "+str(beam)])
                rx_gain_ctrl_bfrf = self.eder.regs.rd('rx_gain_ctrl_bfrf')
                rx_gain_ctrl_bb1 = self.eder.regs.rd('rx_gain_ctrl_bb1')
                rx_gain_ctrl_bb2 = self.eder.regs.rd('rx_gain_ctrl_bb2')
                rx_gain_ctrl_bb3 = self.eder.regs.rd('rx_gain_ctrl_bb3')
                writer.writerow(['rx_gain_ctrl_bfrf', rx_gain_ctrl_bfrf])
                writer.writerow(['rx_gain_ctrl_bb1', rx_gain_ctrl_bb1])
                writer.writerow(['rx_gain_ctrl_bb2', rx_gain_ctrl_bb2])
                writer.writerow(['rx_gain_ctrl_bb3', rx_gain_ctrl_bb3])
                rx_bb_i_dco = self.eder.regs.rd('rx_bb_i_dco')
                rx_bb_q_dco = self.eder.regs.rd('rx_bb_q_dco')
                writer.writerow(['rx_bb_i_dco', rx_bb_i_dco])
                writer.writerow(['rx_bb_q_dco', rx_bb_q_dco])
                writer.writerow(["BB1", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]"])
                dco_log.close()

                with open(file_name, 'ab') as dco_log:
                    writer = self.eder.csv.writer(dco_log)
                    bb1_range = [0x1, 0x3, 0x7, 0xf]
                    for gain in bb1_range:
                        self.eder.regs.wr('rx_gain_ctrl_bb1', gain<<4|gain)
                        time.sleep(0.1)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                        writer.writerow([gain<<4|gain,
                                        diff['idiff'],
                                        diff['qdiff'],
                                        self.eder.rx.dco._decToVolt(diff['idiff'])/(-2.845),
                                        self.eder.rx.dco._decToVolt(diff['qdiff'])/(-2.845),
                                        ])

                dco_log.close()
        self.eder.reset()
		


    def dco_gain_sweep_calib(self, file_name='test_log.csv', numsamples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(["BB1", "BB2", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]", "rx_bb_i_dco", "rx_bb_q_dco"])
            dco_log.close()

            bb1_gain_vector = [0xFF, 0xFF, 0xFF, 0xFF, 0x77, 0x33, 0x11]
            bb2_gain_vector = [0xFF, 0x77, 0x33, 0x11, 0x11, 0x11, 0x11]

            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                for bb_gain_index in range(0,7):  
                    self.eder.regs.wr('rx_gain_ctrl_bb1', bb1_gain_vector[bb_gain_index])
                    self.eder.regs.wr('rx_gain_ctrl_bb2', bb2_gain_vector[bb_gain_index])
                    rx_bb_i_dco, rx_bb_q_dco = self.eder.rx.dco.run()
                    time.sleep(0.5)
                    diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                    writer.writerow([bb1_gain_vector[bb_gain_index], bb2_gain_vector[bb_gain_index], diff['idiff'], diff['qdiff'], self._AdcToVolt(diff['idiff']), self._AdcToVolt(diff['qdiff']), rx_bb_i_dco, rx_bb_q_dco])

            dco_log.close()
            self.eder.reset()

   
    def _AdcToVolt(self, number):
        return round(0.000886948*number,6)


    def dco_log(self, file_name, beam, num_samples, meas_type):
        measured_values = self.eder.rx.dco.iq_meas.meas(num_samples, meas_type)
        measured_values_v = dict()
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            temperature = round(self.eder.temp.run()-273, 1)
            measured_values_v['idiff'] = self.eder.rx.dco._decToVolt(measured_values['idiff'])
            measured_values_v['qdiff'] = self.eder.rx.dco._decToVolt(measured_values['qdiff'])
            measured_values_v['icm'] = self.eder.rx.dco._decToVolt(measured_values['icm'])
            measured_values_v['qcm'] = self.eder.rx.dco._decToVolt(measured_values['qcm'])
            writer.writerow([beam, temperature, measured_values['idiff'], measured_values_v['idiff'], measured_values['qdiff'], 
                             measured_values_v['qdiff'], measured_values['icm'], measured_values_v['icm'], measured_values['qcm'], measured_values_v['qcm']])
            dco_log.close()


    def dco_sweep(self, file_name='dco_sweep.csv', num_samples=16):
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(['Shift', 'Mult. factor', 'Offset', 'i_diff', 'q_diff'])
            
            for shift in range(0,3):
                if shift == 0:
                    log_shift = 'no'
                elif shift == 1:
                    log_shift = 'neg.'
                else:
                    log_shift = 'pos.'
                for mult_fact in range(0,4):
                    if mult_fact == 0:
                        log_mult_fact = 'x1'
                    elif mult_fact == 1:
                        log_mult_fact = 'x2'
                    elif mult_fact == 2:
                        log_mult_fact = 'x3'
                    else:
                        log_mult_fact = 'x4'
                    for dco_reg_value in range(0,0x80):
                        rx_bb_iq_dco = dco_reg_value + (shift << 8) + (mult_fact << 12)
                        #print (hex(rx_bb_iq_dco))
                        self.eder.regs.wr('rx_bb_i_dco', rx_bb_iq_dco)
                        self.eder.regs.wr('rx_bb_q_dco', rx_bb_iq_dco)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff(meas_cm='Yes')
                        writer.writerow([log_shift, log_mult_fact, dco_reg_value, diff['idiff'], diff['qdiff']])
        dco_log.close()

    def dco_sweep_002(self, file_name='dco_sweep_002.csv', num_samples=16):
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(['Shift', 'Mult. factor', 'Offset', 'i_diff', 'q_diff'])
            
            for shift in range(0,3):
                if shift == 0:
                    log_shift = 'no'
                elif shift == 1:
                    log_shift = 'neg.'
                else:
                    log_shift = 'pos.'
                for mult_fact in range(0,4):
                    if mult_fact == 0:
                        log_mult_fact = 'x1'
                    elif mult_fact == 1:
                        log_mult_fact = 'x2'
                    elif mult_fact == 2:
                        log_mult_fact = 'x3'
                    else:
                        log_mult_fact = 'x4'
                    for dco_reg_value in range(0,0x80):
                        rx_bb_iq_dco = dco_reg_value + (shift << 8) + (mult_fact << 12)
                        #print (hex(rx_bb_iq_dco))
                        self.eder.regs.wr('rx_bb_i_dco', rx_bb_iq_dco)
                        self.eder.regs.wr('rx_bb_q_dco', rx_bb_iq_dco)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff()
                        writer.writerow([log_shift, log_mult_fact, dco_reg_value, diff['idiff'], diff['qdiff']])
        dco_log.close()
		
    def dco_sweep_003(self, file_name='dco_sweep_003.csv', num_samples=16):
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(['Mult.[Bits 13:12]', 'Shift[Bits 9:8]', 'Offset[Bits 6:0]', 'i_diff', 'q_diff'])

            for mult_fact in range(0,4):
                for shift in range(0,3):
                    for dco_reg_value in range(0,0x80):
                        rx_bb_iq_dco = dco_reg_value + (shift << 8) + (mult_fact << 12)
                        self.eder.regs.wr('rx_bb_i_dco', rx_bb_iq_dco)
                        self.eder.regs.wr('rx_bb_q_dco', rx_bb_iq_dco)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff()
                        writer.writerow([mult_fact, shift, dco_reg_value, diff['idiff'], diff['qdiff']])
        dco_log.close()
        self.eder.reset()
		
    def dco_sweep_004(self, mult_fact=0, shift=0, file_name='dco_sweep_004.csv', num_samples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(['Gain index', 'Mult.[Bits 13:12]', 'Shift[Bits 9:8]', 'Offset[Bits 6:0]', 'i_diff', 'q_diff'])

            for gain_index in range(42, len(self.agc_gain_table)):
                self.eder.regs.wr('rx_gain_ctrl_bfrf', self.agc_gain_table[gain_index][0]<<4|self.agc_gain_table[gain_index][1])				
                self.eder.regs.wr('rx_gain_ctrl_bb1', self.agc_gain_table[gain_index][2]<<4|self.agc_gain_table[gain_index][2])
                self.eder.regs.wr('rx_gain_ctrl_bb2', self.agc_gain_table[gain_index][3]<<4|self.agc_gain_table[gain_index][3])
                self.eder.regs.wr('rx_gain_ctrl_bb3', self.agc_gain_table[gain_index][4]<<4|self.agc_gain_table[gain_index][4])
                time.sleep(0.1)

                for dco_reg_value in range(0,0x80):
                    rx_bb_iq_dco = dco_reg_value + (shift << 8) + (mult_fact << 12)
                    self.eder.regs.wr('rx_bb_i_dco', rx_bb_iq_dco)
                    self.eder.regs.wr('rx_bb_q_dco', rx_bb_iq_dco)
                    diff = self.eder.rx.dco.iq_meas.meas_vdiff()
                    writer.writerow([gain_index, mult_fact, shift, dco_reg_value, diff['idiff'], diff['qdiff']])
        dco_log.close()
        self.eder.reset()
		
    def dco_sweep_005(self, mult_fact=0, shift=0, file_name='dco_sweep_005.csv', num_samples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(['Gain index', 'Mult.[Bits 13:12]', 'Shift[Bits 9:8]', 'Offset[Bits 6:0]', 'i_diff', 'q_diff'])

            for gain_index in range(0, len(self.agc_table)):
                self.eder.regs.wr('rx_gain_ctrl_bfrf', self.agc_gain_table[self.agc_table[gain_index]][0]<<4|self.agc_gain_table[self.agc_table[gain_index]][1])				
                self.eder.regs.wr('rx_gain_ctrl_bb1', self.agc_gain_table[self.agc_table[gain_index]][2]<<4|self.agc_gain_table[self.agc_table[gain_index]][2])
                self.eder.regs.wr('rx_gain_ctrl_bb2', self.agc_gain_table[self.agc_table[gain_index]][3]<<4|self.agc_gain_table[self.agc_table[gain_index]][3])
                self.eder.regs.wr('rx_gain_ctrl_bb3', self.agc_gain_table[self.agc_table[gain_index]][4]<<4|self.agc_gain_table[self.agc_table[gain_index]][4])
                time.sleep(0.1)

                for dco_reg_value in range(0,0x80):
                    rx_bb_iq_dco = dco_reg_value + (shift << 8) + (mult_fact << 12)
                    self.eder.regs.wr('rx_bb_i_dco', rx_bb_iq_dco)
                    self.eder.regs.wr('rx_bb_q_dco', rx_bb_iq_dco)
                    diff = self.eder.rx.dco.iq_meas.meas_vdiff()
                    writer.writerow([gain_index, mult_fact, shift, dco_reg_value, diff['idiff'], diff['qdiff']])
        dco_log.close()
        self.eder.reset()

        
    def dco_beam_sweep_0001(self, file_name='dco_beam_sweep_0001.csv'):
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Beam', 'i_diff(V)_ffff', 'q_diff(V)_ffff', 'i_diff(V)_0000', 'q_diff(V)_0000'])
            for beam in range(0,64):
                self.eder.rx.set_beam(beam)
                self.eder.regs.wr('trx_rx_on', 0x1fffff)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                self.eder.regs.wr('trx_rx_on', 0x1f0000)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_0_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_0_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([beam, measured_values_v_1_idiff, measured_values_v_1_qdiff, measured_values_v_0_idiff, measured_values_v_0_qdiff])
        log_file.close()

    def dco_beam_sweep_0002(self, file_name='dco_beam_sweep_0002.csv'):
        import time
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Beam', 'i_diff(V)', 'q_diff(V)'])
            for beam in range(0,64):
                self.eder.rx.set_beam(beam)
                time.sleep(0.1)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([beam, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def dco_beam_sweep_0003(self, file_name='dco_beam_sweep_0003.csv'):
        import time
        self.eder.regs.wr('rx_gain_ctrl_bb1', 0x77)
        self.eder.regs.wr('rx_gain_ctrl_bb2', 0x33)
        self.eder.regs.wr('rx_gain_ctrl_bb3', 0xEE)
        self.eder.regs.wr('rx_gain_ctrl_bfrf', 0xEE)
        if self.eder.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            self.eder.rx.drv_dco.run()
        self.eder.rx.dco.run()
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Beam', 'i_diff(V)', 'q_diff(V)'])
            for beam in range(0,64):
                self.eder.rx.set_beam(beam)
                time.sleep(0.1)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([beam, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def dco_phase_sweep_0001(self, file_name='dco_phase_sweep_0001.csv'):
        import time
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Phase', 'i_diff(V)', 'q_diff(V)'])
            for phase in range(0,0x41):
                for ant in range(0,16):
                    self.eder.rx.bf.awv.wr(31, ant, (phase << 8) | phase)
                self.eder.rx.set_beam(31)
                time.sleep(1)
                #self.eder.regs.wr('trx_rx_on', 0x1fffff)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([phase, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def dco_single_phase_sweep_0001(self, ant, file_name='dco_single_phase_sweep_0001.csv'):
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Phase', 'i_diff(V)', 'q_diff(V)'])
            for phase in range(0,0x41):
                self.eder.rx.bf.awv.wr(31, ant, (phase << 8) | phase)
                self.eder.rx.set_beam(31)
                self.eder.regs.wr('trx_rx_on', 0x1fffff)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([phase, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def dco_single_ant_phase_sweep_0001(self, ant, file_name='dco_single_ant_phase_sweep_0001.csv'):
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Phase', 'i_diff(V)', 'q_diff(V)'])
            self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
            for phase in range(0,0x41):
                self.eder.rx.bf.awv.wr(31, ant, (phase << 8) | phase)
                self.eder.rx.set_beam(31)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([phase, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def dco_single_ant_phase_sweep_0002(self, ant, file_name='dco_single_ant_phase_sweep_0002.csv'):
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['I phase', 'Q phase', 'i_diff(V)', 'q_diff(V)'])
            self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
            self.eder.rx.bf.awv.wr(31, ant, 0x1f1f)
            self.eder.rx.dco.run()
            for i_phase in range(0,0x40):
                for q_phase in range(0,0x40):
                    self.eder.rx.bf.awv.wr(31, ant, (i_phase << 8) | q_phase)
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas()
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    writer.writerow([i_phase, q_phase, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def dco_single_ant_phase_sweep_0003(self, ant, file_name='dco_single_ant_phase_sweep_0003'):
        with open(file_name+'_ant_'+str(ant)+'.csv', 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
            self.eder.rx.bf.awv.wr(31, ant, 0x1f1f)
            self.eder.rx.dco.run()
            row_data_idiff = []
            row_data_qdiff = []
            col_header = ['', 'q_phase', '']
            for i in range(0, 0x40):
                col_header = col_header + [i]
            writer.writerow(col_header)
            for i_phase in range(0,0x40):
                row_data_idiff = ['i_phase'] + [i_phase] + ['Vidiff']
                row_data_qdiff = ['i_phase'] + [i_phase] + ['Vqdiff']
                for q_phase in range(0,0x40):
                    self.eder.rx.bf.awv.wr(31, ant, (i_phase << 8) | q_phase)
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas()
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]

                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_single_ant_phase_sweep_0004(self, ant, file_name='dco_single_ant_phase_sweep_0004'):
        with open(file_name+'_ant_'+str(ant)+'_I'+'.csv', 'ab') as log_file_i:
            with open(file_name+'_ant_'+str(ant)+'_Q'+'.csv', 'ab') as log_file_q:
                writer_i = self.eder.csv.writer(log_file_i)
                writer_q = self.eder.csv.writer(log_file_q)
                self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
                self.eder.rx.bf.awv.wr(31, ant, 0x3f3f)
                import time
                time.sleep(30)
                self.eder.rx.dco.run()
                row_data_idiff = []
                row_data_qdiff = []
                col_header = ['', 'q_phase', '']
                for i in range(0, 0x40):
                    col_header = col_header + [i]
                writer_i.writerow(col_header)
                writer_q.writerow(col_header)
                for i_phase in range(0,0x40):
                    row_data_idiff = ['i_phase'] + [i_phase] + ['Vidiff']
                    row_data_qdiff = ['i_phase'] + [i_phase] + ['Vqdiff']
                    for q_phase in range(0,0x40):
                        self.eder.rx.bf.awv.wr(31, ant, (i_phase << 8) | q_phase)
                        self.eder.rx.set_beam(31)
                        measured_values = self.eder.rx.dco.iq_meas.meas()
                        measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                        measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                        row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                        row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]

                    writer_i.writerow(row_data_idiff)
                    writer_q.writerow(row_data_qdiff)
        log_file_i.close()
        log_file_q.close()

    def i_q_circle(self, ampl=1, start_angle=0, i_offset=0, q_offset=0):
        import math
        i=[]
        q=[]
        for angle_deg in range(start_angle, start_angle+360,4):
            angle = angle_deg * math.pi / 180
            i = i + [round(ampl*math.cos(angle)+i_offset, 0)]
            q = q + [round(ampl*math.sin(angle)+q_offset, 0)]
        return i,q


    def dco_single_ant_phase_sweep_0005(self, ant, file_name='dco_single_ant_phase_sweep_0005'):
        with open(file_name+'_ant_'+str(ant)+'.csv', 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                #self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
                #self.eder.rx.bf.awv.wr(31, ant, 0x3f3f)
                import time
                time.sleep(30)
                self.eder.rx.dco.run()
                row_data_idiff = []
                row_data_qdiff = []
                header_0 = []
                header_1 = []
                i_coord, q_coord = self.i_q_circle(0.5)
                for index in range(0, len(q_coord)):
                    header_0 = header_0 + [int(i_coord[index]*31+31)]
                    header_1 = header_1 + [int(q_coord[index]*31+31)]
                writer.writerow(header_0)
                writer.writerow(header_1)
                writer.writerow([''])
                row_data_idiff = []
                row_data_qdiff = []
                for phase_index in range(0, len(i_coord)):
                    self.eder.rx.bf.awv.wr(31, ant, ( int((i_coord[phase_index]*31+31)) << 8) | int((q_coord[phase_index]*31+31)))
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]
                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_all_ant_phase_sweep_0006(self, start_angle=0, file_name='dco_all_ant_phase_sweep_0006'):
        with open(file_name+'.csv', 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                import time
                time.sleep(30)
                self.eder.rx.dco.run()
                row_data_idiff = []
                row_data_qdiff = []
                header_0 = []
                header_1 = []
                i_coord, q_coord = self.i_q_circle(1, start_angle)
                for index in range(0, len(q_coord)):
                    header_0 = header_0 + [int(i_coord[index]*31+31)]
                    header_1 = header_1 + [int(q_coord[index]*31+31)]
                writer.writerow(header_0)
                writer.writerow(header_1)
                writer.writerow([''])
                row_data_idiff = []
                row_data_qdiff = []
                for phase_index in range(0, len(i_coord)):
                    for ant in range(0,16):
                        self.eder.rx.bf.awv.wr(31, ant, ( int((i_coord[phase_index]*31+31)) << 8) | int((q_coord[phase_index]*31+31)))
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]
                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_all_ant_phase_sweep_0007(self, ant, start_angle=0, file_name='dco_all_ant_phase_sweep_0007'):
        with open(file_name+'.csv', 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                writer.writerow([''])
                writer.writerow([''])
                writer.writerow(['Element', ant])
                import time
                #self.set_phase(31, 0x1f, 0x1f)
                time.sleep(30)
                self.eder.rx.dco.run()
                row_data_idiff = []
                row_data_qdiff = []
                header_0 = []
                header_1 = []
                i_coord, q_coord = self.i_q_circle(1, start_angle)
                for index in range(0, len(q_coord)):
                    header_0 = header_0 + [int(i_coord[index]*31+31)]
                    header_1 = header_1 + [int(q_coord[index]*31+31)]
                writer.writerow(header_0)
                writer.writerow(header_1)
                writer.writerow([''])
                row_data_idiff = []
                row_data_qdiff = []
                for phase_index in range(0, len(i_coord)):
                    self.eder.rx.bf.awv.wr(31, ant, ( int((i_coord[phase_index]*31+31)) << 8) | int((q_coord[phase_index]*31+31)))
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]
                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_one_ant_phase_sweep_0008(self, ant, start_angle=0, file_name='dco_one_ant_phase_sweep_0008'):
        with open(file_name+'.csv', 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                writer.writerow([''])
                writer.writerow([''])
                writer.writerow(['Element', ant])
                import time
                self.set_phase(31, 0x1f, 0x1f)
                time.sleep(30)
                self.eder.rx.dco.run()
                measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                initial_i_diff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                #initial_i_diff = measured_values['idiff']
                initial_q_diff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                #initial_q_diff = measured_values['qdiff']
                writer.writerow(['V i_diff', initial_i_diff])
                writer.writerow(['V q_diff', initial_q_diff])
                #writer.writerow(['ADC i_diff', initial_i_diff])
                #writer.writerow(['ADC q_diff', initial_q_diff])
                #self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
                row_data_idiff = []
                row_data_qdiff = []
                header_0 = []
                header_1 = []
                i_coord, q_coord = self.i_q_circle(1, start_angle)
                for index in range(0, len(q_coord)):
                    header_0 = header_0 + [int(i_coord[index]*31+31)]
                    header_1 = header_1 + [int(q_coord[index]*31+31)]
                writer.writerow(header_0)
                writer.writerow(header_1)
                writer.writerow([''])
                row_data_idiff = []
                row_data_qdiff = []
                for phase_index in range(0, len(i_coord)):
                #for phase_index in range(0, 100):
                    self.eder.rx.bf.awv.wr(31, ant, ( int((i_coord[phase_index]*31+31)) << 8) | int((q_coord[phase_index]*31+31)))
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845) - initial_i_diff
                    #measured_values_v_1_idiff = measured_values['idiff']
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845) - initial_q_diff
                    #measured_values_v_1_qdiff = measured_values['qdiff']
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]
                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_one_ant_phase_sweep_0009(self, ant, start_angle=0, file_name='dco_one_ant_phase_sweep_0009'):
        with open(file_name+'.csv', 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                writer.writerow([''])
                writer.writerow([''])
                writer.writerow(['Element', ant])
                import time
                self.set_phase(31, 0x1f, 0x1f)
                time.sleep(30)
                self.eder.rx.dco.run()
                measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                initial_i_diff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                initial_q_diff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow(['V i_diff', initial_i_diff])
                writer.writerow(['V q_diff', initial_q_diff])
                #self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
                row_data_idiff = []
                row_data_qdiff = []
                header_0 = []
                header_1 = []
                i_coord, q_coord = self.i_q_circle(1, start_angle)
                for index in range(0, len(q_coord)):
                    header_0 = header_0 + [int(i_coord[index]*31+31)]
                    header_1 = header_1 + [int(q_coord[index]*31+31)]
                writer.writerow(header_0)
                writer.writerow(header_1)
                writer.writerow([''])
                row_data_idiff = []
                row_data_qdiff = []
                for phase_index in range(0, len(i_coord)):
                    self.eder.rx.bf.awv.wr(31, ant, ( int((i_coord[phase_index]*31+31)) << 8) | int((q_coord[phase_index]*31+31)))
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845) - initial_i_diff
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845) - initial_q_diff
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]
                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_one_ant_phase_sweep_0010(self, ant, start_angle=0, file_name='dco_one_ant_phase_sweep_0010'):
        with open(file_name+'.csv', 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                writer.writerow([''])
                writer.writerow([''])
                writer.writerow(['Element', ant])
                import time
                self.set_phase(31, 0x1f, 0x1f)
                time.sleep(30)
                self.eder.rx.dco.run()
                for count in range(0,6):
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    #initial_i_diff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    initial_i_diff = measured_values['idiff']
                    #initial_q_diff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    initial_q_diff = measured_values['qdiff']
                    #writer.writerow(['V i_diff', initial_i_diff])
                    #writer.writerow(['V q_diff', initial_q_diff])
                    writer.writerow(['ADC i_diff', initial_i_diff])
                    writer.writerow(['ADC q_diff', initial_q_diff])
                #self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
                row_data_idiff = []
                row_data_qdiff = []
                header_0 = []
                header_1 = []
                i_coord, q_coord = self.i_q_circle(1, start_angle)
                for index in range(0, len(q_coord)):
                    header_0 = header_0 + [int(i_coord[index]*31+31)]
                    header_1 = header_1 + [int(q_coord[index]*31+31)]
                writer.writerow(header_0)
                writer.writerow(header_1)
                writer.writerow([''])
                row_data_idiff = []
                row_data_qdiff = []
                #for phase_index in range(0, len(i_coord)):
                for phase_index in range(0, 100):
                    #self.eder.rx.bf.awv.wr(31, ant, ( int((i_coord[phase_index]*31+31)) << 8) | int((q_coord[phase_index]*31+31)))
                    #self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    #measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845) - initial_i_diff
                    measured_values_v_1_idiff = measured_values['idiff']
                    #measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845) - initial_q_diff
                    measured_values_v_1_qdiff = measured_values['qdiff']
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]
                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_double_phase_sweep_0001(self, ant, file_name='dco_single_phase_sweep_0001.csv'):
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Phase', 'i_diff(V)', 'q_diff(V)'])
            for phase in range(0,0x41):
                self.eder.rx.bf.awv.wr(31, ant, (phase << 8) | phase)
                self.eder.rx.set_beam(31)
                self.eder.regs.wr('trx_rx_on', 0x1fffff)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([phase, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def set_phase(self, index, i_phase, q_phase, txrx='rx'):
        for ant in range(0,16):
            if txrx == 'rx':
                self.eder.rx.bf.awv.wr(index, ant, (i_phase << 8) | q_phase)
                self.eder.rx.set_beam(index)
            else:
                self.eder.tx.bf.awv.wr(index, ant, (i_phase << 8) | q_phase)
                self.eder.tx.set_beam(index)

    def read_adc_volt(self, src, num_samples=16):
        self.eder.adc.start(0x80|src, None, self.math.log(num_samples, 2))
        adc_val = self.eder.adc.mean()
        self.eder.adc.stop()
        return self.eder.rx.dco._decToVolt(adc_val)

    def dco_step_meas(self, file_name='dco_step_meas.csv'):
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['mult', 'shift', 'rx_bb_dco_i/q', 'i_diff(V)', 'q_diff(V)'])
            import time
            for mult in range(0,4):
                for shift in range(0,3):
                    for rx_bb_dco in range(0, 0x80):
                        self.eder.regs.wr('rx_bb_i_dco', (mult<<12)|(shift<<8)|rx_bb_dco)
                        self.eder.regs.wr('rx_bb_q_dco', (mult<<12)|(shift<<8)|rx_bb_dco)
                        time.sleep(0.001)
                        measured_values = self.eder.rx.dco.iq_meas.meas()
                        measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                        measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                        writer.writerow([mult, shift, rx_bb_dco, measured_values_v_1_idiff, measured_values_v_1_qdiff])

    def pdet_gain_meas(self, element=8):
        for gain in range(0, 0x10):
            self.eder.regs.wr('tx_bfrf_gain', (gain<<4)+gain)
            self.eder.tx_pdet_offset_meas()
            print (self.eder.pdet_bias['TX'+str(element)])

    def pdet_element_sweep(self, bfrf_gain=0xff):
        self.eder.regs.wr('tx_bfrf_gain', bfrf_gain)
        for element in range(0,16):
            self.eder.regs.wr('trx_tx_on', 0x1f0000+(1<<element))
            self.eder.tx_pdet_offset_meas()
            print (self.eder.pdet_bias['TX'+str(element)])


    def temp_offset_meas(self):
        chip_temp = self.eder.temp.run()-273
        print (chip_temp)
        pcb_temp = self.eder.evkplatform.get_pcb_temp()
        print (pcb_temp)
        print ('offset: ' + str())

    def alc_pdet_temp_meas(self, freq=60.48e9, file_name='alc_pdet_temp_meas'):
        import time
        chip_temp = self.eder.temp.run()-273
        pcb_temp = self.eder.evkplatform.get_pcb_temp()

        print ('-- ROOM TEMPERATURE --')
        print ('Turn OFF baseband signal and press <ENTER> to read power detector offset values')
        key = raw_input()
        self.eder.run_tx(freq)
        self.eder.regs.wr('trx_tx_on', 0x1fffff)
        self.eder.regs.wr('tx_bfrf_gain', 0xee)
        self.eder.tx.dco.run()
        #self.eder.regs.wr('tx_bb_i_dco', 0x23)
        #self.eder.regs.wr('tx_bb_q_dco', 0x1e)

        self.eder.tx_pdet_offset_meas()
        print ('Turn ON baseband signal and press <ENTER> to start measurements')
        key = raw_input()

        import visa
        #rm = visa.ResourceManager('C:\\Program Files (x86)\\IVI Foundation\\VISA\\WinNT\\agvisa\\agbin\\visa32.dll')
        rm = visa.ResourceManager()
        sa = rm.open_resource('TCPIP0::10.1.0.200::inst0::INSTR')
        sa.timeout = 10000
        sa.write('*IDN?')
        print (sa.read())
        sa.write('CALC:MARK2:X {}'.format(freq))
        with open(file_name+'.csv', 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Freq.', freq])
            writer.writerow(['Chip temp.', chip_temp])
            writer.writerow(['PCB temp.', pcb_temp])
            writer.writerow(['PDET offset.', self.eder.pdet_bias['TX00'], self.eder.pdet_bias['TX01'], self.eder.pdet_bias['TX02'], self.eder.pdet_bias['TX03'], self.eder.pdet_bias['TX04'], self.eder.pdet_bias['TX05'], self.eder.pdet_bias['TX06'], 
                              self.eder.pdet_bias['TX07'], self.eder.pdet_bias['TX08'], self.eder.pdet_bias['TX09'], self.eder.pdet_bias['TX10'], self.eder.pdet_bias['TX11'], self.eder.pdet_bias['TX12'], self.eder.pdet_bias['TX13'], self.eder.pdet_bias['TX14'], self.eder.pdet_bias['TX15']])
            writer.writerow([''])
            writer.writerow(['chip temp.', 'pcb temp.', '00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', 'power'])
            while True:
                pcb_temp = self.eder.evkplatform.get_pcb_temp()
                chip_temp = self.eder.temp.run()-273
                power = self.eder.tx_pdet(print_res=False, absolut_value=True)
                sa.write('CALC:MARK2:Y?')
                spec_pow = sa.read()
                writer.writerow([chip_temp, pcb_temp, power['TX00'], power['TX01'], power['TX02'], power['TX03'], power['TX04'], power['TX05'], power['TX06'], power['TX07'], power['TX08'], power['TX09'], power['TX10'], power['TX11'], power['TX12'], power['TX13'], power['TX14'], power['TX15'], spec_pow])
                time.sleep(5)

    def alc_pdet_offset_temp_meas(self, freq=60.48e9, file_name='alc_pdet_offset_temp_meas'):
        import time

        print ('Turn OFF baseband signal and press <ENTER> to read power detector offset values')
        key = raw_input()
        self.eder.run_tx(freq)
        self.eder.regs.wr('trx_tx_on', 0x1fffff)
        self.eder.regs.wr('tx_bfrf_gain', 0xee)
        self.set_phase(31,0,0,'tx')
        chip_temp = self.eder.temp.run()-273
        pcb_temp = self.eder.evkplatform.get_pcb_temp()
        calibration_temp = chip_temp + 20.0
        self.eder.tx.dco.run()
        with open(file_name+'.csv', 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Freq.', freq])
            writer.writerow(['Chip temp.', chip_temp])
            writer.writerow(['PCB temp.', pcb_temp])
            writer.writerow([''])
            writer.writerow(['chip temp.', 'pcb temp.', 'TX00', 'TX01', 'TX02', 'TX03', 'TX04', 'TX05', 'TX06', 'TX07', 'TX08', 'TX09', 'TX10', 'TX11', 'TX12', 'TX13', 'TX14', 'TX15'])
            while True:
                pcb_temp = self.eder.evkplatform.get_pcb_temp()
                chip_temp = self.eder.temp.run()-273
                if chip_temp > calibration_temp:
                    self.eder.tx.dco.run()
                    calibration_temp = chip_temp + 20.0
                self.eder.tx_pdet_offset_meas()
                pdet_offset = self.eder.pdet_bias 
                writer.writerow([chip_temp, pcb_temp, pdet_offset['TX0'], pdet_offset['TX1'], pdet_offset['TX2'], pdet_offset['TX3'], pdet_offset['TX4'], pdet_offset['TX5'], pdet_offset['TX6'], pdet_offset['TX7'], pdet_offset['TX8'], pdet_offset['TX9'], pdet_offset['TX10'], pdet_offset['TX11'], pdet_offset['TX12'], pdet_offset['TX13'], pdet_offset['TX14'], pdet_offset['TX15']])
                time.sleep(5)


    def alc_meas_001(self):
        self.eder.run_tx()
        self.eder.regs.wr('tx_bfrf_gain', 0xdd)
        self.eder.regs.wr('tx_bb_gain', 0x01)
        self.eder.regs.wr('trx_tx_on', 0x1fffff)
        self.eder.regs.wr('tx_bb_iq_gain', 0xff)
        x = raw_input('Turn off signal and press Enter to continue')
        self.eder.tx.dco.run()
        self.eder.tx.alc.init()
        self.eder.tx.alc.start()
        for ampl in range(350, 90, -10):
            print ('Set signal amplitude to {} mV'.format(ampl))
            x = raw_input('Press Enter to continue')
            x = raw_input('Power meter: ')
            print (str(x) + 'dBm')
            print (float(x)-19.6-(-74.09460775)-(-1))
            self.eder.temp.run()-273
            self.eder.tx.alc.pdet_dump()

    def alc_meas_002(self, channel=2, file_name_prefix='alc_meas_002'):
        import visa
        import time
        import datetime
		
        freqs = [58.32e9, 60.48e9, 62.64e9, 64.80e9, 66.96e9, 69.12e9]
        rm = visa.ResourceManager()
        spec = rm.open_resource('GPIB1::18::INSTR')
        spec.timeout = 10000
        self.eder.run_tx(freqs[channel-1])
        spec.write('CF '+str(freqs[channel-1])+'Hz')
        time.sleep(2)
        self.eder.tx.dco.run()

        self.eder.logger.log_info('TX enabled and LO leakage calibrated')
        self.eder.logger.log_info('Start signal generator')
        raw_input('Press any key to continue')
		
        spec.write('CF '+str(freqs[channel-1]-500e6)+'Hz')
        spec.write('SP 50e6Hz')
        # Peak search
        spec.write('MKPK')
        # MK -> CF
        spec.write('MKCF')

        with open(file_name_prefix+'_chan_'+str(channel)+'.csv', 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            #sa.write('*IDN?')
            #print (sa.read())
            #sa.write('CALC:MARK2:X {}'.format(60.48e9))

            self.eder.tx.alc.init()
            self.eder.tx.alc.pdet_src_set(8)
            self.eder.tx.alc.gain_mode_set(self.eder.tx.alc.TX_INACTIVE_ADJUST)
            low_th = self.eder.tx.alc.pdet_th_lo_trim(8, 1000, True)
            self.eder.logger.log_info('low_th: ' + str(low_th))
            writer.writerow(['Low threshold', low_th])
            self.eder.regs.clr('trx_ctrl', 3)
            self.eder.regs.set('trx_ctrl', 8)
            self.eder.tx.alc.start()
            counter = 0
            temp = self.eder.temp.run()-273
            writer.writerow(['Time', 'Temperature[deg. C]', 'Power[dBm]', 'tx_alc_bfrf_gain'])
            while True:
                time_stamp = datetime.datetime.now().time()
                self.eder.logger.log_info(time_stamp)
                time.sleep(1)
                self.eder.evkplatform.drv.settxrxsw(1)
                self.eder.logger.log_info('TX On')
                new_temp = self.eder.temp.run()-273
                self.eder.logger.log_info('Temp. ' + str(new_temp) + ' deg. C')
                self.eder.tx.alc.status()
                tx_alc_bfrf_gain = self.eder.regs.rd('tx_alc_bfrf_gain')
                time.sleep(1)
                spec.write("MKPK")
                #Read marker ampl.
                spec.write("MKA?")
                power = spec.read()
                writer.writerow([time_stamp, new_temp, power, tx_alc_bfrf_gain])
                #if (new_temp - temp > 4):
                #    low_th = low_th 
                #sa.write('CALC:MARK2:Y?')
                #spec_pow = sa.read()
                #print (spec_pow)
                #print ('')
                time.sleep(0.1)
                self.eder.evkplatform.drv.settxrxsw(0)
                self.eder.logger.log_info('TX Off')


    def test_lo_calib(self, num_of_tries=10):
        num_of_failures = 0
        freqs = [58.32e9, 60.48e9, 62.64e9, 64.80e9, 66.96e9, 69.12e9]
        for i in range(0, num_of_tries):
            for freq in freqs:
                print ('Temperature: ' + str(self.eder.temp.run()-273) + ' deg. C')
                self.eder.run_tx(freq)
                if self.eder.tx.dco.run() == False:
                    num_of_failures = num_of_failures + 1
                    print ('Calibration Failure')
                    print ('    Temperature: ' + str(self.eder.temp.run()-273) + ' deg. C')
                    print ('    Freq: ' + str(freq) + ' Hz')
        print ('Number of failures: ' + str(num_of_failures) + ' of ' + str(num_of_tries*6))

    def set_gain_index(self, gain_index):
        self.eder.regs.wr('rx_gain_ctrl_bfrf', self.agc_gain_table[gain_index][0]<<4|self.agc_gain_table[gain_index][1])
        self.eder.regs.wr('rx_gain_ctrl_bb1', self.agc_gain_table[gain_index][2]<<4|self.agc_gain_table[gain_index][2])
        self.eder.regs.wr('rx_gain_ctrl_bb2', self.agc_gain_table[gain_index][3]<<4|self.agc_gain_table[gain_index][3])
        self.eder.regs.wr('rx_gain_ctrl_bb3', self.agc_gain_table[gain_index][4]<<4|self.agc_gain_table[gain_index][4])

    def test_dco_screening(self):
        import time

        self.eder.run_rx()
        self.eder.regs.wr('trx_rx_on', 0x1fffff)
        self.set_gain_index(40)
        time.sleep(1)
        if self.eder.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            self.eder.rx.drv_dco.run()
        self.eder.rx.dco.run()
        self.eder.regs.dump('rx')
        diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=16)
        print(round(1000 * self.eder.test._AdcToVolt(diff['idiff'])/(-2.845)))
        print(round(1000 * self.eder.test._AdcToVolt(diff['qdiff'])/(-2.845)))
        i_dco = []
        q_dco = []
        i_dco_beam = []
        q_dco_beam = []
        for beam in range(0,64):
            self.eder.rx.set_beam(beam)
            time.sleep(0.1)
            diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=16)
            i_dco.append(round(1000 * self.eder.test._AdcToVolt(diff['idiff'])/(-2.845)))
            q_dco.append(round(1000 * self.eder.test._AdcToVolt(diff['qdiff'])/(-2.845)))
            i_dco_beam.append(beam)
            q_dco_beam.append(beam)

        log_string = 'I RX DCO[mV] '+ ' '.join('{:3.0f}[{}]'.format(dco,dco_beam) for dco,dco_beam in zip(i_dco,i_dco_beam))
        print (log_string)

        log_string = 'Q RX DCO[mV] '+ ' '.join('{:3.0f}[{}]'.format(dco,dco_beam) for dco,dco_beam in zip(q_dco,q_dco_beam))
        print (log_string)

        self.eder.reset()

    def dco_beam_sweep_b_magn_phase(self, gain_index=None, file_name='dco_beam_sweep_b_magn_phase.xlsx', numsamples=16, freq=None, mag_max_y=None):
        from openpyxl import Workbook
        import time
        import math
        import numpy as np
        import matplotlib.pyplot as plt

        if gain_index != None:
            calib_gain_index = gain_index
            self.eder.regs.wr('rx_gain_ctrl_bfrf', self.agc_gain_table[calib_gain_index][0]<<4|self.agc_gain_table[calib_gain_index][1])
            self.eder.regs.wr('rx_gain_ctrl_bb1', self.agc_gain_table[calib_gain_index][2]<<4|self.agc_gain_table[calib_gain_index][2])
            self.eder.regs.wr('rx_gain_ctrl_bb2', self.agc_gain_table[calib_gain_index][3]<<4|self.agc_gain_table[calib_gain_index][3])
            self.eder.regs.wr('rx_gain_ctrl_bb3', self.agc_gain_table[calib_gain_index][4]<<4|self.agc_gain_table[calib_gain_index][4])
        else:
            self.eder.regs.wr('rx_gain_ctrl_bfrf', 0xff)
            self.eder.regs.wr('rx_gain_ctrl_bb1', 0xff)
            self.eder.regs.wr('rx_gain_ctrl_bb2', 0x33)
            self.eder.regs.wr('rx_gain_ctrl_bb3', 0x33)
            pass

        self.eder.regs.dump('rx')

        self.eder.regs.wr('trx_rx_on', 0x1fffff)
        time.sleep(10)
        if self.eder.regs.device_info.get_attrib('chip_type') == 'Eder B MMF':
            self.eder.rx.drv_dco.run()
        self.eder.rx.dco.run()

        wb = Workbook()
        ws = wb.active

        ws.append(["Beam", "Temp [deg. C]", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]", "Ampl.", "Phase[deg.]"])

        ampl = []
        phase = []

        for beam in range(0,64):
            self.eder.rx.set_beam(beam)
            time.sleep(0.1)
            diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
            row = [beam, self.eder.temp.run()-273, diff['idiff'], diff['qdiff'], (self._AdcToVolt(diff['idiff'])/(-2.845))/2, (self._AdcToVolt(diff['qdiff'])/(-2.845))/2]
            row.append(math.sqrt(row[4]*1000000*row[4]+row[5]*1000000*row[5]))
            row.append(180*math.atan2(row[4],row[5])/math.pi)
            ws.append(row)
            ampl.append(row[6])
            phase.append(row[7])

        wb.save(file_name)

        self.plot_ampl_phase(file_name, title='Freq. '+str(freq), mag_max_y=None, save_plot=True)

    def plot_ampl_phase(self, file_name, title=None, worksheet=None, mag_max_y=None, save_plot=False):
        from openpyxl import Workbook
        from openpyxl import load_workbook
        import math
        import numpy as np
        import matplotlib.pyplot as plt

        wb = load_workbook(filename = file_name)
        if worksheet == None:
            ws = wb.active
        else:
            ws = wb[worksheet]

        ampl = []
        for col in ws['G']:
            ampl.append(col.value)
        ampl = ampl[1:len(ampl)]

        phase = []
        for col in ws['H']:
            phase.append(col.value)
        phase = phase[1:len(phase)]

        fig, axs = plt.subplots(2, figsize=[18,12])
        if title != None:
            fig.suptitle(str(title))
        plt.setp(axs[0], xticks=range(0,64))
        plt.setp(axs[1], xticks=range(0,64))
        axs[0].plot(range(0,64), ampl, 'tab:orange')
        axs[0].set_title('Magnitude')
        if mag_max_y == None:
            axs[0].set(xlabel='Beam', ylabel='Magnitude [mV]')
        else:
            axs[0].set(xlabel='Beam', ylabel='Magnitude [mV]', ylim=(0, mag_max_y))
        axs[1].plot(range(0,64), phase, 'tab:red')
        axs[1].set_title('Phase [deg.]')
        axs[1].set(xlabel='Beam', ylabel='Phase [deg.]', ylim=(-180, 180))

        plt.show(block=False)
        plt.pause(1)
        plt.savefig(file_name.replace('.xlsx', '.png'),format='png')

    def dco_beam_chan_sweep(self, prefix=None, gain_index=42, mag_max_y=30):
        channels = [58.32e9, 60.48e9, 62.64e9, 64.80e9, 66.96e9, 69.12e9]
        if prefix==None:
            base_file_name = ''
        else:
            base_file_name = str(prefix)+'_'
        for freq in channels:
            self.eder.run_rx(freq)
            self.dco_beam_sweep_b_magn_phase(gain_index=gain_index, file_name='dco_meas_data\\'+base_file_name+str(freq)+ '.xlsx', freq=freq, mag_max_y=mag_max_y)
            #self.dco_beam_sweep_b_magn_phase(gain_index=0, file_name='dco_meas_data\\'+base_file_name+str(freq)+ '.xlsx', freq=freq, mag_max_y=None)


    def temp_accuracy_check(self):
        import time
        from openpyxl import Workbook
        from openpyxl import load_workbook
        import pyvisa
        rm = pyvisa.ResourceManager()
        mm = rm.open_resource('GPIB0::22::INSTR')

        file_name = 'temp_meas.xlsx'
        #wb = load_workbook('temp_meas.xlsx')
        wb = Workbook()
        ws = wb.active
        ws.append(["trx_tx_on", "Sensor[mV]", "PCB temp. [deg. C]", "Chip temp.[deg. C]"])

        self.eder.pll.init()
        self.eder.pll.set(60.48e9)
        self.eder.tx.setup(60.48e9, beam=31, trx_tx_on=0x1f0000)
        self.eder.regs.wr('trx_ctrl', 0x02)
        trx_tx_on=0x1f0000
        for i in range(0,16):
            print ('trx_tx_on: '+hex(trx_tx_on))
            for k in range(0,60):
                time.sleep(1)
                chip_temp = self.eder.temp.run('C')
                pcb_temp = -300
                while pcb_temp == -300:
                    pcb_temp = self.eder.eeprom.read_pcb_temp()
                mm.write('MEASure:VOLTage:DC?')
                try:
                    sensor_v = float(mm.read())*1000
                except:
                    sensor_v = 0
                print ('CHIP temperature: {:5.1f} Celcius'.format(chip_temp))
                print ('Sensor temperature: {:5.1f} Celcius'.format(sensor_v))
                ws.append([hex(trx_tx_on), sensor_v, pcb_temp, chip_temp])
                wb.save(file_name)
            trx_tx_on = trx_tx_on + (1 << i)
            self.eder.regs.wr('trx_tx_on', trx_tx_on)

    def txRxToggleLoop(self):
        # Toggle TRX
        #global alcTxRxAutoToggleOn_flag
        self.eder.evkplatform.drv.settxrxsw(0)
        self.time.sleep(0.2)
        self.eder.evkplatform.drv.settxrxsw(1)
        if self.alcTxRxAutoToggleOn_flag:
            self.timer = self.threading.Timer(0.2, self.txRxToggleLoop)
            self.timer.start()
            # print('txRxToggleLoop %d'% alcTxRxAutoToggleOn_flag)
        else:
            self.eder.evkplatform.drv.settxrxsw(1)
            # print('txRxToggleLoop %d' % alcTxRxAutoToggleOn_flag)

    def alcTxRxAutoToggle(self):
        # Fun to make the TRX toggle work
        #global alcTxRxAutoToggleOn_flag
        if not self.alcTxRxAutoToggleOn_flag:
            self.eder.regs.clr('trx_ctrl', 0x09)
            self.eder.regs.set('trx_ctrl', 0x02)
            # alcTxRxAutoToggleOn = False
            # eder.alcTxRxAutoToggleButton.configure(fg='black')
        else:
            self.eder.regs.clr('trx_ctrl', 0x03)
            self.eder.regs.set('trx_ctrl', 0x08)
            # alcTxRxAutoToggleOn = True
            # eder.alcTxRxAutoToggleButton.configure(fg='red')
            timer = self.threading.Timer(0.5, self.txRxToggleLoop)
            timer.start()

    def do_alc(self, alc_time_sec=30):
        """
        alc_time_sec = number seconds to do alc, default is 30 sec
        """
        # Start ALC
        #global alcTxRxAutoToggleOn_flag
        self.eder.tx.alc.enable()
        self.eder.tx.alc.init()
        self.eder.tx.alc.pdet_src_set(8)
        self.eder.tx.alc.start()

        self.alcTxRxAutoToggleOn_flag = alcTxRxAutoToggleOn = True
        self.alcTxRxAutoToggle()

        self.time.sleep(alc_time_sec)
        self.alcTxRxAutoToggleOn_flag = alcTxRxAutoToggleOn = False
        # alcTxRxAutoToggle()
        self.eder.evkplatform.drv.settxrxsw(1)
        # time.sleep(10)
        # eder.evkplatform.drv.settxrxsw(1)
        # eder.evkplatform.drv.settxrxsw(1)
        # print('After TRX Switching')
        # self.time.sleep(5)
        # eder.regs.dump('tx')