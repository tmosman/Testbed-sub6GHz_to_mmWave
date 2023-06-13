# -*- coding: utf-8 -*-
"""
Created on Thu Apr  7 21:48:14 2022

@author: tmosman
"""

#!/usr/bin/env python3
##################################################################
#   Author:         Tawfik Osman
#   Date:           21/7/2022
#   Description:    This file is meant to implement a class that
#                     handles the USRP radios 
##################################################################


from gnuradio import blocks
from gnuradio import gr 
from gnuradio import uhd


class USRP(gr.top_block):
    def __init__(self,usrp_id,center_freq,samp_rate,channels,gain):
        gr.top_block.__init__(self, "BS_RX")
        # Variables
        self.samp_rate = samp_rate
        self.center_freq = center_freq
        self.gain = gain
        self.channels = channels
        self.usrp_id = usrp_id

        # File Source Block
        self.save_file = f'{self.usrp_id}_measured_signals.dat'
        self.blocks_streams_to_vector = blocks.streams_to_vector(gr.sizeof_gr_complex, len(self.channels))
        self.blocks_file_sink = blocks.file_sink(gr.sizeof_gr_complex, self.save_file, False)
        self.blocks_file_sink.set_unbuffered(False)

        # Connections
        #self.connect((self.blocks_streams_to_vector, 0),(self.blocks_file_sink, 0))
        
        # USRP Blocks
        self.usrp_rx = None
        self.init_usrp(self.usrp_id)
    
    def init_usrp(self,device):
        try:
            self.usrp_rx = uhd.usrp_source(
                ",".join(("serial=" + device, "")),
                uhd.stream_args(
                    cpu_format="fc32",
                    otw_format="sc16",
                    channels=range(len(self.channels)),
                ),
            )
            for i in self.channels:
                self.usrp_rx.set_samp_rate(self.samp_rate)
                self.usrp_rx.set_center_freq(self.center_freq, i)
                self.usrp_rx.set_gain(self.gain, i)
                self.usrp_rx.set_antenna('TX/RX', i)
                self.usrp_rx.set_bandwidth(self.samp_rate, i)
                self.usrp_rx.set_auto_dc_offset(True, i)
                self.usrp_rx.set_auto_iq_balance(True, i)
                self.connect((self.usrp_rx, i), (self.blocks_streams_to_vector, i))
                self.connect((self.blocks_streams_to_vector, i),(self.blocks_file_sink, i))
        except RuntimeError:
            self.init_usrp(device)
    
    def open_file(self,save_file):
        self.save_file = save_file
        self.blocks_file_sink.open(save_file)
    
    def close_file(self):
        self.blocks_file_sink.close()
