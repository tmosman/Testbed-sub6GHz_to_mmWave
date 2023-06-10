# -*- coding: utf-8 -*-
"""
Created on Sat Feb  4 17:05:44 2023
Updated: Friday June 9, 2023
@author: osman

"""

from main_classes_June_9th import GNURadioUHD,mmWaveSDR, pyUHD,createZMQ,Estimator,Robot_Interface
import time
from datetime import datetime
import numpy as np
import zmq
import logging
import matplotlib.pyplot as plt
import scipy.io as sc
import ast
#import uhd
#from usrp_func import _config_streamer,_start_stream,_config_usrp,_start_stream_new,_stop_stream,init_usrp_new,Capture_samples_new

def subscriber_zmq(usrp_dict,capture_config,queue,gnuRadioAPI = False):
    ## configured variables
    num_samps,num_runs =  int(capture_config['no_samples']),\
                           int(capture_config['num_capture'])
    local_ip = capture_config['ip']
    pubSubPort = ast.literal_eval(capture_config['pubSubPort'])
    reqRepPort = ast.literal_eval(capture_config['reqRepPort'])
    sdrAPI = ast.literal_eval(capture_config['API'])
    cap_dir  =  ast.literal_eval(capture_config['save_dir'])
    
    logging.basicConfig(filename='./config/logFile.log',level=logging.INFO, 
                        format='%(asctime)s : %(processName)s : %(message)s')
    
    #initialize zmq object
    zmq_obj = createZMQ(local_ip)
    
    # ZMQ subscriber and request objects
    subcriber = zmq_obj.createSubcriber(pubSubPort)
    requester = zmq_obj.createREQ(reqRepPort)
    
    if ast.literal_eval(usrp_dict['freq_band']) == 'sub6':
        #initialize the USRP device
        if sdrAPI == 'gnuradio':
            usrp_device = GNURadioUHD(usrp_dict)
            gnuRadioAPI = True
        else:
            usrp_device = pyUHD(usrp_dict)
            queue.put(f'{usrp_device.usrp_id} initialized')  # Signal to continue initialization
       
        try:
            # Sync 
            requester.send_string('')
            print(f'Synced with response !! {requester.recv().decode()}')
        except KeyboardInterrupt:
            print("\n Interrupting  !! .... \n")
        queue.put('Request-Response connections established !!!')
        print(' -- Subscriber and Request ZMQ Connections Initialized -- ')
        
        if gnuRadioAPI:
            print('Using gnuradio-uhd API .... ')
            usrp_device.start() 
            print('Flowgraph Started ... ')
            for k in range(num_runs):
                print(f'--- Capture {k} ----')
                if 'Ack' in str(subcriber.recv_string()):
                    
                    msg_content = subcriber.recv_pyobj()
                    t1 = time.time()
                    usrp_device.open_file([f'{cap_dir}cap_{k}.dat',f'{cap_dir}cap_1_{k}.dat'],2)
                    time.sleep(2)
                    usrp_device.close_file(2)
                    
                    usrp1_data = np.fromfile(f'{cap_dir}cap_{k}.dat',dtype=np.complex64)
                    usrp1_data = usrp1_data.reshape(-1,2).transpose()
                    
                    usrp2_data = np.fromfile(f'{cap_dir}cap_1_{k}.dat',dtype=np.complex64)
                    usrp2_data = usrp2_data.reshape(-1,2).transpose()
                    samples = {'data':'sub6',  'usrp1':usrp1_data,'usrp2':usrp2_data}
    
                    #samples = usrp_device.capture_samples(num_samps)
                    print(f'Time to capture: {(time.time()-t1)*1000} ms')
                    #print(f'Time now : {(datetime.now().microsecond)/1000}')
                    logging.info(f'{usrp_device.usrp_id} capture at: {(datetime.now().microsecond)/1000}')
                    #print(samples.shape)
                    #print(samples)
                    # Send IQ samples as response
                    #samples = np.zeros((4,1700))
                    requester.send_pyobj(samples)
                    requester.recv()
                    print(f'Latency {int(msg_content)}: {(time.time()-t1)*1000} ms')
                        # plt.plot(np.real(samples[0,:]))
                        # plt.pause(2)
                        
                else:
                    subcriber.close()
                    requester.close()
                    break
                logging.info(f'Done Captured IQ stream at {k}')
            usrp_device.stop()
            usrp_device.wait() 
            
        else:
            print('Using UHD Python API .... ')
            # Initialize USRP Streamer
            usrp_device._config_streamer()
            
            for k in range(num_runs):
                print(f'--- Capture {k} ----')
                if 'Ack' in str(subcriber.recv_string()):
                    msg_content = subcriber.recv_pyobj()
                    t1 = time.time()
                    samples = usrp_device.capture_samples(num_samps)
                    print(f'Time to capture: {(time.time()-t1)*1000} ms')
                    #print(f'Time now : {(datetime.now().microsecond)/1000}')
                    logging.info(f'{usrp_device.usrp_id} capture at: {(datetime.now().microsecond)/1000}')
                    print(samples.shape)
                    #print(samples)
                    # Send IQ samples as response
                    requester.send_pyobj(samples)
                    requester.recv()
                    print(f'Latency {int(msg_content)}: {(time.time()-t1)*1000} ms')
                    # plt.plot(np.real(samples[0,:]))
                    # plt.pause(2)
                    
                else:
                    subcriber.close()
                    requester.close()
                    break
            logging.info('Done Capturing')
            
    else:
        usrp_device = mmWaveSDR(usrp_dict)
        save_file = 'cap.dat'
        # Initialize Array
        #my_Array = Array(sn_id)
        usrp_device.phasedArray.initialize_Array(62.64e9)
        print(' -- Siver Array: Initialized -- ')
        queue.put(f'{usrp_dict["array"]} initialized')
        beams_pwrs = np.zeros((num_runs, 63))
            
        for k in range(num_runs):
            print(f'--- Capture {k} ----')
            if 'Ack' in str(subcriber.recv_string()):
                msg_content = subcriber.recv_pyobj()
                t1 = time.time()
                sweep_idx = int(msg_content)
                usrp_device.phasedArray.start_Sweep()
                # Beam Sweeping
                for beam_dir in np.arange(1,64):
                    t1 = time.time()
                    usrp_device.phasedArray.set_dir(beam_dir)
                    usrp_device.save_iq_stream(save_file)
                    #samples = usrp_device.capture_samples(num_samps)
                    print(f'Time to set : {(time.time()-t1)*1000} ms')
                    samples = np.fromfile(save_file,dtype=np.complex64)
                    #samples = samples.reshape(-1,).transpose()
                        
                    beams_pwrs[sweep_idx, beam_dir-1] = np.mean(np.abs(samples.reshape(-1,)) ** 2)
                plt.plot(beams_pwrs[sweep_idx,:])
                plt.pause(0.0001)
                    # Send IQ samples as response
                requester.send_pyobj(np.zeros([int(usrp_dict["no_channels_per_usrp"]),num_samps]))
                requester.recv()
                print(f'Latency {int(msg_content)}: {(time.time()-t1)*1000} ms')
                plt.plot(np.real(samples[0,:]))
                plt.pause(2)
                    
            else:
                subcriber.close()
                requester.close()
                break
        logging.info('Done Capturing')

