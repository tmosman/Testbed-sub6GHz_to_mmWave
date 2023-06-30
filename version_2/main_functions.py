# -*- coding: utf-8 -*-
"""
Created on Sat Feb  4 17:05:44 2023
Updated: Friday June 9, 2023
@author: osman

"""

from main_classes import * #GNURadioUHD,mmWaveSDR, pyUHD,createZMQ,Estimator,Robot_Interface
import time
from datetime import datetime
import numpy as np
import zmq
import logging
import matplotlib.pyplot as plt
import scipy.io as sc
import ast
import os
def subscriber_zmq(usrp_dict,capture_config,queue,save_dir,gnuRadioAPI = False):
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
            print('\n .... Using gnuradio-uhd API .... \n')
            usrp_device.start() 
            print('Flowgraph Started ... ')
            for loc in range(1):
                if not os.path.exists(save_dir+'/usrp1'):
                    os.mkdir(save_dir+'/usrp1')
                if not os.path.exists(save_dir+'/usrp2'):
                    os.mkdir(save_dir+'/usrp2')

                for k in range(num_runs):
                    print(f'--- Capture {k} ----')
                    if 'Ack' in str(subcriber.recv_string()):
                        msg_content = subcriber.recv_pyobj()
                        t1 = time.time()
                        usrp_device.open_file([f'{save_dir}/usrp1/cap_{k}.dat',f'{save_dir}/usrp2/cap_{k}.dat'],2)
                        time.sleep(20)
                        usrp_device.close_file(2)
                        
                        ## load and reshape the IQ samples saved 
                        usrp1_data = np.fromfile(f'{save_dir}/usrp1/cap_{k}.dat',dtype=np.complex64)
                        usrp1_data = usrp1_data.reshape(-1,2).transpose()
                        usrp2_data = np.fromfile(f'{save_dir}/usrp2/cap_{k}.dat',dtype=np.complex64)
                        usrp2_data = usrp2_data.reshape(-1,2).transpose()

                        samples = {'dataType':'sub6',  'usrp1':usrp1_data,'usrp2':usrp2_data}
                        print(f'Time to capture: {(time.time()-t1)*1000} ms')
                        #print(f'Time now : {(datetime.now().microsecond)/1000}')
                        logging.info(f'{usrp_device.usrp_id} capture at: {(datetime.now().microsecond)/1000} nano secs')
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
                    logging.info(f'Done Captured IQ stream at {k}')
                usrp_device.stop()
                usrp_device.wait()

            
        else:
            print('\n ... Using UHD Python API .... \n')
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
        mmW_device = mmWaveSDR(usrp_dict)
        mmW_device.usrp_device._config_streamer()
        # Initialize Array
        mmW_device.init_Parray(ast.literal_eval(usrp_dict['carrier_freq']))
        print(' -- Siver Array: Initialized -- ')
        queue.put(f'{usrp_dict["array"]} initialized')
        beams_pwrs = np.zeros((num_runs, 63))

        try:
            # Sync 
            requester.send_string('')
            print(f'Synced with response !! {requester.recv().decode()}')
        except KeyboardInterrupt:
            print("\n Interrupting  !! .... \n")
        queue.put('Request-Response connections established !!!')
        print(' -- Subscriber and Request ZMQ Connections Initialized -- ')

        for k in range(num_runs):
            print(f'--- Capture {k} ----')
            if 'Ack' in str(subcriber.recv_string()):
                msg_content = subcriber.recv_pyobj()
                t1 = time.time()
                sweep_idx = int(msg_content)
                mmW_device.phasedArray.start_Sweep()
                #print('PA start sweep')
                
                # Beam Sweeping
                for beam_dir in np.arange(1,64):
                    t1 = time.time()
                    mmW_device.phasedArray.set_dir(beam_dir)
                    #usrp_device.save_iq_stream(save_file)
                    mmW_device.phasedArray.set_dir(beam_dir)
                    samples = mmW_device.usrp_device.capture_samples_new(num_samps)
                    #print(f'Time to set : {(time.time()-t1)*1000} ms')                        
                    beams_pwrs[sweep_idx, beam_dir-1] = np.mean(np.abs(samples.reshape(-1,)) ** 2)
                #plt.plot(beams_pwrs[sweep_idx,:])
                #plt.pause(1)
                #plt.draw()
                # Send best beam and power vector as a response
                samples = {'dataType':'mmWave',  'pwr':beams_pwrs[sweep_idx,:],'bestBeam':np.argmax(beams_pwrs[sweep_idx,:])+1}
                requester.send_pyobj(samples)
                requester.recv()
                #print(f'Latency {int(msg_content)}: {(time.time()-t1)*1000} ms')
                #plt.plot(np.real(samples[0,:]))
                #plt.pause(2)
                    
            else:
                subcriber.close()
                requester.close()
                break
        logging.info('Done mmWave Capturing')
        #plt.show()

