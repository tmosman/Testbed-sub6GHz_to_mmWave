# -*- coding: utf-8 -*-
"""
Created on Tue Jun 13 11:58:28 2023

@author: tmosman
"""

import numpy as np
import  matplotlib.pyplot as plt
from channels_compute import Estimator
save_dir = r'E:/summer2023_sub6_system/Data_June_12th/capture1/'

estObj = Estimator(numberSubCarriers=64, numberOFDMSymbols=2, modOrder=16)
min_all = []
for k in range(10):
    usrp1_data = np.fromfile(f'{save_dir}usrp_0_{k}.dat',dtype=np.complex64)
    usrp1_data = usrp1_data.reshape(-1,2).transpose()
    win_size = int(1e6)
    num_win = usrp1_data.shape[1]//win_size
    for ch_idx in range(2):
        all_pkts = []
        for q in range(1,num_win):
            data = usrp1_data[ch_idx,q*win_size:(q*win_size)+win_size]
            #print(f'Range: {q*win_size}:{(q*win_size)+win_size}')
            lts_corr,numberofPackets,valid_peak_indices = estObj.detectPeaks(data.reshape(1,-1))
            all_pkts.append(numberofPackets)
        print(f'Min-Max Number of Packets in RF index {ch_idx} : {min(all_pkts)} <--> {max(all_pkts)}')
        min_all.append(min(all_pkts))
print(f'Minimun : {min(min_all)}')
       
'''
    for q in range(1,num_win):
        data = usrp1_data[1,q*win_size:(q*win_size)+win_size] 
        Hest,Hest_0 = estObj.Rx_processing_Hest(data.reshape(1,-1),0,min(all_pkts)-1)
        ph_diff = np.angle(Hest[0,1:])- np.angle(Hest_0[0,1:])
        ph_diff[26:38] = np.zeros((12,))
        plt.plot(ph_diff)
        
'''
