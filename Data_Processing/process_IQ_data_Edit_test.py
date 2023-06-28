# -*- coding: utf-8 -*-
"""
Created on Tue Jun 13 11:58:28 2023

@author: tmosman
"""

import numpy as np
import  matplotlib.pyplot as plt
from channels_compute import Estimator
import time

save_dir = r'E:/summer2023_sub6_system/Data_June_12th/capture1/'

estObj = Estimator(numberSubCarriers=64, numberOFDMSymbols=2, modOrder=16)
min_all = []
t1 = time.time()
all_locs =[]
for loc in range(1,21):
    save_dir = f'E:/summer2023_sub6_system/Data_June_12th/capture{loc}/'
    all_caps =[]
    tx = time.time()
    for k in range(10):
        u1 = []
        for usrp in range(1):    
        #for k in range(1):
            usrp1_data = np.fromfile(f'{save_dir}usrp_{0}_{k}.dat',dtype=np.complex64)
            usrp1_data = usrp1_data.reshape(-1,2).transpose()
            usrp2_data = np.fromfile(f'{save_dir}usrp_{1}_{k}.dat',dtype=np.complex64)
            usrp2_data = usrp2_data.reshape(-1,2).transpose()
            #print(usrp1_data.shape,usrp2_data.shape)
            max_index = min(usrp1_data.shape[1],usrp2_data.shape[1])
            all_data = np.vstack((usrp1_data[:,0:max_index],usrp2_data[:,0:max_index]))
            #print(all_data.shape)
            #break
            win_size = int(1e6)
            num_win = all_data.shape[1]//win_size
            
            for ch_idx in range(4):
                all_pkts = []
                ch_0 = np.zeros((1,64))
                plt.cla()
                for q in range(0,num_win):
                    data = all_data[ch_idx,q*win_size:(q*win_size)+win_size]
                    #print(f'Range: {q*win_size}:{(q*win_size)+win_size}')
                    lts_corr,numberofPackets,valid_peak_indices = estObj.detectPeaks(data.reshape(1,-1))
                    #ch_zeros = np.zeros((numberofPackets,64))
                    print(f'Location: {loc} Capture: {k} RF: {ch_idx} window: {q}')
                    
                    #select_pkt = 1
                    count = 0
                    for select_pkt in range(numberofPackets):
                        Hest,Hest_0,ber = estObj.Rx_processing_Hest(data.reshape(1,-1),ch_idx,select_pkt)
                        if ber == 0:
                            ph_diff = np.angle(Hest[0,1:])- np.angle(Hest_0[0,1:])
                            ph_diff[26:38] = np.zeros((12,))
                            
                            if np.var(ph_diff,axis=0) > 0.1:
                                print('---------------------------------- ')
                                print(f'USRP: {usrp+1} Capture: {k} RF: {ch_idx} window: {q}')
                                print(np.var(ph_diff,axis=0))
                                print('---------------------------------- ')
                            else:
                                ch_0 = np.vstack((ch_0,Hest))
                                count +=1 
                                plt.title(f'USRP: {usrp+1} Capture: {k} RF: {ch_idx} window: {q}')
                                plt.plot(ph_diff)
                                plt.pause(0.01)
                        if count == 100:
                            break
                u1.append(ch_0[1:,:])
                
        all_caps.append(np.array(u1))    
        np.save(f'./Hest_data/channels/channel_estimates_capture{k}_loc_{loc}.npy',np.array(u1))
                       
    print(f'Time Location {loc} : {(time.time()-tx)/60} minutes')
    np.save(f'./Hest_data/loc_{loc}_channel_estimates.npy',np.array(all_caps))  
    all_locs.append(np.array(all_caps))
np.save('./channel_estimates_all.npy',np.array(all_locs))                  
print(f'Time All:  {(time.time()-t1)/60} minutes') 

'''
all_locs -- shape
(numberlocs,numberCaptures,RFchannels,packets/numberofHest,numberOfSubcarriers)
'''
