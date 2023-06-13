from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio import analog
from gnuradio.filter import firdes
import numpy as np
import os

serial_usrp = 'serial=31E9F2E'


class usrp_tx(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "TX")

        # Variables
        self.samp_rate = 2e6
        self.center_freq = 1e9
        self.gain = 50
        self.pkt = np.fromfile(os.getcwd() + '/ofdm_packet.dat',dtype=np.complex64)


        # Blocks
        self.usrp_tx = uhd.usrp_sink(",".join((serial_usrp, "")),
                                    uhd.stream_args(
                                        cpu_format="fc32",
                                        channels=range(1),
                                    ),
                                    )
        
        self.usrp_tx.set_clock_source('internal', 0)  #changed from externalto internal for usrp 205mini
        self.usrp_tx.set_time_source('internal', 0)
        self.usrp_tx.set_samp_rate(self.samp_rate)
        self.usrp_tx.set_center_freq(self.center_freq, 0)
        self.usrp_tx.set_gain(self.gain, 0)
        self.usrp_tx.set_bandwidth(self.samp_rate, 0)

        self.blocks_vector_source = blocks.vector_source_c(self.pkt.tolist(),True,1,[])
        self.blocks_null_source = blocks.vector_source_c(self.pkt.tolist(),True,1,[])
     

        # Initial Connection
        self.connect((self.blocks_null_source, 0), (self.usrp_tx, 0))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.usrp_tx.set_samp_rate(self.samp_rate)
        self.usrp_tx.set_bandwidth(self.samp_rate, 0)


    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.usrp_tx.set_center_freq(center_freq, 0)


    def begin_transmit(self):
        print('Locking Gnu Radio')
        self.lock()
        print('Disconnecting Null Source')
        self.disconnect((self.blocks_null_source, 0), (self.usrp_tx, 0))
        print('Connecting Vector Source')
        self.connect((self.blocks_vector_source, 0), (self.usrp_tx, 0))
        print('Unlocking Gnu Radio')
        self.unlock()

    def end_transmit(self):
        self.lock()
        self.disconnect((self.blocks_vector_source, 0), (self.usrp_tx, 0))
        self.connect((self.blocks_null_source, 0), (self.usrp_tx, 0))
        self.unlock()
