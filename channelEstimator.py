# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 23:39:51 2023

@author: osman
"""

import numpy as np
import numpy.matlib
import matplotlib.pyplot as plt
import scipy.io as sc
from scipy import signal as sig

class Estimator:
    def __init__(self,numberSubCarriers,numberOFDMSymbols,modOrder):
        self.N_OFDM_SYMS = numberOFDMSymbols  # Number of OFDM symbols
        self.MOD_ORDER   = modOrder           # Modulation order (2/4/16/64 = BSPK/QPSK/16-QAM/64-QAM)
        if numberSubCarriers == 64:
            self.subcarriersIndex_64(numberSubCarriers)
        self.lts_time,self.all_preamble = self.preamble()
        self.LTS_CORR_THRESH = 0.95
        self.FFT_OFFSET = 4
        pass
    
    def subcarriersIndex_64(self,NSubCarriers):
        self.N_SC   = NSubCarriers     # Number of subcarriers
        self.CP_LEN = 16      # Cyclic prefix length
        #allCarriers = np.arange(1,NSubCarriers)  # indices of all subcarriers ([0, 1, ... K-1])
        self.SC_IND_PILOTS = np.array([7,21,43,57]);  # Pilot subcarrier indices
        #self.SC_IND_DATA = np.delete(allCarriers, self.SC_IND_PILOTS)
        self.SC_IND_DATA  = np.array([1,2,3,4,5,6,8,9,10,11,12,13,14,15,16,17,
                                      18,19,20,22,23,24,25,26,38,39,40,41,42,
                                      44,45,46,47,48,49,50,51,52,53,54,55,56,
                                      58,59,60,61,62,63]);     # Data subcarrier indices
        self.N_DATA_SYMS = self.N_OFDM_SYMS * len(self.SC_IND_DATA)  # Number of data symbols (one per data-bearing subcarrier per OFDM symbol)
        
        
    def preamble(self, zc = False):
        # STS
        sts_f = np.zeros((1,self.N_SC ),'complex')
        sts_f[0,0:27] = [0,0,0,0,-1-1j,0,0,0,-1-1j,0,0,0,1+1j,0,0,0,1+1j,0,0,0,
                         1+1j,0,0,0,1+1j,0,0]
        sts_f[0,38:]= [0,0,1+1j,0,0,0,-1-1j,0,0,0,1+1j,0,0,0,-1-1j,0,0,0,-1-1j,
                       0,0,0,1+1j,0,0,0];
        sts_t = np.fft.ifft(np.sqrt(13/6)*sts_f[0,:],64)
        sts_t = sts_t[0:16];
           
        # LTS 
        lts_t = np.zeros((1,self.N_SC ),'complex')
        lts_f = [0,1,-1,-1,1,1,-1,1,-1,1,-1,-1,-1,-1,-1,1,1,-1,-1,1,-1,1,-1,1,
                 1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,-1,-1,1,1,-1,1,-1,1,1,1,1,1,1,
                 -1,-1,1,1,-1,1,-1,1,1,1,1];
        lts_t[0,:] = np.fft.ifft(lts_f,64);
    
        # Generation of expected preamble
        if zc == True:
            zc_len = 1023
            idx = np.arange(zc_len)
            M_root =7
            zc = np.exp(-1j * np.pi * M_root / zc_len * idx * (idx + 1)).reshape(1,-1)
            preamble = np.concatenate((zc[0,:],lts_t[0,32:],lts_t[0,:],lts_t[0,:]),axis=0);
        else:
            AGC = np.matlib.repmat(sts_t, 1, 30);
            preamble = np.concatenate((AGC[0,:],lts_t[0,32:],lts_t[0,:],lts_t[0,:]),axis=0);
        return lts_t,preamble
    
    def detectPeaks(self,data,select_peak):
        flip_lts = np.fliplr(self.lts_time)
        lts_corr = abs(np.convolve(np.conj(flip_lts[0,:]),data[0,:], mode='full'))
        lts_peaks = np.argwhere(lts_corr > self.LTS_CORR_THRESH*np.max(lts_corr));
        
        #print(len(lts_peaks))
        [LTS1, LTS2] = np.meshgrid(lts_peaks,lts_peaks);
        [lts_second_peak_index,_] = np.where(LTS2-LTS1 == np.shape(self.lts_time)[1]);
        valid_peak_indices = lts_peaks[lts_second_peak_index].flatten()
        payload_ind = valid_peak_indices[select_peak]
        lts_ind = payload_ind-160;
        lts_ind = lts_ind+1
        print('Number of Packets Detected: ',len(lts_second_peak_index),
              f' at {payload_ind}')
        print(lts_peaks[lts_second_peak_index].flatten())
        return lts_corr,payload_ind,lts_ind
    
    def decimate2x(self,data):
        # Read the captured IQ sample file, filter
        h = sc.loadmat('./files_req/filter_array.mat')['interp_filt2']
        print(h.shape)
       # data_conv = np.convolve(data_recv[0,:],h[0,:],'full').reshape(1,-1)
        filter_data = sig.upfirdn(h[0,:],data[0,:],down=2).reshape(1,-1)
        return filter_data
    def cfoEstimate(self,dataSamples, lts_index,do_cfo = True):
        print(dataSamples.shape)
        ## CFO Correction
        if do_cfo == True:
            rx_lts = dataSamples[0,lts_index : lts_index+160] #Extract LTS (not yet CFO corrected)
            rx_lts1 = rx_lts[-64+-self.FFT_OFFSET + 96:-64+-self.FFT_OFFSET +160];  # Check indexing
            rx_lts2 = rx_lts[-self.FFT_OFFSET+96:-self.FFT_OFFSET+160];
            
            #Calculate coarse CFO est
            rx_cfo_est_lts = np.mean(np.unwrap(np.angle(rx_lts2 * np.conj(rx_lts1))));
            rx_cfo_est_lts = rx_cfo_est_lts/(2*np.pi*64);
        else:
            rx_cfo_est_lts = 0;
        
        # Apply CFO correction to raw Rx waveform
        time_vec = np.arange(0,np.shape(dataSamples)[1],1);
        rx_cfo_corr_t = np.exp(-1j*2*np.pi*rx_cfo_est_lts*time_vec);
        return dataSamples  * rx_cfo_corr_t;
    
    def complexChannelGain(self,dataSamples,lts_index):
        rx_lts = dataSamples[0,lts_index : lts_index+160];
        rx_lts1 = rx_lts[-64+-self.FFT_OFFSET + 96:-64+-self.FFT_OFFSET +160];  # Check indexing
        rx_lts2 = rx_lts[-self.FFT_OFFSET+96:-self.FFT_OFFSET+160];
        rx_lts1_f, rx_lts2_f = np.fft.fft(rx_lts1), np.fft.fft(rx_lts2);
        # Calculate channel estimate from average of 2 training symbols
        rx_H_est = np.fft.fft(self.lts_time,64) * (rx_lts1_f + rx_lts2_f)/2;
        return rx_H_est
    
    def equalizeSymbols(self,samples,payload_index,channelEstimates):
        rx_dec_cfo_corr = samples[0,:]
        payload_vec = rx_dec_cfo_corr[payload_index+1: payload_index+self.N_OFDM_SYMS*(self.N_SC+self.CP_LEN)+1]; # Extract received OFDM Symbols
        payload_mat = np.matlib.reshape(payload_vec, (self.N_OFDM_SYMS,(self.N_SC+self.CP_LEN) )).transpose(); # Reshape symbols
        #payload_mat = np.transpose(payload_mat)
                
        # Remove the cyclic prefix, keeping FFT_OFFSET samples of CP (on average)
        payload_mat_noCP = payload_mat[self.CP_LEN-self.FFT_OFFSET:self.CP_LEN-self.FFT_OFFSET+self.N_SC, :];
                
        # Take the FFT
        syms_f_mat = np.fft.fft(payload_mat_noCP, self.N_SC, axis=0);
                
        # Equalize (zero-forcing, just divide by complex chan estimates)
        rep_rx_H = np.transpose(np.matlib.repmat(channelEstimates, self.N_OFDM_SYMS,1))
        return  syms_f_mat / (rep_rx_H);
    
    def demodumlate(self,equalizedSymbols):
        payload_syms_mat = equalizedSymbols[self.SC_IND_DATA, :];
        ## Demodulate
        rx_syms = payload_syms_mat.transpose().reshape(1,self.N_DATA_SYMS)
        rx_syms = rx_syms.reshape(-1,self.N_DATA_SYMS)
        demod_fcn_16qam = lambda x: (8*(np.real(x)>0)) + (4*(abs(np.real(x))<0.6325)) \
                            + (2*(np.imag(x)>0)) + (1*(abs(np.imag(x))<0.6325));
                
        #rx_data = arrayfun(demod_fcn_16qam, rx_syms);
        rx_data = np.array(list(map(demod_fcn_16qam,rx_syms)))
        
        return rx_data,rx_syms
    
    def ber(self,receivedSymbols,receivedData):
        tx_data = sc.loadmat("./files_req/tx_data_usrp_mgs.mat")['tx_data'];
        tx_syms =  sc.loadmat("./files_req/packet_syms_QAM_usrp_mgs.mat")['tx_syms']
                #print(tx_data)
                # tx_data = double(tx_data{1});
        sym_errs = np.sum(tx_data != receivedData);
        bit_errs = np.sum((tx_data^receivedData) != 0)
        rx_evm  = np.sqrt(np.sum((np.real(receivedSymbols) - np.real(tx_syms))**2 \
                                 + (np.imag(receivedSymbols) - np.imag(tx_syms))**2)/(len(self.SC_IND_DATA) * self.N_OFDM_SYMS));
    
        print('\nResults:\n');
        print(f'Num Bytes:  {self.N_DATA_SYMS * np.log2(self.MOD_ORDER) / 8 }\n' );
        print(f'Sym Errors:  {sym_errs} (of { self.N_DATA_SYMS} total symbols)\n');
        print(f'Bit Errors:  {bit_errs} (of {self.N_DATA_SYMS * np.log2(self.MOD_ORDER)} total bits) {bit_errs/(self.N_DATA_SYMS * np.log2(self.MOD_ORDER))}\n')
        print(f'The Receiver EVM is : {(rx_evm)*100}%')
        return 1
    def Rx_processing(self,rx_samples):
        output = self.decimate2x(rx_samples)
        autocorr,payload_ind,lts_ind = self.detectPeaks(output,0)
        #plt.plot(autocorr)
        #print(payload_ind,lts_ind)
        dataOutput = self.cfoEstimate(output, lts_ind)
        Hest = self.complexChannelGain(dataOutput,lts_ind)
        equalizeSymbols = self.equalizeSymbols(dataOutput, payload_ind, Hest)
        
        receivedData,receivedSymbols = self.demodumlate(equalizeSymbols)
        plt.plot(receivedSymbols.real,receivedSymbols.imag, 'bo')
        plt.pause(3)
        return self.ber(receivedSymbols, receivedData)
    
    
        
if __name__ == "__main__":
    estObj = Estimator(numberSubCarriers=64, numberOFDMSymbols=2, modOrder=16)
    transmit_waveform = sc.loadmat("sub6_iq_1.mat")['data']
    #transmit_waveform = sc.loadmat("OFDM_packet_upsample_x2.mat")['tx_vec_air_A']
    rx_OTA = np.tile(transmit_waveform, 1)
    estObj.Rx_processing(rx_OTA)
   
    
   
    
   #lts,_ = estObj.preamble()
    # plt.plot(np.real(output))
    # #autocorr = abs(np.convolve(output[:],np.conj(np.fliplr(lts)[0,:]),  mode='full'))
  