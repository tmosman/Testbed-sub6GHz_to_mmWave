# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 12:24:37 2023

@author: osman
"""

import numpy as np
import  matplotlib.pyplot as plt
from channels_compute import Estimator
import time



h_dir = './Hest_data/channels/'

allch = []
count = 0
for loc in range(1,21):
    #a = [x.clear() for x in subplot_list]
    a_ls = []
    aa = np.zeros((1,256))
    
    for cap in range(10):
        h_est = np.load(h_dir+f'channel_estimates_capture{cap}_loc_{loc}.npy')
        #print(h_est.shape)
        #ch1 = h_est[0,:,:]
        #print(ch1.shape)
        all_h = np.zeros((h_est[0,:,:].shape[0],64*4),dtype=np.complex64)
        count+=h_est[0,:,:].shape[0]
        print(f'Location : {loc} ----------: {h_est[0,:,:].shape[0]}')
        for k in range( h_est[0,:,:].shape[0]):
            h = np.zeros((64,))
            for i in range(4):
                new_h = h_est[i,:,:][k,:]
                new_h[0] = 0+0*1j
                new_h[26:38] = np.zeros((12,),dtype=np.complex64)
                #print(h.shape, new_h.shape)
                h = np.hstack((h,new_h))
                
            all_h[k,:]= h[64:]
        a_ls.append(all_h)
        aa = np.vstack((aa,np.array(all_h)))
        
    allch.append(aa)
np.save('./fist_20_grids_channels.npy', np.array(allch, dtype=object), allow_pickle=True)
print(f'Total data size: {count}')
    