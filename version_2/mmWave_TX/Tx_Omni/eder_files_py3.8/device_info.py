# List of used attributes
# chip_type     : 'Eder B' or 'Eder B MMF'
# rfm_type      : 'BFM06010', 'BFM06005', 'BFM06009' or 'BFM06012'
# rx_power_mode : 'low' or 'normal'
# tx_power_mode : 'low' or 'normal'

class DeviceInfo(object):

    __instance = None

    __product_id_table = {'BFM06010' : 'BFM06010',
                          'BFM06011' : 'BFM06010',
                          'BFM06009' : 'BFM06009',
                          'BFM06012' : 'BFM06012',
                          'BFM06015' : 'BFM06015',
                          'BFM06016' : 'BFM06016'}

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(DeviceInfo, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
    
    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import evk_logger
        self.device_info = {}
        self.logger = evk_logger.EvkLogger()

    def get_attrib(self, attribute=None):
        if attribute != None:
            try:
                value = self.device_info[attribute]
            except:
                value = None
            return value
        else:
            return self.device_info

    def set_attrib(self, attribute, value):
        self.logger.log_bold('{0}: {1}'.format(attribute, value), 2)
        self.device_info[attribute] = value

    def product_id_2_rfm_type(self, product_id):
        try:
            rfm_type = self.__product_id_table[product_id]
        except:
            rfm_type = None
        return rfm_type

