# -*- coding: utf-8 -*-
"""
Created on Sat Feb  4 17:05:44 2023

@author: osman
"""

from main_classes import usrpUHD,createZMQ,Robot_Interface,Array
import time
from datetime import datetime
import numpy as np
import zmq
import logging
import matplotlib.pyplot as plt
import scipy.io as sc
from channelEstimator import Estimator
  
def subscriber_zmq(local_ip,usrp_dict,num_samps,num_runs,queue):
    
    logging.basicConfig(filename='./files_req/logFile.log',level=logging.INFO, 
                        format='%(asctime)s : %(processName)s : %(message)s')
    
    #initialize zmq object
    zmq_obj = createZMQ(local_ip)
    
    # ZMQ subscriber and request objects
    subcriber = zmq_obj.createSubcriber(9993)
    requester = zmq_obj.createREQ(9994)
    
    #initialize the USRP device
    usrp_device = usrpUHD(usrp_dict)
    queue.put(f'{usrp_device.usrp_id} initialized')  # Signal to continue initialization
    try:
        # Sync 
        requester.send_string('')
        print(f'Synced with response !! {requester.recv().decode()}')
    except KeyboardInterrupt:
        print("\n Interrupting  !! .... \n")
    queue.put('Request-Response connections established !!!')
    print(' -- Subscriber and Request ZMQ Connections Initialized -- ')

        
    if 'TX' in usrp_dict['type']:
        # Initialize USRP Streamer
        usrp_device._config_streamer()

        for k in range(num_runs):
            print(f'--- Capture {k} ----')
            if 'Ack' in str(subcriber.recv_string()):
            
                msg_content = subcriber.recv_pyobj()
                t1 = time.time()
                samples = usrp_device.send_samples()
                print(f'Time to capture: {(time.time()-t1)*1000} ms')
                #print(f'Time now : {(datetime.now().microsecond)/1000}')
                logging.info(f'{usrp_device.usrp_id} capture at: {(datetime.now().microsecond)/1000}')
                # Send IQ samples as response
                requester.send_pyobj(np.zeros([int(usrp_dict["no_channels_per_usrp"]),num_samps]))
                
                requester.recv()
                print(f'Latency {int(msg_content)}: {(time.time()-t1)*1000} ms')
                
            else:
                subcriber.close()
                requester.close()
                break
        
        logging.info('Done Transmitting')
        
    else:
        if 'USRP' in usrp_dict['name']:
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
        elif 'PArray' in usrp_dict['name']:
            sn_id = usrp_dict['array']
            #save_file = f'{usrp_id}.dat'
            # Initialize Array
            my_Array = Array(sn_id)
            my_Array.initialize_Array(62.64e9)
            print(' -- Siver Array: Initialized -- ')
            queue.put(f'{sn_id} initialized')
            beams_pwrs = np.zeros((num_runs, 63))
            
            for k in range(num_runs):
                print(f'--- Capture {k} ----')
                if 'Ack' in str(subcriber.recv_string()):
                    msg_content = subcriber.recv_pyobj()
                    t1 = time.time()
                    sweep_idx = int(msg_content)
                    my_Array.start_Sweep()
                    
                    # Beam Sweeping
                    for beam_dir in np.arange(1,64):
                        t1 = time.time()
                        my_Array.set_dir(beam_dir)
                        samples = usrp_device.capture_samples(num_samps)
                        print(f'Time to set : {(time.time()-t1)*1000} ms')
                        
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

        
def publisher_zmq(local_ip,num_conns,num_capture,no_samples,robot_status):
    
    logging.basicConfig(filename='logFile.log',level=logging.INFO, 
                        format='%(asctime)s : %(processName)s : %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p'
                        )
    
    zmq_obj = createZMQ(local_ip)
    if robot_status == 'yes':
        robot_client = Robot_Interface('127.0.0.1', 9999)
    ## Initialize ZMQ
    publiser = zmq_obj.createPublisher(9993)
    responder = zmq_obj.createREP(9994)
    channels  = 2
    recv_data = np.zeros((num_capture,channels,no_samples),dtype=np.complex64)
    estObj = Estimator(numberSubCarriers=64, numberOFDMSymbols=2, modOrder=16)
    
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
    
    
    for i in range(num_capture):
        tx = time.time()
        publiser.send_string("Ack", flags=zmq.SNDMORE)
        #robot_client.send('Hello')
        publiser.send_pyobj(i)
        print('send both')
        
        ## Receive IQ samples from each subscriber
        subscribers_in = 0
        IQ =[]
        while subscribers_in  < num_conns:
            t_1 = time.time()
            data_recv = responder.recv_pyobj()
            #recv_data[i,subscribers_in,:]
            
            IQ.append(data_recv)
            print(f' Print shape : {data_recv.shape}')
            subscribers_in += 1
            responder.send(b'')
            print(f'Time to receive 1 subscriber: {(time.time()-t_1)*1000} ms')
            
        print(f'Delay : {(time.time()- tx)*1000} ms')
        recv_data[i] = IQ[0]
        #recv_data[i] = np.vstack((IQ[0],IQ[1]))
        
        #estObj.Rx_processing(recv_data[i])
        sc.savemat(f'sub6_iq_{i}.mat',{'data':recv_data[i]})
        
       
    print("Data Captution Done !!!")
    publiser.send_string("close", flags=zmq.SNDMORE)
    publiser.close()
    responder.close()
    
