# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 21:13:14 2023

@author: osman
"""
import sys
sys.path.insert(1, './scripts')
from  multiprocessing import Process,Queue
from configparser import ConfigParser
from my_functions import publisher_zmq,subscriber_zmq


import logging
import time
import scipy.io as sc


if __name__ == "__main__":
    
    #global logging
    logging.basicConfig(filename='./files_req/logFile.log', filemode='w', level=logging.DEBUG)
    config = ConfigParser()
    
    
    config.read('my_self.ini')  
    capture_config = config['capture']
    
    num_conns,no_samples,num_capture =  int(capture_config['num_conns']), \
                                        int(capture_config['no_samples']), \
                                        int(capture_config['num_capture'])
    no_samples = no_samples * 10
    local_ip = capture_config['ip']
    robot_client = str(capture_config['robot'])
    
    transmit_waveform = sc.loadmat("./files_req/OFDM_packet_upsample_x2.mat")['tx_vec_air_A'] 
    
    processes = []
    queue = Queue()
    
    message = input(" -> ")  # take input
    while message.lower().strip() != 'bye':        
        # Start Publisher Process
        p_pub = Process(name='Publisher',target=publisher_zmq, args=(local_ip,num_conns,num_capture,no_samples,robot_client,))
        p_pub.start() 
        print('Publisher Script Started !!')
        time.sleep(1)
        for i in range(num_conns):
            usrp_configData = config[f'Device{i}']
            p = Process(name=f'Subscriber{i}',target=subscriber_zmq, args=(local_ip,usrp_configData,no_samples,num_capture,queue,))
            p.start()
            print(queue.get())
            processes.append(p)
            print('Subcriber !!!')
        
        
        
        for p in processes:
            print(queue.get())
            p.join()
        p_pub.join()
        print('Processes Closed !!')
        message = input(" -> ")  # take input
    
