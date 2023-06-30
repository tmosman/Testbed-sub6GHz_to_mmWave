# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 21:13:14 2023
Updated on June 9, 2023
@author: Tawfik Osman

"""
from  multiprocessing import Process,Queue
from configparser import ConfigParser
from main_functions import publisher_zmq,subscriber_zmq
import os
import logging
import time
import matplotlib.pyplot as plt
import ast


if __name__ == "__main__":
    ## global logging
    logging.basicConfig(filename='./config/logFile.log', filemode='w', level=logging.DEBUG)
    config = ConfigParser()
    
    ## load config file
    selectAPI = True  ## True --> gnuradio, else: uhd
    if selectAPI:
        config.read('./config/gnuradio_config_mmW.ini')   
    else:
        config.read('./config/uhd_config.ini')
 
    capture_config = config['capture']
    num_conns =  int(capture_config['num_conns'])
    
    ## create directory for IQ logging
    '''
    save_dir = ast.literal_eval(capture_config['save_dir'])
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    if not os.path.exists(save_dir+'/usrp1'):
        os.mkdir(save_dir+'/usrp1')
    if not os.path.exists(save_dir+'/usrp2'):
        os.mkdir(save_dir+'/usrp2')
        '''
    
 
    ## Start Processes !!!
    message = input(" -> ")  # take input
    processes = []
    queue = Queue()
    while message.lower().strip() != 'bye':
        for loc in range(1):
            save_dir = ast.literal_eval(capture_config['save_dir'])+f'{loc}'
            if not os.path.exists(save_dir):
                os.mkdir(save_dir)
            '''
            if not os.path.exists(save_dir+'/usrp1'):
                os.mkdir(save_dir+'/usrp1')
            if not os.path.exists(save_dir+'/usrp2'):
                os.mkdir(save_dir+'/usrp2')  
            '''
                 
            ## Start Publisher Process
            p_pub = Process(name='Publisher',target=publisher_zmq, args=(capture_config,save_dir,))
            p_pub.start() 
            time.sleep(1)
            print('Publisher Script Started !!')
            
            
            for i in range(num_conns):
                usrp_configData = config[f'Device{i}']
                p = Process(name=f'Subscriber{i}',target=subscriber_zmq, args=(usrp_configData,capture_config,queue,save_dir,))
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
        
