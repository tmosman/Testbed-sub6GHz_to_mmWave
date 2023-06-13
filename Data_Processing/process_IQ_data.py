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

for k in range(1):
    usrp1_data = np.fromfile(f'{save_dir}usrp_0_{k}.dat',dtype=np.complex64)
    usrp1_data = usrp1_data.reshape(-1,2).transpose()
    win_size = 1000000
    num_win = usrp1_data.shape[1]//win_size
    init = 0
    all_pkts = []
    for q in range(1,num_win):
        data = usrp1_data[1,q*win_size:(q*win_size)+win_size]
        print(f'Range: {q*win_size}:{(q*win_size)+win_size}')
        lts_corr,numberofPackets,valid_peak_indices = estObj.detectPeaks(data.reshape(1,-1))
        all_pkts.append(numberofPackets)
    print(f'Min-Max Number of Packets : {min(all_pkts)} <--> {max(all_pkts)}')
    
    for q in range(1,num_win):
        data = usrp1_data[1,q*win_size:(q*win_size)+win_size] 
        Hest,Hest_0 = estObj.Rx_processing_Hest(data.reshape(1,-1),0,min(all_pkts)-1)
        ph_diff = np.angle(Hest[0,1:])- np.angle(Hest_0[0,1:])
        ph_diff[26:38] = np.zeros((12,))
        plt.plot(ph_diff)
        
   
    
   
    
   
    
   
    
   
    
   
    
   
    
   
    
   
    
   
    
   # Hest,Hest_0 = estObj.Rx_processing_Hest(usrp1_data[0,:].reshape(1,-1),0,30)
    # #lts_corr,numberofPackets,valid_peak_indices = estObj.detectPeaks(usrp1_data[0,:].reshape(1,-1))
    # # usrp2_data = np.fromfile(f'{save_dir}usrp_1_{k}.dat',dtype=np.complex64)
    # # usrp2_data = usrp2_data.reshape(-1,2).transpose()
    # # print(usrp1_data.shape)
    # # plt.plot(np.real(usrp1_data[0,0:10000]))
    # # plt.plot(np.real(usrp2_data[0,0:10000]))
    # #plt.plot(lts_corr)
    # #print(len(valid_peak_indices))
    # #plt.scatter(np.real(Hest[0]),np.imag(Hest[0]),s=10)
    # ph_diff = np.angle(Hest[0,1:])- np.angle(Hest_0[0,1:])
    # ph_diff[26:38] = np.zeros((12,))
    # plt.plot(ph_diff)