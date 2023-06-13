# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 11:41:58 2022
Updated: Friday June 9, 2023
@author: Tawfik Osman

"""

import time
import numpy as np
import sys
#from datetime import datetime
import scipy.io as sc
import ast
from scipy import signal as sig
import matplotlib.pyplot as plt
import numpy.matlib

class Estimator:
    def __init__(self,numberSubCarriers,numberOFDMSymbols,modOrder):
        self.N_OFDM_SYMS = numberOFDMSymbols  # Number of OFDM symbols
        self.MOD_ORDER   = modOrder           # Modulation order (2/4/16/64 = BSPK/QPSK/16-QAM/64-QAM)
        if numberSubCarriers == 64:
            self.subcarriersIndex_64(numberSubCarriers)
        self.lts_time,self.all_preamble = self.preamble()
        self.LTS_CORR_THRESH = 0.75
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

    def detectPeaks(self,data):
        """
        Time synchronization; Detect LTS peaks
        Input:
            data - time domain received IQ samples
        Output:
            lts_corr - autocorrelation output
            numberofPackets - Number of detected packets in the raw samples
            valid_peak_indices - Indices of the detected packets
        """
        data = self.decimate2x(data,0) ## Edited
        
        flip_lts = np.fliplr(self.lts_time)
        lts_corr = abs(np.convolve(np.conj(flip_lts[0,:]),data[0,:], mode='full'))
        lts_peaks = np.argwhere(lts_corr > self.LTS_CORR_THRESH*np.max(lts_corr));
        
        #print(len(lts_peaks))
        [LTS1, LTS2] = np.meshgrid(lts_peaks,lts_peaks);
        [lts_second_peak_index,_] = np.where(LTS2-LTS1 == np.shape(self.lts_time)[1]);
        valid_peak_indices = lts_peaks[lts_second_peak_index].flatten()
        #print(lts_second_peak_index)
        
        if len(valid_peak_indices) >=2:
            select_peak = np.argmax(lts_second_peak_index)-1
            payload_ind = valid_peak_indices[select_peak]
            lts_ind = payload_ind-160;
            lts_ind = lts_ind+1
            # print('Number of Packets Detected: ',len(valid_peak_indices),
            #       f' at {payload_ind}')
            #print(lts_peaks[lts_second_peak_index].flatten())
        else:
            payload_ind,lts_ind = 0,0
            print('No Packet Detected !!!')
        numberofPackets = len(valid_peak_indices)
       
        return lts_corr,numberofPackets,valid_peak_indices
    def detectPeaks_process(self,data):
        """
        Time synchronization; Detect LTS peaks
        Input:
            data - time domain received IQ samples
        Output:
            lts_corr - autocorrelation output
            numberofPackets - Number of detected packets in the raw samples
            valid_peak_indices - Indices of the detected packets
        """
        #data = self.decimate2x(data,0) ## Edited
        
        flip_lts = np.fliplr(self.lts_time)
        lts_corr = abs(np.convolve(np.conj(flip_lts[0,:]),data[0,:], mode='full'))
        lts_peaks = np.argwhere(lts_corr > self.LTS_CORR_THRESH*np.max(lts_corr));
        
        #print(len(lts_peaks))
        [LTS1, LTS2] = np.meshgrid(lts_peaks,lts_peaks);
        [lts_second_peak_index,_] = np.where(LTS2-LTS1 == np.shape(self.lts_time)[1]);
        valid_peak_indices = lts_peaks[lts_second_peak_index].flatten()
        #print(lts_second_peak_index)
        
        if len(valid_peak_indices) >=2:
            select_peak = np.argmax(lts_second_peak_index)-1
            payload_ind = valid_peak_indices[select_peak]
            lts_ind = payload_ind-160;
            lts_ind = lts_ind+1
            #print('Number of Packets Detected: ',len(valid_peak_indices),
            #      f' at {payload_ind}')
            #print(lts_peaks[lts_second_peak_index].flatten())
        else:
            payload_ind,lts_ind = 0,0
            print('No Packet Detected !!!')
        numberofPackets = len(valid_peak_indices)
       
        return lts_corr,numberofPackets,valid_peak_indices
    def decimate2x(self,data,idx):
        """
        Down sample the received IQ samples by a factor of 2
        
        """
        # Read the captured IQ sample file, filter
        filter_coeff = sc.loadmat('./files_req/filter_array.mat')['interp_filt2']
        
       # data_conv = np.convolve(data_recv[0,:],h[0,:],'full').reshape(1,-1)
        filter_data = sig.upfirdn(filter_coeff[0,:],data[idx,:],down=2).reshape(1,-1)
        
        return filter_data
    
    def cfoEstimate(self,dataSamples, lts_index, do_cfo):
        """
        Estimate and correct CFO
        Input:
            dataSamples - time domain received signal before CFo correction
            lts_index - starting index of the lts samples
            do_cfo - Boolean argument True/False
            
        Output:
            cfo_samples_t - data samples after cfo correction;
        """
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
        cfo_samples_t  = dataSamples  * rx_cfo_corr_t
        
        return cfo_samples_t
    
    def complexChannelGain(self,dataSamples,lts_index):
        """
        compute channel estimates from LTS sequences
        Input:
            dataSamples - time domain received signal after CFo correction
            lts_index - starting index of the lts samples
            
        Output:
            rx_H_est - vector of complex channel gains
        """
        
        rx_lts = dataSamples[0,lts_index : lts_index+160]
        rx_lts1 = rx_lts[-64+-self.FFT_OFFSET + 96:-64+-self.FFT_OFFSET +160];  # Check indexing
        rx_lts2 = rx_lts[-self.FFT_OFFSET+96:-self.FFT_OFFSET+160]
        print(rx_lts1.shape,self.N_SC)
        if rx_lts1.shape[0] and rx_lts2.shape[0] == self.N_SC:
            rx_lts1_f, rx_lts2_f = np.fft.fft(rx_lts1), np.fft.fft(rx_lts2)
            # Calculate channel estimate from average of 2 training symbols
            rx_H_est = np.fft.fft(self.lts_time,64) * (rx_lts1_f + rx_lts2_f)/2
            
        else:
            rx_H_est = np.ones((1,64), dtype=np.complex64)

        return rx_H_est
    
    def equalizeSymbols(self,samples,payload_index,channelEstimates):
        """
        Equalizing the frequency domain received signal with channel estimates
        Input:
            samples - time domain received signal after CFo correction
            payload_index - starting index of the payload samples
            channelEstimates - vector of complex channel gains
        Output:
            rx_syms - Equalized, frequency domain received data symbols
        """
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
        rx_syms = syms_f_mat / (rep_rx_H)
        return rx_syms
    
    
    def demodumlate(self,equalizedSymbols):
        """
        Demodulating QAM symbols
        Input:
            equalizedSymbols - Equalized, frequency domain received signal
        Output:
            rx_data -received binary data
            rx_syms - Equalized, frequency domain received data symbols
        """
        payload_syms_mat = equalizedSymbols[self.SC_IND_DATA, :];
        ## Demodulate
        rx_syms = payload_syms_mat.transpose().reshape(1,self.N_DATA_SYMS)
        rx_syms = rx_syms.reshape(-1,self.N_DATA_SYMS)
        if self.MOD_ORDER == 16:
            demod_fcn_16qam = lambda x: (8*(np.real(x)>0)) + (4*(abs(np.real(x))<0.6325)) \
                            + (2*(np.imag(x)>0)) + (1*(abs(np.imag(x))<0.6325));
            rx_data = np.array(list(map(demod_fcn_16qam,rx_syms)))
        elif self.MOD_ORDER == 4:
            demod_fcn_qpsk = lambda x: (2*(np.real(x)>0)) + (1*(np.imag(x)>0)) 
            rx_data = np.array(list(map(demod_fcn_qpsk,rx_syms)))
        #rx_data = arrayfun(demod_fcn_16qam, rx_syms);
        elif self.MOD_ORDER == 2:
            demod_fcn_bpsk = lambda x: (1*(np.real(x)>0)) 
            rx_data = np.array(list(map(demod_fcn_bpsk,rx_syms)))
        
        return rx_data,rx_syms
    
    def sfo_correction(self, rxSig_freq_eq,ch_est):
        """
        Apply Sample Frequency Offset
        Input:
            rxSig_freq_eq - Equalized, frequency domain received signal
            pilot_sc      - Pilot subcarriers (indexes)
            pilots_matrix - Pilots in matrix form
            n_ofdm_syms   - Number of OFDM symbols
        Output:
            rxSig_freq_eq - Frequency domain signal after SFO correction

            pilots = [1 1 -1 1].';
            pilots_mat = repmat(pilots, 1, N_OFDM_SYMS);	
        """
        n_ofdm_syms = self.N_OFDM_SYMS
        pilot_sc = self.SC_IND_PILOTS
        pilot_syms= np.array([1,1, -1, 1])
        pilots_matrix = np.transpose(np.vstack((pilot_syms,pilot_syms)))
        
        # Extract pilots and equalize them by their nominal Tx values
        pilot_freq = rxSig_freq_eq[pilot_sc, :]
        pilot_freq_corr = pilot_freq * pilots_matrix
        
        # Compute phase of every RX pilot
        pilot_phase = np.angle(np.fft.fftshift(pilot_freq_corr))
        pilot_phase_uw = np.unwrap(pilot_phase)
        
        # Slope of pilot phase vs frequency of OFDM symbol
        pilot_shift = np.fft.fftshift(pilot_sc)
        pilot_shift_diff = np.diff(pilot_shift)
        pilot_shift_diff_mod = np.remainder(pilot_shift_diff, 64).reshape(len(pilot_shift_diff), 1)
        pilot_delta = np.matlib.repmat(pilot_shift_diff_mod, 1, n_ofdm_syms)
        pilot_slope = np.mean(np.diff(pilot_phase_uw, axis=0) / pilot_delta, axis=0)
        
        # Compute SFO correction phases
        tmp = np.array(range(-32, 32)).reshape(len(range(-32, 32)), 1)
        tmp2 = tmp * pilot_slope
        pilot_phase_sfo_corr = np.fft.fftshift(tmp2, 1)
        pilot_phase_corr = np.exp(-1j * pilot_phase_sfo_corr)
        
        # Apply correction per symbol
        rxSig_freq_eq = rxSig_freq_eq * pilot_phase_corr
        ch_est = ch_est* np.transpose(np.mean(pilot_phase_corr,axis=1))
        #print(rxSig_freq_eq.shape,pilot_phase_corr.shape,np.mean(pilot_phase_corr,axis=1).shape )
        
        return rxSig_freq_eq,ch_est
    def phase_correction(self, rxSig_freq_eq):
        """
        Apply Phase Correction
        Input:
            rxSig_freq_eq - Equalized, time domain received signal
            pilot_sc      - Pilot subcarriers (indexes)
            pilots_matrix - Pilots in matrix form
        Output:
            phase_error   - Computed phase error
        """
        # Extract pilots and equalize them by their nominal Tx values
        pilot_sc = self.SC_IND_PILOTS
        pilot_syms= np.array([1,1, -1, 1])
        pilots_matrix = np.transpose(np.vstack((pilot_syms,pilot_syms)))
        pilot_freq = rxSig_freq_eq[pilot_sc, :]
        pilot_freq_corr = pilot_freq * pilots_matrix
        
        # Calculate phase error for each symbol
        phase_error = np.angle(np.mean(pilot_freq_corr, axis=0))
        
        return phase_error


    def compute_BER(self,receivedSymbols,receivedData):
        if self.MOD_ORDER == 16:
            tx_data = sc.loadmat("./files_req/tx_data_usrp_mgs.mat")['tx_data']
            tx_syms =  sc.loadmat("./files_req/packet_syms_QAM_usrp_mgs.mat")['tx_syms']
        elif self.MOD_ORDER == 4:
            tx_data = sc.loadmat("./files_req/tx_data_usrp_mmWave_qpsk.mat")['tx_data'];
            tx_syms =  sc.loadmat("./files_req/packet_syms_QAM_usrp_mmWave_qpsk.mat")['tx_syms']
        elif self.MOD_ORDER == 2:
            tx_data = sc.loadmat("./files_req/tx_data_usrp_mmWave_bpsk.mat")['tx_data'];
            tx_syms =  sc.loadmat("./files_req/packet_syms_QAM_usrp_mmWave_bpsk.mat")['tx_syms']
        
        bit_errs = np.sum((tx_data^receivedData) != 0)
        rx_evm  = np.sqrt(np.sum((np.real(receivedSymbols) - np.real(tx_syms))**2 \
                                     + (np.imag(receivedSymbols) - np.imag(tx_syms))**2)/(len(self.SC_IND_DATA) * self.N_OFDM_SYMS));
        print('\nResults:\n');
        print(f'Num Bytes:  {self.N_DATA_SYMS * np.log2(self.MOD_ORDER) / 8 }\n' );
        #print(f'Sym Errors:  {sym_errs} (of { self.N_DATA_SYMS} total symbols)\n');
        print(f'Bit Errors:  {bit_errs} (of {self.N_DATA_SYMS * np.log2(self.MOD_ORDER)} total bits) {bit_errs/(self.N_DATA_SYMS * np.log2(self.MOD_ORDER))}\n')
        print(f'The Receiver EVM is : {(rx_evm)*100}%')
        bit_errs = bit_errs/(self.N_DATA_SYMS * np.log2(self.MOD_ORDER))
        return bit_errs,tx_syms
    
    
    def Rx_processing_noPlot(self,rx_samples,ch_indx,select_peak):
        # Downn sample the sample by 2
        output = self.decimate2x(rx_samples,ch_indx)
        
        #Time synchronization
        autocorr,no_of_peak,valid_peak_indices = self.detectPeaks(output)
        payload_ind = valid_peak_indices[select_peak]
        lts_ind = payload_ind-160;
        lts_ind = lts_ind+1
        print(f'Decoding Packet {select_peak}, starting at index {payload_ind}')

        # CFO correction
        dataOutput = self.cfoEstimate(output, lts_ind,do_cfo=False)
       
        # channel estimation
        Hest = self.complexChannelGain(dataOutput,lts_ind)
        
        # Equalization
        equalizeSymbols = self.equalizeSymbols(dataOutput, payload_ind, Hest)
        
        # Apply SFO correction
        sfo_syms,Hest_sfo = self.sfo_correction(equalizeSymbols,Hest)
        
        # Appy Phase Error correction
        phase_error = self.phase_correction(equalizeSymbols)
        print(np.mean(sfo_syms,axis=1).shape,Hest.shape,phase_error.shape)
        
        # Apply SFO + PE to the channel estimate, to correct residual offsets
        Hest = Hest_sfo* np.exp(-1j * np.mean(phase_error) )
        all_equalized_syms = sfo_syms * np.exp(-1j * phase_error) 
        
        # Demodulation of QAM symbols
        receivedData,receivedSymbols = self.demodumlate(all_equalized_syms)
        #receivedData,receivedSymbols = self.demodumlate(equalizeSymbols)
        
        # Compute BER
        ber,tx_syms = self.compute_BER(receivedSymbols, receivedData)
        
        return receivedSymbols,tx_syms,ber,Hest

    def Rx_processing(self,rx_samples,fig_list,rf_ch,count1,usrp_no):
        output = self.decimate2x(rx_samples,0)
        #output = self.decimate2x(output)
        autocorr,no_of_peak,valid_peak_indices = self.detectPeaks(output)

        payload_indx = valid_peak_indices[0]
        lts_indx = payload_indx-160;
        lts_indx = lts_indx+1

        dataOutput = self.cfoEstimate(output, lts_indx,do_cfo = False)
        ax = fig_list[0]
        ax1 = fig_list[1]
        ax2 = fig_list[2]
        ax3 = fig_list[3]
        
        if no_of_peak >= 2:
            plt.title(f'RF chain :{rf_ch}')
            #for select_peak in range(no_of_peak-1): 
            for select_peak in range(2,3): 
                payload_ind = valid_peak_indices[select_peak]
                lts_ind = payload_ind-160;
                lts_ind = lts_ind+1
                print(f'Decoding Packet {select_peak}, starting at index {payload_ind}')
                
                Hest = self.complexChannelGain(dataOutput,lts_ind)
                #Hest = np.ones((1,64),np.complex64)
                Hest0 = self.complexChannelGain(dataOutput,lts_indx)
                
                equalizeSymbols = self.equalizeSymbols(dataOutput, payload_ind, Hest0)
                ## apply SFO to the data symbols and the estimated channel
                sfo_syms,Hest_sfo = self.sfo_correction(equalizeSymbols,Hest)
                phase_error = self.phase_correction(equalizeSymbols)
                
                Hest = Hest_sfo* np.exp(-1j * np.mean(phase_error) ) # apply PE to the estimated channel
                all_equalized_syms = sfo_syms * np.exp(-1j * phase_error)  # apply PE to the data symbols
                receivedData,receivedSymbols = self.demodumlate(all_equalized_syms)
                #receivedData,receivedSymbols = self.demodumlate(equalizeSymbols)
                
                ber,tx_syms = self.compute_BER(receivedSymbols, receivedData)
                if ber <0.01:
                    print(f'BER of data symbols: {ber} %', )
                
                    if usrp_no == 0:
                        rf_ch = rf_ch
                    else:
                        rf_ch = rf_ch+2
                    color_plt =['blue','green','red','pink']

                    ax.set_title(f'Reveiver, BER => {ber:.4f}, RF :{rf_ch}')
                    ax.scatter(receivedSymbols.real,receivedSymbols.imag, s=5,  marker='o')
                    ax.scatter(tx_syms.real,tx_syms.imag, s=20,  marker='o',c='r')
                    #ax.set_xlabel('Real Component')
                    #ax.set_ylabel('Imaginary Component')
                    pdp = 10.0 * np.log10(np.fft.ifft(Hest[0],64))
                    tap = np.argmax(pdp)
                    print('channel:', Hest.shape)
                    ax1.set_title(f'Power Delay Profile at tap {tap}, RF :{rf_ch}')
                    #ax1.plot(np.arange(0,64),pdp)
                    ax1.plot(np.abs(dataOutput[0][payload_ind:payload_ind+80]))

                # ax1.plot(np.unwrap(np.angle(Hest[0]))-np.unwrap(np.angle(Hest0[0])))
                    
                    ## Load the channel estimate vecotor of packet 1 in previous capture
                    if count1 != 0 and rf_ch%1 ==0 and usrp_no == 0:
                        Hest_prev = sc.loadmat(f'./June_7th/RF{rf_ch}/sub6_iq_{count1-1}.mat')['data']
                    elif count1 != 0 and rf_ch%1 !=0 and usrp_no == 1:
                        Hest_prev = sc.loadmat(f'./June_7th/RF{rf_ch+2}/sub6_iq_{count1-1}.mat')['data']
                    else:
                        Hest_prev = self.complexChannelGain(dataOutput,lts_indx)
                
                    ax2.set_title(f'Absolute Phase Difference, RF :{rf_ch}')
                    #ph_diff = np.unwrap(np.angle(Hest0[0,1:]))-np.unwrap(np.angle(Hest_prev[0,1:]) ) # find the phase difference between current packet1 Hest and previous packet 1 Hest
                    
                    ph_diff = np.angle(Hest0[0,1:])- np.angle(Hest_prev[0,1:]) # find the phase difference between current packet1 Hest and previous packet 1 Hest#print(ph_diff[27-1:39-1].shape,np.zeros((12,)).shape)  
                    ph_diff[27-1:39-1] = np.zeros((12,))  # replace the complex gains of the guard bands with zeros.
                    ax2.plot(ph_diff)
                    #ax1.axis([0, 64, -10, 10])
                    ax3.set_title(f'Estimated channel(s) for RF-chain :{rf_ch}')
                    ax3.scatter(np.real(Hest[0]),np.imag(Hest[0]),s=1,color=color_plt[rf_ch])
                    
                    #ax1.set_xlabel('Sub-carriers')
                    #ax1.set_ylabel('Abs. Channel Response')
                    plt.pause(0.01)
                #Hest0 = self.complexChannelGain(dataOutput,lts_indx)  
            
        else:
            print('No Packet is decoded !!!')
            Hest = np.zeros((1,64),np.complex64)
            ber = 0.50
            '''
            ax.clear()
            ax1.clear()
            ax2.clear()
            ax3.clear()
                
            plt.cla()
            '''
        return Hest,Hest0
    def Rx_processing_Hest(self,rx_samples,rf_ch,select_peak):
        output = self.decimate2x(rx_samples,0)
        #output = self.decimate2x(output)
        autocorr,no_of_peak,valid_peak_indices = self.detectPeaks_process(output)

        payload_indx = valid_peak_indices[0]
        lts_indx = payload_indx-160;
        lts_indx = lts_indx+1

        dataOutput = self.cfoEstimate(output, lts_indx,do_cfo = False)
        
        if no_of_peak >= 2:
            for iqq in range(1): 
                payload_ind = valid_peak_indices[select_peak]
                lts_ind = payload_ind-160;
                lts_ind = lts_ind+1
                print(f'Decoding Packet {select_peak}, starting at index {payload_ind}')
                
                Hest = self.complexChannelGain(dataOutput,lts_ind)
                #Hest = np.ones((1,64),np.complex64)
                Hest0 = self.complexChannelGain(dataOutput,lts_indx)
                
                equalizeSymbols = self.equalizeSymbols(dataOutput, payload_ind, Hest0)
                ## apply SFO to the data symbols and the estimated channel
                sfo_syms,Hest_sfo = self.sfo_correction(equalizeSymbols,Hest)
                phase_error = self.phase_correction(equalizeSymbols)
                
                Hest = Hest_sfo* np.exp(-1j * np.mean(phase_error) ) # apply PE to the estimated channel
                all_equalized_syms = sfo_syms * np.exp(-1j * phase_error)  # apply PE to the data symbols
                receivedData,receivedSymbols = self.demodumlate(all_equalized_syms)
                #receivedData,receivedSymbols = self.demodumlate(equalizeSymbols)
                
                ber,tx_syms = self.compute_BER(receivedSymbols, receivedData)
        else:
            print('No Packet is decoded !!!')
            Hest = np.zeros((1,64),np.complex64)
            #ber = 0.50
            '''
            ax.clear()
            ax1.clear()
            ax2.clear()
            ax3.clear()
                
            plt.cla()
            '''
        return Hest,Hest0


if __name__ == "__main__":
    print(' run main script !!!')
