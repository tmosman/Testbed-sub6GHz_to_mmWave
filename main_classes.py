# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 11:41:58 2022

@author: osman
"""

import uhd
import time
import numpy as np
import zmq
import socket
from configparser import ConfigParser
import sys
sys.path.insert(1, './eder_files_py3.8')
from eder import Eder
from gnuradio import blocks
from gnuradio import gr
from gnuradio import uhd as grUHD
#from datetime import datetime
import scipy.io as sc


class usrpUHD:
    def __init__(self, config_data):
        self.deviceInfo = config_data
        self.usrp_id = self.deviceInfo["id"]
        self.channels = list(range(int(self.deviceInfo["no_channels_per_usrp"])))
        self.sample_rate = float(self.deviceInfo["sampleRate"])
        self.gain = int(self.deviceInfo["gain"])
        self.type = str(self.deviceInfo["type"])
        self.duration = float(self.deviceInfo["tx_duration"])
        
        
        self.center_freq = uhd.libpyuhd.types.tune_request(float(self.deviceInfo["centerFreq"]))
        self.usrp_trx = uhd.usrp.MultiUSRP(f'mboard_serial={self.usrp_id}')
        
        
        ## Tune the RF front-end of the USRP
        self.config_usrp()
        
        ## configure streamer
        self._config_streamer
        
 
    def config_usrp(self):
        try:
            print(f'[Number Channels] : {self.deviceInfo["no_channels_per_usrp"]}')
            self.st_args = uhd.usrp.StreamArgs("fc32", "sc16")
            self.st_args.channels = self.channels
            
            for channel_index in self.channels:
                self.usrp_trx.set_rx_rate(self.sample_rate, channel_index)
                self.usrp_trx.set_rx_bandwidth(self.sample_rate, channel_index)
                self.usrp_trx.set_rx_freq(self.center_freq, channel_index)
                self.usrp_trx.set_rx_gain(self.gain, channel_index)
                if 'TX' in str(self.deviceInfo["rf_port"]):
                    self.usrp_trx.set_rx_antenna('TX/RX', channel_index)
                else:
                     self.usrp_trx.set_rx_antenna('RX2', channel_index)  
                     
            print(f'Clock Source {self.deviceInfo["clock"]}')
            
            if 'in' in str(self.deviceInfo["clock"]):
                print('pass')
                self.usrp_trx.set_clock_source('internal')
                self.usrp_trx.set_time_source('internal')
            else:
                self.usrp_trx.set_clock_source('external')
                self.usrp_trx.set_time_source('external')
                self._setup_pps()
                
                
            
            print(f'USRP {self.usrp_id} initialiazed !!! ')
            
        except RuntimeError:  
            self.config_usrp()
    
    def _setup_pps(self):
        # Wait for 1 PPS to happen, then set the time at next PPS to 0.0
        time_at_last_pps = self.usrp_trx.get_time_last_pps().get_real_secs()
        while time_at_last_pps == self.usrp_trx.get_time_last_pps().get_real_secs():
            time.sleep(0.1) # keep waiting till it happens- if this while loop never finishes then the PPS signal isn't there
        self.usrp_trx.set_time_next_pps(uhd.libpyuhd.types.time_spec(0.0))
        
        
    def _config_streamer(self):
        """
        Set up the correct streamer
        """ 
        
        if 'TX' in self.type:
            self.metadata =  uhd.types.TXMetadata()
            self.streamer = self.usrp_trx.get_tx_stream(self.st_args)
            self.tx_path = self.deviceInfo["path"]
            print('Tx init -----')
        else:
            self.metadata =  uhd.types.RXMetadata()
            self.streamer = self.usrp_trx.get_rx_stream(self.st_args)
        return self.streamer
    
       
    def _start_stream(self):
        """
        Issue the start-stream command.
        """
        # stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
        # stream_cmd.num_samps = num_to_done
        if 'RX' in self.type:
            stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
            stream_cmd.stream_now = (len(self.channels) == 1)
            if not stream_cmd.stream_now:
                #stream_cmd.time_spec = uhd.libpyuhd.types.time_spec(3.0) # set start time (try tweaking this)
                time_set = self.usrp_trx.get_time_now().get_real_secs() + 0.05
                stream_cmd.time_spec = uhd.libpyuhd.types.time_spec(time_set)
                
                print(f'The time set at: {time_set}')
            self.streamer.issue_stream_cmd(stream_cmd)
        else:
            # Now stream
            #if start_time is not None:
            time_set = self.usrp_trx.get_time_now().get_real_secs() + 0.05
            self.metadata.time_spec = uhd.libpyuhd.types.time_spec(time_set)
            #stream_cmd.time_spec = uhd.libpyuhd.types.time_spec(time_set)
            #print('')
        return 1
    
    
    def _stop_stream(self):
        """
        Issue the stop-stream command and flush the queue.
        """
        recv_buffer = np.zeros(
            (len(self.channels), self.streamer.get_max_num_samps()), dtype=np.complex64)
        tx = time.time()
        metadata = uhd.types.RXMetadata()     
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
        self.streamer.issue_stream_cmd(stream_cmd)
        #print(streamer.recv(recv_buffer, metadata))
        while self.streamer.recv(recv_buffer, metadata):
            pass
        print(f'Time Meta : {(time.time()-tx)*1000} ms')
        
        
    def capture_samples(self,num_samps):
        self._start_stream()
        # Set up buffers and counters
        result = np.empty((len(self.channels), num_samps), dtype=np.complex64)
        recv_buffer = np.zeros(
            (len(self.channels), self.streamer.get_max_num_samps()), dtype=np.complex64)
        recv_samps,samps  = 0,0
    
        while recv_samps < num_samps:
            samps = self.streamer.recv(recv_buffer, self.metadata)
            if self.metadata.error_code != uhd.types.RXMetadataErrorCode.none:
                print(self.metadata.strerror())
            if samps:
                real_samps = min(num_samps - recv_samps, samps)
                result[:, recv_samps:recv_samps + real_samps] = \
                            recv_buffer[:, 0:real_samps]
                recv_samps += real_samps
    
        print(' Capture Done !! ')
    
        # Stop and clean up
        self._stop_stream()
        
        return result
    
    
    def send_samples(self):
        self._start_stream()
        waveform_proto = sc.loadmat(self.tx_path)['tx_vec_air_A']
        # Set up buffers and counters
        buffer_samps = self.streamer.get_max_num_samps()
        proto_len = waveform_proto.shape[-1]
        if proto_len < buffer_samps:
            waveform_proto = np.tile(waveform_proto,
                                     (1, int(np.ceil(float(buffer_samps)/proto_len))))
            proto_len = waveform_proto.shape[-1]
        send_samps = 0
        max_samps = int(np.floor(self.duration * self.sample_rate))
        if len(waveform_proto.shape) == 1:
            waveform_proto = waveform_proto.reshape(1, waveform_proto.size)
        if waveform_proto.shape[0] < len(self.channels):
            waveform_proto = np.tile(waveform_proto[0], (len(self.channels), 1))
        
        while send_samps < max_samps:
            real_samps = min(proto_len, max_samps-send_samps)
            if real_samps < proto_len:
                #print(waveform_proto[:, :real_samps])
                samples = self.streamer.send(waveform_proto[:, :real_samps], self.metadata)
            else:
                samples = self.streamer.send(waveform_proto, self.metadata)
            send_samps += samples
        
        # Send EOB to terminate Tx
        self.metadata.end_of_burst = True
        self.streamer.send(np.zeros((len(self.channels), 1), dtype=np.complex64), self.metadata)
        # Help the garbage collection
        #streamer = None
        print(' Transmission Done !! ')
    
        # Stop and clean up
        #self._stop_stream()
        #print(send_samps)
        return send_samps
        
class createZMQ:
    def __init__(self,ip_add):
        self.ctx = zmq.Context()
        self.local_ip =ip_add
        
        pass
    
    def createPublisher(self,port):
        self.zmq_pub = self.ctx.socket(zmq.PUB)
        self.zmq_pub.bind(f"tcp://{self.local_ip}:{port}")
        
        return self.zmq_pub
    
    def createSubcriber(self,port):
        self.zmq_sub = self.ctx.socket(zmq.SUB)
        self.zmq_sub.connect(f"tcp://{self.local_ip}:{port}")
        self.zmq_sub.setsockopt_string(zmq.SUBSCRIBE, '')
        return self.zmq_sub
    
    
    def createREQ(self,port):
        self.zmq_req = self.ctx.socket(zmq.REQ)
        self.zmq_req.connect(f"tcp://{self.local_ip}:{port}")
        return self.zmq_req
    
    
    def createREP(self,port):
        self.zmq_rep = self.ctx.socket(zmq.REP)
        self.zmq_rep.bind(f"tcp://{self.local_ip}:{port}")
        return self.zmq_rep
    
    def subsc_usrp(self,usrp_device,num_samps,num_runs,queue):
        if '31' in usrp_device.usrp_id:
            
            # Initialize USRP
            usrp_device._config_streamer()
            
            # ZMQ Sockets
            subcriber = self.createSubcriber(9993)
            requester = self.createREQ(9994)
            print(' -- Publish and Request ZMQ Connections Initialized -- ')
            
            #queue.put(f'{usrp_device.usrp_id} initialized')  # Signal to continue initialization
            print(f'checking  !!! {usrp_device.capture_samples(num_samps)}')
                
            try:
                # Sync 
                requester.send_string('') 
                message = requester.recv()
                        
            #     for k in range(num_runs):
            #         if 'Ack' in str(subcriber.recv_string()):
            #             _,msg_content = subcriber.recv_string(),subcriber.recv_pyobj()
            #             #print('Receive from Pub !!')
            #             t1 = time.time()
            #             samples = usrp_device.capture_samples(num_samps)
            #             print(f'Time to capture: {(time.time()-t1)*1000} ms')
            #             print((datetime.now().microsecond)/1000)
                            
            #             #data[int(msg_content),:] = samples
            #             print("Captured IQ Samples !!")
                        
                        
            #             # Send IQ samples as response
            #             requester.send_pyobj(samples)
            #             requester.recv()
                        
            #             print(f'Latency {int(msg_content)}: {(time.time()-t1)*1000} ms')
                    
            #         else:
            #             subcriber.close()
            #             requester.close()
            #             break
            except KeyboardInterrupt:
                print("\n Interrupting  !! .... \n")
            #queue.put(f'{usrp_device.usrp_id} Done')
    
    def publish(self,num_conns,num_capture,no_samples):
    
        ## Initialize ZMQ
        publiser = self.createPublisher(9993)
        responder = self.createREP(9994)
        
        recv_data = np.zeros((num_capture,4,no_samples),dtype=np.complex64)
        #print(recv_data)
        
        print("Finding Subscribers Devices")
        subscribers = 0
        while subscribers < num_conns:
            # Wait for syncronization request
            msg = responder.recv()
            responder.send(b"Ack")
            subscribers += 1
            print("Found {} satellites".format(subscribers))
        time.sleep(1)
        
        
        
        # print(zmq_pub.closed,zmq_rep.closed)
        print('Done Searching')
        
        t_start = time.time()
        # for i in range(num_capture):
        #     tx = time.time()
        #     publiser.send_string("Ack", flags=zmq.SNDMORE)
        #     publiser.send_pyobj(i)
        #     print('send both')
            
        #     ## Receive IQ samples from each subscriber
        #     subscribers_in = 0
        #     IQ =[]
        #     while subscribers_in  < num_conns:
        #         t_1 = time.time()
        #         data_recv = responder.recv_pyobj()
        #         IQ.append(data_recv)
        #         subscribers_in += 1
        #         responder.send(b'')
        #         print(f'Time to receive 1 subscriber: {(time.time()-t_1)*1000} ms')
                
        #     print(f'Delay : {(time.time()- tx)*1000} ms')
        #     recv_data[i] = np.vstack((IQ[0],IQ[1]))
        #     #sc.savemat(f'./Jan_22nd_IQ/Row{row}/sub6_iq_{i}.mat',{'data':recv_data[i]})
           
        print("All Acks Sent")
        publiser.send_string("close", flags=zmq.SNDMORE)
        publiser.close()
        responder.close()
        print(f'Total Elapse Time : {time.time()- t_start} seconds')
    pass       
 
class Array(Eder):
    def __init__(self,sn_id):
        Eder.__init__(self, unit_name=sn_id)
              
       
    def initialize_Array(self, freq):
        self.rx_setup(float(freq))
        self.rx_enable()
        return 1
        
        
    def start_Sweep(self):
        self.rx.set_beam(0)
        self.rx.bf.idx.set(0)
        self.rx.bf.idx.rst()
        return 1
        
    
    def set_Increment(self, direction):
        #self.ue.rx.set_beam(int(direction))
        self.rx.bf.idx.inc()
        return 1
    
    
    def disable(self):
        self.rx_disable()
        return 1

class usrpGNURadio(gr.top_block):
    def __init__(self,usrp_id,center_freq,samp_rate,channels,gain):
        gr.top_block.__init__(self, "BS_RX")
        # Variables
        self.samp_rate = samp_rate
        self.center_freq = center_freq
        self.gain = gain
        self.channels = channels
        self.usrp_id = usrp_id

        # File Source Block
        self.save_file = './measured_signals.dat'
        self.blocks_streams_to_vector = blocks.streams_to_vector(gr.sizeof_gr_complex, len(self.channels))
        self.blocks_file_sink = blocks.file_sink(gr.sizeof_gr_complex, self.save_file, False)
        self.blocks_file_sink.set_unbuffered(False)
        
        # USRP Blocks
        self.usrp_rx = None
        self.init_usrp(self.usrp_id)
    
    def init_usrp(self,device):
        try:
            self.usrp_rx = grUHD.usrp_source(
                ",".join(("serial=" + device, "")),
                uhd.stream_args(
                    cpu_format="fc32",
                    otw_format="sc16",
                    channels=range(len(self.channels)),
                ),
            )
            for i in self.channels:
                self.usrp_rx.set_samp_rate(self.samp_rate)
                self.usrp_rx.set_center_freq(self.center_freq, i)
                self.usrp_rx.set_gain(self.gain, i)
                self.usrp_rx.set_antenna('TX/RX', i)
                self.usrp_rx.set_bandwidth(self.samp_rate, i)
                self.usrp_rx.set_auto_dc_offset(True, i)
                self.usrp_rx.set_auto_iq_balance(True, i)
                self.connect((self.usrp_rx, i), (self.blocks_streams_to_vector, i))
                self.connect((self.blocks_streams_to_vector, i),(self.blocks_file_sink, i))
        except RuntimeError:
            self.init_usrp(device)
    
    def open_file(self,save_file):
        self.save_file = save_file
        self.blocks_file_sink.open(save_file)
    
    def close_file(self):
        self.blocks_file_sink.close()

class Robot_Interface():

    # Initiate client
    def __init__(self, host_ip, port):
        self.active = False
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host_ip = host_ip
        self.port = port
        
    # Connect to server
    def send(self,text):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        recieved = ''
        try:
            self.client.connect((self.host_ip,self.port))
            self.client.sendall(text.encode())

            recieved = self.client.recv(1024).decode()

            while recieved != 'ACK':
                time.sleep(0.1)
                recieved = self.client.recv(1024).decode()
            
        finally:
            self.client.close()

        if recieved == 'ACK':
            time.sleep(0.1)
            print(f'Ack from Robot Server -: {recieved}' )
            return 1
        else:
            return 0

if __name__ == "__main__":
    config = ConfigParser()
    config.read('my_self.ini')
    config_data = config['Device']
    usrp = usrpUHD(config_data)
    print('Hello World !!')