def publisher_zmq(capture_config,save_dir):
    ## Load configured variables
    num_conns,no_samples,num_capture =  int(capture_config['num_conns']), \
                                        int(capture_config['no_samples']), \
                                        int(capture_config['num_capture'])
    local_ip = capture_config['ip']
    pubSubPort = ast.literal_eval(capture_config['pubSubPort'])
    reqRepPort = ast.literal_eval(capture_config['reqRepPort'])
    total_channels  = int(capture_config['total_channels'])
    sdrAPI = ast.literal_eval(capture_config['API'])
    dualSystem = ast.literal_eval(capture_config['plus_mmWave'])
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
        robot_client = Robot_Interface('192.168.1.150', 9999) # connect to the robot server script
        robotServer = True
    else:
        robotServer = False

    
    ## Initialize ZMQ
    publiser = zmq_obj.createPublisher(pubSubPort)
    responder = zmq_obj.createREP(reqRepPort)
    
    recv_data = np.zeros((num_capture,total_channels,no_samples),dtype=np.complex64)
    mmW_data = np.zeros((num_capture,63),dtype=np.complex64)
    
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
    fig = plt.figure(2,figsize=(8,8))
    fig.subplots_adjust(top=0.85)
    fig.tight_layout(pad=3.5)
    initial = 220
    subplot_list = [fig.add_subplot(initial+fig_idx) for fig_idx in range(1,5)]
    

    # For each loc
    for loc in range(1):

        ## Loop thro' each capture
        for count in range(num_capture):
            #tx = time.time()
            publiser.send_string("Ack", flags=zmq.SNDMORE)
            publiser.send_pyobj(count)

            # Send command to Robot
            print('send both')
            
            ## Receive IQ samples from each subscriber
            subscribers_in = 0
            IQ =[]
            if sdrAPI == 'gnuradio':
                # receive data from all connected subscribers
                while subscribers_in  < num_conns:
                    t_1 = time.time()
                    data_recv = responder.recv_pyobj()
                    #IQ.append(data_recv)
                    
                    if data_recv['dataType'] == 'sub6':
                        IQ.append(data_recv)
                    elif data_recv['dataType'] == 'mmWave':
                        mmW_data[count,:] = data_recv['pwr']

                    subscribers_in += 1
                    responder.send(b'')
                    print(f'Time to receive 1 subscriber: {(time.time()-t_1)*1000} ms')
                #print(IQ)
                if dualSystem == 'no':
                    iq_samples_dict = IQ[0]
                    pwr_vec = mmW_data[count,:]
                    np.save(f'{save_dir}/powervec_cap_{count}.npy',pwr_vec)
                    win_len = 50000
                    '''
                    subplot_list[0].clear()
                    subplot_list[1].clear()
                    subplot_list[2].clear()
                    subplot_list[3].clear()
                    '''
                    

                    for j in range(2):
                        h_recv,h0 = estObj.Rx_processing(iq_samples_dict['usrp1'][j,:][0:win_len].reshape(1,-1),subplot_list,j,count,0,pwr_vec)
                        if j%1 ==0:
                            sc.savemat(f'./June_7th/RF{j}/sub6_iq_{count}.mat',{'data':h0})  # saving the Hest of the first packets  in each captured IQ samples                                                                     
                        else:
                            sc.savemat(f'./June_7th/RF{j}/sub6_iq_{count}.mat',{'data':h0})
                    print('Done')   
                    #time.sleep(1)
                    for j in range(2):
                        h_recv,h0 = estObj.Rx_processing(iq_samples_dict['usrp2'][j,:][0:win_len].reshape(1,-1),subplot_list,j,count,1,pwr_vec)
                        if j%1 ==0:
                            sc.savemat(f'./June_7th/RF{2+j}/sub6_iq_{count}.mat',{'data':h0})
                        else:
                            sc.savemat(f'./June_7th/RF{2+j}/sub6_iq_{count}.mat',{'data':h0})
                    print('Done')
                    plt.pause(1)    
                    #time.sleep(1)
                    subplot_list[0].clear()
                    subplot_list[1].clear()
                    subplot_list[2].clear()
                    subplot_list[3].clear()

            
            else:
                ## Receive IQ samples from each subscriber
                while subscribers_in  < num_conns:
                    t_1 = time.time()
                    data_recv = responder.recv_pyobj()
                    IQ.append(data_recv)
                    print(f' Print shape : {data_recv.shape}')
                    subscribers_in += 1
                    responder.send(b'')
                    print(f'Time to receive 1 subscriber: {(time.time()-t_1)*1000} ms')
            
                recv_data[count] = np.vstack((IQ[0],IQ[1]))
                for ch_indx in range(4):
                    receivedSymbols,tx_syms,ber,Hest = estObj.Rx_processing_noPlot(recv_data[count],ch_indx,select_peak=2)
                    subplot_list[ch_indx].set_title(f'Reveiver, BER => {ber:.4f}, RF :{ch_indx}')
                    #subplot_list[ch_indx].set_title(f'Reveiver, BER => {ber}, RF :{ch_indx}')
                    #fig_list[ch_indx].scatter(Hest.real,Hest.imag, s=5,  marker='o')
                    subplot_list[ch_indx].scatter(receivedSymbols.real,receivedSymbols.imag, s=5,  marker='o')
                    subplot_list[ch_indx].scatter(tx_syms.real,tx_syms.imag, s=20,  marker='*',c='r')
                sc.savemat(f'./uhd_capture/sub6_iq_{count}.mat',{'data':recv_data[count]})
        #if dualSystem == 'yes':
            
            if robotServer == True:
                    #robot_client.send('Hello')
                mgs = f"MOVE+{count}"
                robot_client.send(mgs)
                time.sleep(2)

        
            
        
        print("Data Captution Done !!!")
        publiser.send_string("close", flags=zmq.SNDMORE)
        np.save(f'{ast.literal_eval(capture_config["save_dir"])}power_vector.npy',mmW_data)
        publiser.close()
        responder.close()
    plt.show() 


if __name__ == "__main__":
    print(' run main script !!!')
    
