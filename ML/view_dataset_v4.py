# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 09:43:54 2023

@author: tmosman
"""

import scipy.io as scs
import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import train_test_split
X=np.arange(0,20)
y=np.arange(0,20)
locs = np.array([1,15,2,16,3,14,4,17,5,13,6,18,7,12,8,19,9,11,10,20])-1

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)
print(X_train)
print(X_test)
sub6 = np.load('../Data_processing/fist_20_grids_channels.npy',allow_pickle=True)
print(sub6.shape)

int_sub6_tr = np.zeros([1,256])
int_pwr_tr = np.zeros([1,1])
int_sub6_te = np.zeros([1,256])
int_pwr_te = np.zeros([1,1])
for i,loc in enumerate(locs):
    if i in X_train:
        
        all_ch_tr = sub6[loc]
        all_pwr_tr = np.tile(i+1,[all_ch_tr.shape[0],1])
        print(all_ch_tr.shape)
       # for 
        all_ch_tr = np.vstack((int_sub6_tr,all_ch_tr))
        int_sub6_tr = all_ch_tr
        
        
        all_pwr_tr = np.vstack((int_pwr_tr,all_pwr_tr))
        int_pwr_tr = all_pwr_tr
    elif i in X_test:
        all_ch_te = sub6[loc]
        all_pwr_te = np.tile(i+1,[all_ch_te.shape[0],1])
        print(all_ch_te.shape)
       # for 
        all_ch_te = np.vstack((int_sub6_te,all_ch_te))
        int_sub6_te = all_ch_te
        
        
        all_pwr_te = np.vstack((int_pwr_te,all_pwr_te))
        int_pwr_te = all_pwr_te
    
    #print(all_ch_est.shape)
    #print(all_pwr_est.shape)
    #all_ch_est[0,:]
np.save('./Datasets/trainset_channels_1.npy',all_ch_tr[1:,:])
np.save('./Datasets/trainset_locs_1.npy',all_pwr_tr[1:,:].astype(int)) 
np.save('./Datasets/testset_channels_1.npy',all_ch_te[1:,:])
np.save('./Datasets/testset_locs_1.npy',all_pwr_te[1:,:].astype(int)) 
print(np.load('./Datasets/trainset_channels_1.npy').shape)
print(np.load('./Datasets/trainset_locs_1.npy').shape)
print(np.load('./Datasets/testset_channels_1.npy').shape)
print(np.load('./Datasets/testset_locs_1.npy').shape)
'''
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
np.save('./Datasets/Trainset_sub6_channels_allx.npy',all_ch_est[1:,:])
np.save('./Datasets/Trainset_locs_allx.npy',all_pwr_est[1:,:].astype(int))
print(np.load('./Datasets/Trainset_sub6_channels_allx.npy').shape)
print(np.load('./Datasets/Trainset_locs_allx.npy').shape)




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
np.save('./Datasets/Testset_sub6_channels_allx.npy',all_ch_est[1:,:])
np.save('./Datasets/Testset_locs_allx.npy',all_pwr_est[1:,:].astype(int))
print(np.load('./Datasets/Testset_sub6_channels_allx.npy').shape)
print(np.load('./Datasets/Testset_locs_allx.npy').shape)

'''
