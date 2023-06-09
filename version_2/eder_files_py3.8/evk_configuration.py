import os

class EvkConfiguration(object):
    
    
    def __init__(self):
        self.abs_dirname = os.path.dirname(os.path.abspath(__file__))

    def get_main_path(self):
        return self.abs_dirname

    def get_beambook_path(self):
        return self.abs_dirname + '/lut/beambook'

    def get_alc_path(self):
        return self.abs_dirname + '/lut/vco'

    def get_config_path(self):
        return self.abs_dirname + '/config'