def publisher_zmq(capture_config):
    ## Load configured variables
    num_conns,no_samples,num_capture =  int(capture_config['num_conns']), \
                                        int(capture_config['no_samples']), \
                                        int(capture_config['num_capture'])
    local_ip = capture_config['ip']
    pubSubPort = ast.literal_eval(capture_config['pubSubPort'])
    reqRepPort = ast.literal_eval(capture_config['reqRepPort'])
    total_channels  = int(capture_config['total_channels'])
    sdrAPI = ast.literal_eval(capture_config['API'])
    
    configMod = ast.literal_eval(capture_config['ModConfig'])
    no_Subcs,nOFDMsys,modOr = configMod['num_sc'],configMod['num_ofdm_syms'], \
                               configMod['modOder']
    
    
    ## load logger
    logging.basicConfig(filename='./config/logFile.log',level=logging.INFO, 
                        format='%(asctime)s : %(processName)s : %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p'
                        )
    
    ## create zmq object for the publisher process 
    zmq_obj = createZMQ(local_ip)
    if ast.literal_eval(capture_config['robot']) == 'yes':
        robot_client = Robot_Interface('127.0.0.1', 9999) # connect to the robot server script
        robotServer = True
    else:
        robotServer = False

    
    ## Initialize ZMQ
    publiser = zmq_obj.createPublisher(pubSubPort)
    responder = zmq_obj.createREP(reqRepPort)
    
    recv_data = np.zeros((num_capture,total_channels,no_samples),dtype=np.complex64)
    
    estObj = Estimator(numberSubCarriers=no_Subcs, numberOFDMSymbols=nOFDMsys, modOrder=modOr)
    
    ## Check for subcribers
    try:
        print("Finding Subscribers Devices")
        subscribers = 0
        while subscribers < num_conns:
            # Wait for syncronization request
            responder.recv()
            responder.send(b"Ack")
            subscribers += 1
            print("Found {} satellites".format(subscribers))
        time.sleep(1)
    except KeyboardInterrupt:
        print("\n Interrupting  !! .... \n")    
    logging.info(' Done Searching')
    ## create figure for the results displayed
    fig = plt.figure(figsize=(8,8))
    fig.subplots_adjust(top=0.85)
    fig.tight_layout(pad=3.5)
    subplot_list = []
    initial = 220
    for fig_idx in range(1,5):
        subplot_list.append(fig.add_subplot(initial+fig_idx))

    ## Loop thro' each capture
    for count in range(num_capture):
        #tx = time.time()
        publiser.send_string("Ack", flags=zmq.SNDMORE)
        publiser.send_pyobj(count)

        # Send command to Robot
        if robotServer == True:
            robot_client.send('Hello')

        print('send both')
        
        ## Receive IQ samples from each subscriber
        subscribers_in = 0
        IQ =[]
        if sdrAPI == 'gnuradio':
            # receive data from all connected subscribers
            while subscribers_in  < num_conns:
                t_1 = time.time()
                data_recv = responder.recv_pyobj()
                #recv_data[i,subscribers_in,:]
                if data_recv['data'] == 'sub6':
                    IQ.append(data_recv)
                #print(f' Print shape : {data_recv.shape}')
                subscribers_in += 1
                responder.send(b'')
                print(f'Time to receive 1 subscriber: {(time.time()-t_1)*1000} ms')
                
            #print(f'Delay : {(time.time()- tx)*1000} ms')
            #for iq_samples_dict in IQ:
            iq_samples_dict = IQ[0]
            for j in range(2):
                h_recv,h0 = estObj.Rx_processing(iq_samples_dict['usrp1'][j,:].reshape(1,-1),subplot_list,j,count,0)
                if j%1 ==0:
                    sc.savemat(f'./June_7th/RF{j}/sub6_iq_{count}.mat',{'data':h0})  # saving the Hest of the first packets 
                                                                                         # in each captured IQ samples
                else:
                    sc.savemat(f'./June_7th/RF{j}/sub6_iq_{count}.mat',{'data':h0})
                    #IQ.append(h_recv)
                print('Done')
                
            time.sleep(1)
            for j in range(2):
                h_recv,h0 = estObj.Rx_processing(iq_samples_dict['usrp2'][j,:].reshape(1,-1),subplot_list,j,count,1)
                if j%1 ==0:
                    sc.savemat(f'./June_7th/RF{2+j}/sub6_iq_{count}.mat',{'data':h0})
                else:
                    sc.savemat(f'./June_7th/RF{2+j}/sub6_iq_{count}.mat',{'data':h0})
                #IQ.append(h_recv)
                
            print('Done')    
                    
            #count+=1
            time.sleep(1)
            
        else:
            ## Receive IQ samples from each subscriber
            #estObj = EstimatorOld(numberSubCarriers=64, numberOFDMSymbols=2, modOrder=16)
            while subscribers_in  < num_conns:
                t_1 = time.time()
                data_recv = responder.recv_pyobj()
                #recv_data[i,subscribers_in,:]
                
                IQ.append(data_recv)
                print(f' Print shape : {data_recv.shape}')
                subscribers_in += 1
                responder.send(b'')
                print(f'Time to receive 1 subscriber: {(time.time()-t_1)*1000} ms')
                
            #print(f'Delay : {(time.time()- tx)*1000} ms')
            recv_data[count] = np.vstack((IQ[0],IQ[1]))
            #print('Ny=  sss_ :',recv_data[count].shape)
            for ch_indx in range(4):
                receivedSymbols,tx_syms,ber,Hest = estObj.Rx_processing_noPlot(recv_data[count],ch_indx,select_peak=2)
                subplot_list[ch_indx].set_title(f'Reveiver, BER => {ber:.4f}, RF :{ch_indx}')
                #subplot_list[ch_indx].set_title(f'Reveiver, BER => {ber}, RF :{ch_indx}')
                #fig_list[ch_indx].scatter(Hest.real,Hest.imag, s=5,  marker='o')
                subplot_list[ch_indx].scatter(receivedSymbols.real,receivedSymbols.imag, s=5,  marker='o')
                subplot_list[ch_indx].scatter(tx_syms.real,tx_syms.imag, s=20,  marker='*',c='r')
            sc.savemat(f'./uhd_capture/sub6_iq_{count}.mat',{'data':recv_data[count]})
        #estObj.Rx_processing(recv_data[i])
        #sc.savemat(f'sub6_iq_{i}.mat',{'data':recv_data[i]})
    plt.show() 
        
       
    print("Data Captution Done !!!")
    publiser.send_string("close", flags=zmq.SNDMORE)
    publiser.close()
    responder.close()
    
    
    
if __name__ == "__main__":
    print(' run main script !!!')
    
