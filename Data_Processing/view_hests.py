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
fig = plt.figure(figsize=(9,9))
fig.subplots_adjust(top=0.85)
fig.tight_layout(pad=3.5)
initial = 220
subplot_list = [fig.add_subplot(initial+fig_idx) for fig_idx in range(1,5)]

for loc in range(3,11):
    a = [x.clear() for x in subplot_list]
    for cap in range(10):
        h_est = np.load(h_dir+f'channel_estimates_capture{cap}_loc_{loc}.npy')
        print(h_est.shape)
        # ch1 = h_est[0,:,:]
        # print(ch1.shape)
        
        for k in range( h_est[0,:,:].shape[0]):
            #plt.title(f'Location : {loc}, Capture :{cap}, Packet :{k}')
            fig.suptitle(f'Location : {loc}, Capture :{cap}, Packet :{k}', fontsize=16)
            for i,ax in enumerate(subplot_list):
                ax.set_title(f'RF : {i}')
                all_ph = np.angle(h_est[i,:,:][k,1:])
                all_ph[26:38] = np.zeros((12,))
                ax.plot(all_ph)
            plt.pause(0.01)
            
        plt.pause(0.1)
    