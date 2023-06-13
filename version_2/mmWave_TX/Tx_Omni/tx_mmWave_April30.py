#!/usr/bin/python2
###############################################################################
#   Author:
#   Date:
#   Description:
#############################################################################


import time
import sys
sys.path.insert(1,r'./eder_files_py3.8')  # call py module from specif
from eder import Eder
#import pdb0
import os
import subprocess
import shlex
import scipy.io as scs
from gnuradio_uhd import usrp_tx


def main(top_block_cls=usrp_tx, options=None):
    serial_phasedarr_0 = 'SNSP210109'
    
    print("start phased array TX")
    subprocess.call(shlex.split('sudo ./start_mb1_b.sh -u '+ serial_phasedarr_0))
    ue = Eder(unit_name= serial_phasedarr_0)
    ue.reset()
    ue.tx_setup(62.64e9)
    ue.tx_enable()
    ue.tx.set_beam(0)
    print("tx reg info:")
    ue.regs.dump('trx')

    # Begin transmission(USRP)
    tb = top_block_cls()
    tb.start()
    print(tb.pkt)
    tb.begin_transmit()
    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()

