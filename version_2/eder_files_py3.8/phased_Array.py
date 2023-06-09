# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 09:11:31 2022

@author: osman
"""
# import sys
# sys.path.insert(1, r'./eder_files_py3.8')
from eder import Eder
#from usrp import USRP

class Array(Eder):
    def __init__(self,sn_id):
        Eder.__init__(self, unit_name=sn_id)
        
        #self.ue = Eder(unit_name='SNSP210110')
        
       
    def initialize_Array(self, freq):
        self.rx_setup(float(freq))
        self.rx_enable()
        return 1
        
        
    def start_Sweep(self):
        #self.ue.rx.set_beam(0)
        self.rx.bf.idx.set(0)
        #self.ue.rx.bf.dump()
        return 1
        
        
    def set_PA(self, freq):
        self.run_rx(float(freq))
        #self.ue.rx_enable()
        return 1
    def set_dir(self, direction):
        #self.ue.rx.set_beam(int(direction))
	#self.ue.rx.bf.idx.set(int(direction))
        self.rx.bf.idx.inc()
        #print(int(direction))
        return 1
    def disable(self):
        self.rx_disable()
        return 1