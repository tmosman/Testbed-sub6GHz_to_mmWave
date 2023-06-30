# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 09:43:54 2023

@author: tmosman
"""

import scipy.io as scs
import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import train_test_split
X=np.arange(0,10)
y=np.arange(0,10)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)
print(X_train)
print(X_test)
sub6 = np.load('../Data_processing/fist_10_grids_channels.npy',allow_pickle=True)
print(sub6.shape)


int_sub6 = np.zeros([1,256])
int_pwr = np.zeros([1,1])
for loc in X_train:
    all_ch_est = sub6[loc]
    all_pwr_est = np.tile(loc+1,[all_ch_est.shape[0],1])
    print(all_ch_est.shape)
   # for 
    all_ch_est = np.vstack((int_sub6,all_ch_est))
    int_sub6 = all_ch_est
    
    
    all_pwr_est = np.vstack((int_pwr,all_pwr_est))
    int_pwr = all_pwr_est
    
    #print(all_ch_est.shape)
    #print(all_pwr_est.shape)
    #all_ch_est[0,:]
np.save('./Trainset_sub6_channels.npy',all_ch_est[1:,:])
np.save('./Trainset_locs.npy',all_pwr_est[1:,:].astype(int))
print(np.load('./Trainset_sub6_channels.npy').shape)
print(np.load('./Trainset_locs.npy').shape)




int_sub6 = np.zeros([1,256])
int_pwr = np.zeros([1,1])
for loc in X_test:
    all_ch_est = sub6[loc]
    all_pwr_est = np.tile(loc+1,[all_ch_est.shape[0],1])
    print(all_ch_est.shape)
   # for 
    all_ch_est = np.vstack((int_sub6,all_ch_est))
    int_sub6 = all_ch_est
    
    
    all_pwr_est = np.vstack((int_pwr,all_pwr_est))
    int_pwr = all_pwr_est
np.save('./Testset_sub6_channels.npy',all_ch_est[1:,:])
np.save('./Testset_locs.npy',all_pwr_est[1:,:].astype(int))
print(np.load('./Testset_sub6_channels.npy').shape)
print(np.load('./Testset_locs.npy').shape)

'''
'''