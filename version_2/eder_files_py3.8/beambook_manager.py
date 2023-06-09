import os
import xml.sax
import xml.etree.ElementTree as ET
import evk_configuration

class BeambookManager(object):
    def __init__(self, beambook_folder=None):
        if beambook_folder == None:
            evk_config = evk_configuration.EvkConfiguration()
            self.beambook_folder = evk_config.get_beambook_path() + '/'
        else:
            self.beambook_folder = beambook_folder
        self.beambook_index = []
        self.selected_beambook_index = -1
        self.subscribers = []

    def create_beambook_index_entry(self, file_name, date_generated, desc, version, beambook_type, module_types, supported_freq, azimuth_data, elevation_data, num_of_tables):
        beambook_index_entry = {'file_name': file_name, 'date': date_generated, 'desc': desc, 'version': version, 'beambook_type': beambook_type, 'module_types': module_types, 
                                'supported_freq_mhz': supported_freq, 'azimuth_data': azimuth_data, 'elevation_data': elevation_data, 'num_of_tables': num_of_tables, 'selected':''}
        self.beambook_index.append(beambook_index_entry)

    def get_compatible_beambook_index_numbers(self, module_type, beambook_type, sort_beambooks=False):
        compatible_beambook_index_numbers = []
        compatible_beambook_index_version_numbers = []
        module_type = module_type.upper()
        beambook_type = beambook_type.upper()
        for beambook_index_number in range(0, len(self.beambook_index)):
            if module_type == 'ALL':
                if (self.beambook_index[beambook_index_number]['beambook_type'] == beambook_type):
                    compatible_beambook_index_numbers.append(beambook_index_number)
                    compatible_beambook_index_version_numbers.append(self.beambook_index[beambook_index_number]['version'])
            else:
                if (self.beambook_index[beambook_index_number]['beambook_type'] == beambook_type) and (module_type in self.beambook_index[beambook_index_number]['module_types']):
                    compatible_beambook_index_numbers.append(beambook_index_number)
                    compatible_beambook_index_version_numbers.append(self.beambook_index[beambook_index_number]['version'])
        if sort_beambooks:
            # Sort beambooks based on version
            compatible_beambook_index_numbers = [x for _,x in sorted(zip(compatible_beambook_index_version_numbers, compatible_beambook_index_numbers), reverse=True)]

        return compatible_beambook_index_numbers

    def read_file_content(self, file_name):
        with open(file_name, 'r') as file:
            file_content_lines = file.readlines()
        file_content = ''
        for line in file_content_lines:
            if not (line.startswith('#') or line.startswith('const') or line.startswith('{') or line.startswith('};')):
                file_content += line
        file_content = file_content.replace('/*', '').replace('*/','')
        return file_content

    def get_beambook_supported_frequencies(self, index):
        return self.beambook_index[index]['supported_freq_mhz']

    def get_beam_number(self, index, freq_mhz, azimuth_deg, elevation_deg):
        beam_info = self.get_beam(index, freq_mhz)['info']
        for beam_counter in range(0, len(beam_info)):
            if beam_info[beam_counter][1] != 'OMNI':
                if abs(float(beam_info[beam_counter][1]) - azimuth_deg) < 0.5:
                    if abs(float(beam_info[beam_counter][2]) - elevation_deg) < 0.5:
                        return int(beam_info[beam_counter][0])
            else:
                if azimuth_deg == 'OMNI':
                    return int(beam_info[beam_counter][0])
        return None

    def get_beam(self, index, freq_mhz, beam_number='all'):
        beam = {}
        skip_to_next_table = False
        beam_section_started = False
        get_next_beam_data = False
        hexstr2int = lambda hex_str : int(hex_str,16)
        try:
            file_content = self.read_file_content(self.beambook_index[index]['file_name'])
            file_content_xml = ET.fromstring(file_content)
            for table_tags in file_content_xml.iter('TABLE'):
                for table in table_tags:
                    if skip_to_next_table:
                        skip_to_next_table = False
                        break
                    if table.tag == 'TABLE_DESC':
                        if beam_section_started:
                            return beam
                        beam['table_desc'] = table.text
                    elif table.tag == 'FREQ_MHZ':
                        try:
                            freq = int(table.text.strip())
                            if freq == freq_mhz:
                                beam['freq_mhz'] = freq
                                beam['info'] = []
                                beam['data'] = []
                            else:
                                beam['table_desc'] = ''
                                skip_to_next_table = True
                        except ValueError:
                            #print ('Error: Table frequency: {}'.format(table.text.strip()))
                            pass
                    elif table.tag == 'BEAM':
                        beam_section_started = True
                        for beam_tags in table:
                            if beam_tags.tag == 'INFO':
                                beam_info = beam_tags.text.split()
                                if beam_number == 'all':
                                    beam['info'].append(beam_info)
                                else:
                                    if beam_info[0] == str(beam_number):
                                        beam['info'] = beam_info
                                        get_next_beam_data = True
                            elif beam_tags.tag == 'DATA':
                                if beam_number == 'all':
                                    data = beam_tags.text.replace('{', '').replace('}','').replace(',','')
                                    data = data.split()
                                    data = list(map(hexstr2int, data))
                                    beam['data'].append(data)
                                else:
                                    if get_next_beam_data:
                                        data = beam_tags.text.replace('{', '').replace('}','').replace(',','')
                                        data = data.split()
                                        data = list(map(hexstr2int, data))
                                        beam['data'].append(data)
                                        return beam
                                
                        
        except IndexError:
            print ('Error: No such beambook index')
            return None
        return beam

    def list_beambooks(self, module_type='all', beambook_type='all'):
        print ('{}{:>14}{:>24}{:>42}{:>36}{:>13}'.format('No.', 'Beambook type', 'Supported module types', 'Supported freq [MHz]', 'Version', 'File name'))
        print ('{}{:>14}{:>24}{:>42}{:>36}{:>13}'.format('---', '-------------', '----------------------', '--------------------', '-------', '---------'))
        rx_beambooks = []
        tx_beambooks = []
        if beambook_type == 'all' or beambook_type == 'RX':
            rx_beambooks = self.get_compatible_beambook_index_numbers(module_type, 'RX')

        if beambook_type == 'all' or beambook_type == 'TX':
            tx_beambooks = self.get_compatible_beambook_index_numbers(module_type, 'TX')

        beambooks = rx_beambooks + tx_beambooks
        for beambook_num in beambooks:
            beambook_type_str_len = len(self.beambook_index[beambook_num]['beambook_type'])
            module_types_str_len = len(str(self.beambook_index[beambook_num]['module_types']))
            supported_freq_mhz_str_len = len(str(self.beambook_index[beambook_num]['supported_freq_mhz']))
            version_str_len = len(self.beambook_index[beambook_num]['version'])
            file_name_str_len = len(self.beambook_index[beambook_num]['file_name'])
            print ('{}{}{}{}{}{}{}{}{}{}{}{}'.format(beambook_num, \
                                           ' '*(3), \
                                           self.beambook_index[beambook_num]['beambook_type'], \
                                           ' '*(15-beambook_type_str_len), \
                                           self.beambook_index[beambook_num]['module_types'],  \
                                           (44 - module_types_str_len)*' ', \
                                           self.beambook_index[beambook_num]['supported_freq_mhz'],  \
                                           (49 - supported_freq_mhz_str_len)*' ', \
                                           self.beambook_index[beambook_num]['version'], \
                                           (11-version_str_len)*' ', \
                                           self.beambook_index[beambook_num]['file_name'], \
                                           (40 - file_name_str_len)*' '))


    def create_beambook_index(self, select_beambook_type):
        self.beambook_index = []
        list_path = os.listdir(self.beambook_folder)
        for file_name in list_path:
            if file_name.endswith('.h'):
                file_content = self.read_file_content(self.beambook_folder + file_name)
                file_content_xml = ET.fromstring(file_content)
                #children = file_content_xml.getchildren()
                #print (children)
                beambook_file_name = self.beambook_folder + file_name
                for beambook_meta_data_tags in file_content_xml.iter('BEAMBOOK'):
                    for beambook_meta_data in beambook_meta_data_tags:
                        if beambook_meta_data.tag == 'DATE_GENERATED':
                            date_generated = beambook_meta_data.text.strip()
                        elif beambook_meta_data.tag == 'DESCRIPTION':
                            desc = beambook_meta_data.text.strip()
                        elif beambook_meta_data.tag == 'VERSION':
                            version = beambook_meta_data.text.strip()
                        elif beambook_meta_data.tag == 'BEAMBOOK_TYPE':
                            beambook_type = beambook_meta_data.text.strip().upper()
                        elif beambook_meta_data.tag == 'MODULE_TYPES':
                            module_types = beambook_meta_data.text.strip().split(',')
                            for i in range(0, len(module_types)):
                                module_types[i] = module_types[i].upper().strip()
                        elif beambook_meta_data.tag == 'SUPPORTED_FREQ_MHZ':
                            supported_freq = beambook_meta_data.text.strip().split(',')
                            supported_freq = list(map(int, supported_freq))
                        elif beambook_meta_data.tag == 'NUMBER_OF_TABLES':
                            num_of_tables = int(beambook_meta_data.text.strip())
                        elif beambook_meta_data.tag == 'AZIMUTH_DATA':
                            azimuth_data = beambook_meta_data.text.strip().split(',')
                            azimuth_data = list(map(float, azimuth_data))
                        elif beambook_meta_data.tag == 'ELEVATION_DATA':
                            elevation_data = beambook_meta_data.text.strip().split(',')
                            elevation_data = list(map(float, elevation_data))
                    if select_beambook_type == beambook_type:
                        self.create_beambook_index_entry( os.path.relpath(beambook_file_name),
                                                          date_generated,
                                                          desc,
                                                          version,
                                                          beambook_type,
                                                          module_types,
                                                          supported_freq,
                                                          azimuth_data,
                                                          elevation_data,
                                                          num_of_tables)

    def get_azimuth_range(self, index):
        try:
            return self.beambook_index[index]['azimuth_data']
        except:
            return None

    def get_elevation_range(self, index):
        try:
            return self.beambook_index[index]['elevation_data']
        except:
            return None

    def subscribe(self, call_back_func):
        self.subscribers.append(call_back_func)

    def set_selected_beambook(self, index):
        if index > (len(self.beambook_index) - 1):
            print ('Beambook with index {} not found'.format(index))
            return
        try:
            if self.selected_beambook_index != -1:
                self.beambook_index[self.selected_beambook_index]['selected'] = ''
            self.selected_beambook_index = index
            self.beambook_index[self.selected_beambook_index]['selected'] = 'Yes'
            for n in range(0,len(self.subscribers)):
                self.subscribers[n](False)
        except IndexError:
            print ('Beambook selection with index {} failed'.format(index))

    def get_selected_beambook(self):
        if self.selected_beambook_index == -1:
            return None
        return self.selected_beambook_index


if __name__ == "__main__":
    import beambook_manager
    bbp = beambook_manager.BeambookManager()
