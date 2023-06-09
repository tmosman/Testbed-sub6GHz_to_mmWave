class Awv():
    """AWV Table class
	Handles access functions to the Antenna Weight Vector Table, controls used index/row
	and associated SRAMs.
    """
    import common
    import beambook_manager
    
    RX = 0
    TX = 1
    
    START_TABLE_TAG = 'START_TABLE FREQ:'
    END_TABLE_TAG   = 'END_TABLE'
    TEMP_TAG        = 'TEMP'
    
    def __init__(self, txrx):
        import memory
        import device_info
        import evk_logger
        self._txrx = txrx
        self.bbp = self.beambook_manager.BeambookManager()
        if txrx == self.RX:
            self.bbp.create_beambook_index('RX')
        else:
            self.bbp.create_beambook_index('TX')
        self.memory = memory.Memory()
        self.device_info = device_info.DeviceInfo()
        self.logger = evk_logger.EvkLogger()
        self.active_beambook = None
        self.selected_freq = None

    def set(self, index):
        if index > 63:
            self.logger.log_info('Error: index should be between 0 and 63')
            return
        ptr = 0x80 | index
        if self._txrx == self.RX:
            self.memory.awv.wr('bf_rx_awv_ptr', ptr)
        elif self._txrx == self.TX:
            self.memory.awv.wr('bf_tx_awv_ptr', ptr)

    def set_angle(self, azimuth_deg, elevation_deg):
        selected_beambook_index = self.bbp.get_selected_beambook()
        if selected_beambook_index != None:
            beam = self.bbp.get_beam_number(selected_beambook_index, 0, azimuth_deg, elevation_deg)
            if beam != None:
                print ('Beam {}'.format(beam))
                self.set(beam)
            else:
                return False
            return True
        else:
            print ('No beambook selected.')
        return False

    def get(self):
        if self._txrx == self.RX:
            return 0x7F & self.memory.awv.rd('bf_rx_awv_ptr')
        elif self._txrx == self.TX:
            return 0x7F & self.memory.awv.rd('bf_tx_awv_ptr')

    def get_table_heads(self, fname):
        try:
            f = open(fname)
        except IOError:
            try:
                f = open('../'+fname)
            except IOError:    
                self.logger.log_error(fname + ' not found!')
                return
        tags = list()
        line = f.readline()
        while line != '':
            if line.find(self.START_TABLE_TAG) >= 0:
                tags.append(line)
            line = f.readline()
        f.close()
        return tags

    def get_freq_from_head(self, line):
        start = line.find(self.START_TABLE_TAG)+len(self.START_TABLE_TAG)
        end   = line.find(self.TEMP_TAG)
        freq  = float(line[start:end].strip())*1e9
        return freq

    def get_closest_freq_head(self, freq, heads):
        freq_sel = freq
        diff_sel = freq
        head_sel = None
        for head in heads:
            head_freq = self.get_freq_from_head(head)
            diff      = abs(freq - head_freq)
            if diff <= diff_sel:
                freq_sel = head_freq
                diff_sel = diff
                head_sel = head
        return head_sel, freq_sel, diff_sel

        
    def get_table(self, fname, tag):
        try:
            f = open(fname)
        except IOError:
            try:
                f = open('../'+fname)
            except IOError:    
                self.logger.log_error(fname + ' not found!')
                return
        line = ''
        while line[0:len(tag)] != tag:
            line = f.readline()
            if line == '':
                break
        line = f.readline()
        table = ''
        while line[0:len(self.END_TABLE_TAG)] != self.END_TABLE_TAG:
            if line == '':
                break
            table += line
            line = f.readline()
        f.close()
        return table

    def pack_bytes_2_bf_awv(self, q, i):
        pack = lambda q , i : ( ((q & 0x3f) << 6) + (i & 0x3f) )
        return pack(q,i)

    def pack_word_2_bf_awv(self, qi):
        pack = lambda qi : ( ((qi & 0x3f00) >> 2) + (qi & 0x3f) )
        return pack(qi)

    def unpack_bf_awv_2_bytes(self, data):
        return (data >> 6)&0x3f, (data & 0x3f)

    def unpack_bf_awv_2_word(self, data):
        (q,i) = self.unpack_bf_awv_2_bytes(data)
        return (q<<8) + i

    def setup(self, freq=None):
        if freq == None:
            if self.selected_freq != None:
                freq = self.selected_freq
            else:
                return
        else:
            self.selected_freq = freq
        if self._txrx == 0:
            beambook_type = 'RX'
        else:
            beambook_type = 'TX'
        module_type = self.device_info.get_attrib('rfm_type').upper()
        chip_type = self.device_info.get_attrib('chip_type').upper()
        #if module_type == 'RFM_3.0' and chip_type == 'EDER B MMF':
        #    module_type = 'RFM_3.0_2.0'

        self.active_beambook = self.bbp.get_selected_beambook()
        if self.active_beambook == None:
            # Find a suitable beambook
            compatible_beambook_index_numbers = self.bbp.get_compatible_beambook_index_numbers(module_type, beambook_type, sort_beambooks=True)
            if len(compatible_beambook_index_numbers) > 1:
                self.logger.log_warning('Multiple compatible beambooks found')
                self.logger.log_warning('Selecting first beambook')
            else:
                self.logger.log_info('Compatible beambook found')
            #self.bbp.list_beambooks(module_type, beambook_type)
            self.active_beambook = compatible_beambook_index_numbers[0]
            self.bbp.set_selected_beambook(self.active_beambook)
            # Find closest frequency
            freq = freq / 1000000
            beambook_supported_frequencies = self.bbp.get_beambook_supported_frequencies(compatible_beambook_index_numbers[0])
            diff = freq
            selected_freq = freq
            for beambook_freq in beambook_supported_frequencies:
                if diff >= abs(freq - beambook_freq):
                    diff = abs(freq - beambook_freq)
                    selected_freq = beambook_freq
            self.logger.log_info('Selected beambook for frequency {} MHz'.format(selected_freq))
        else:
            # A beambook is already selected
            # Find closest frequency
            freq = freq / 1000000
            beambook_supported_frequencies = self.bbp.get_beambook_supported_frequencies(self.active_beambook)
            diff = freq
            selected_freq = freq
            for beambook_freq in beambook_supported_frequencies:
                if diff >= abs(freq - beambook_freq):
                    diff = abs(freq - beambook_freq)
                    selected_freq = beambook_freq
            self.logger.log_info('Selected beambook for frequency {} MHz'.format(selected_freq))

        loaded_beambook = self.bbp.get_beam(self.active_beambook, selected_freq, beam_number='all')
        packed_bf_awv = []
        for beam_index in range(0, len(loaded_beambook['data'])):
            for ant_elem in range(0, len(loaded_beambook['data'][beam_index])//2):
                packed_bf_awv.append(self.pack_bytes_2_bf_awv(loaded_beambook['data'][beam_index][ant_elem*2], loaded_beambook['data'][beam_index][ant_elem*2+1]))
        intbfdata = self.common.intlist2int(packed_bf_awv,0x10000)
        if self._txrx == self.RX:
            self.memory.awv.wr('bf_rx_awv', intbfdata)
        elif self._txrx == self.TX:
            self.memory.awv.wr('bf_tx_awv', intbfdata)


    def _get_element_addr(self, index, ant):
        if index > 63 or ant > 15:
            self.logger.log_error('Error: index or ant out of range')
            return -1
        if self._txrx == self.RX:
            addr = self.memory.awv.addr('bf_rx_awv')
        elif self._txrx == self.TX:
            addr = self.memory.awv.addr('bf_tx_awv')
        addr += (index*32 + (15 - ant)*2)
        return addr


    def rd(self, index, ant):
        """Returns value at location [index,ant] of AWV table.
           Example: Reads value at index 2 antenna 4 of AWV table.
                    rd(2,4)
        """
        value = self.unpack_bf_awv_2_word(self.memory.awv.rd(self._get_element_addr(index, ant), 2))
        return value


    def wr(self, index, ant, value):
        """Writes value to location [index,ant] of AWV table.
           Example: Writes 0x1234 to index 2 antenna 4 of AWV table.
		    Antenna element 4 on row 2 will be set to Q=0x12, I=0x34.
                    wr(2,4,0x1234)
        """
        if isinstance(value,int):
            data = self.pack_word_2_bf_awv(value)
        elif isinstance(value,list) or isinstance(value,tuple):
            data = self.pack_bytes_2_bf_awv(value[0],value[1])
        elif isinstance(value,dict):
            data =  self.pack_bytes_2_bf_awv(value['q'],value['i'])
            
        self.memory.awv.wr(self._get_element_addr(index,ant), data, 2)


    def wr_row(self, index, value, type='w'):
        """Writes the specified value to a index/row in AWV table.
           Example: Write value 0x1234 to index/row 2 in the AWV table.
		    Antenna element 0 on row 2 will be set to Q=0x12, I=0x34, while all other elements
		    on row 2 will be set to Q=0x00, I=0x00.
                    wr_row(2, 0xabab)
        """
        if isinstance(value,int) or isinstance(value,long):
            print (map(hex,map(self.pack_word_2_bf_awv,self.common.int2intlist(value,2**16,16))))
            data = self.common.intlist2int(map(self.pack_word_2_bf_awv,self.common.int2intlist(value,2**16,16)),2**16)
        elif isinstance(value,list) or isinstance(value,tuple):
            if len(value) > 16:
                type = 'b'
            if (type == 'b') or (type == 8):
                self.logger.log_error("Row-writes using list/tuple with bytes not supported yet.")
                return
            else:
                data = self.common.intlist2int(map(self.pack_word_2_bf_awv,value),2**16)
        elif isinstance(value,dict):
            self.logger.log_error("Row-writes using dictionary is not supported yet")
            return

        self.memory.awv.wr(self._get_element_addr(index,15), data, 32)


    def dump(self, do_print=True):
        """
        """
        if self._txrx == self.RX:
            values = self.memory.awv.rd('bf_rx_awv')
        elif self._txrx == self.TX:
            values = self.memory.awv.rd('bf_tx_awv')
        else:
            values = None
        if do_print:
            self.logger.log_info("             -------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("             |                                              AWV_Table (Q=13:8, I=5:0))                                         |")
            self.logger.log_info("     AWV_Ptr |  15     14     13     12     11     10      9      8      7      6       5      4      3      2      1      0   |")
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            for row in range(0,64):
                row_string = '       {:{}}    |'.format(row,2)
                row_val = (values>>((63-row)*16*16))&(2**(16*16)-1)
                for col in range(0,16):
                    col_val = self.unpack_bf_awv_2_word((row_val>>((15-col)*16))&0xffff)
                    row_string += ' 0x{:0{}X}'.format(int(col_val),4)
                row_string += ' |'
                self.logger.log_info(row_string)
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("Direct AWV_Ptr : " + str(self.get()&0x3f))
        else:
            return values


    def rd_raw(self, index, ant):
        """Returns content of SRAM at location [index,ant] of AWV table.
           Example: Reads SRAM content for index 2 antenna 4 of AWV table.
                    rd_raw(2,4)
        """
        value = self.memory.awv.rd(self._get_element_addr(index, ant), 2)
        return value

    def wr_raw(self, index, ant, value):
        """Writes the specified value to SRAM at location [index,ant] of AWV Table.
           Example: Writes 0x1234 to SRAM for index 2 antenna 4 of AWV table.
                    wr_raw(2,4,0x1234) 
        """
        self.memory.awv.wr(self._get_element_addr(index, ant), value, 2)

    def dump_raw(self, do_print=True):
        """Prints and returns contents of all SRAMs of AWV Table.
        """
        if self._txrx == self.RX:
            values = self.memory.awv.rd('bf_rx_awv')
        elif self._txrx == self.TX:
            values = self.memory.awv.rd('bf_tx_awv')
        else:
            values = None
        if do_print:
            self.logger.log_info("             -------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("             |                                     SRAM for AWV_Table (Q=11:6, I=5:0)                                          |")
            self.logger.log_info("     AWV_Ptr |  15     14     13     12     11     10      9      8      7      6       5      4      3      2      1      0   |")
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            for row in range(0,64):
                row_string = '       {:{}}    |'.format(row,2)
                row_val = (values>>((63-row)*16*16))&(2**(16*16)-1)
                for col in range(0,16):
                    col_val = (row_val>>((15-col)*16))&0xffff
                    row_string += ' 0x{:0{}X}'.format(int(col_val),4)
                row_string += ' |'
                self.logger.log_info(row_string)
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("Direct AWV_Ptr : " + str(self.get()))
        else:
            return values
