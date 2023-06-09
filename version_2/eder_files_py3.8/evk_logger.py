import logging
import colorama

class FontColors:
    HEADER    = '\033[95m'
    OKBLUE    = '\033[94m'
    OKGREEN   = '\033[92m'
    DEBUG     = '\033[94m'
    WARNING   = '\033[93m'
    FAIL      = '\033[91m'
    CRITICAL  = '\033[91m'
    ENDC      = '\033[0m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'

class EvkLogger(object):

    import readline

    __instance = None

    def __new__(cls, fname='evk.info', indent=0):
        if cls.__instance is None:
            cls.__instance = super(EvkLogger, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, fname='evk.info', indent=0):
        if self.__initialized:
            return
        colorama.init(autoreset=True)
        self._indent = indent
        self._last_hist_item_idx = self.readline.get_current_history_length()
        self._logger = logging.getLogger('evk_logger')
        self._logger.setLevel(logging.DEBUG)
        self._fh = logging.FileHandler(fname)
        self._fh.setLevel(logging.DEBUG)
        self._ch = logging.StreamHandler()
        self._ch.setLevel(logging.INFO)
        file_format = logging.Formatter('%(asctime)s %(levelname)-5s: %(message)s')
        scr_format = logging.Formatter('%(message)s')
        self._ch.setFormatter(scr_format)
        self._fh.setFormatter(file_format)
        self._logger.addHandler(self._ch)
        self._logger.addHandler(self._fh)
        self.__initialized = True

    def log_info(self, message, indentation=None):
        if indentation == None:
            indentation = self._indent
        self._log_cmd_hist() 
        self._logger.info(' '*indentation + str(message))

    def log_bold(self, message, indentation=None):
        if indentation == None:
            indentation = self._indent
        self._log_cmd_hist() 
        self._logger.info(' '*indentation + colorama.Style.BRIGHT + str(message))

    def log_warning(self, message, indentation=None):
        if indentation == None:
            indentation = self._indent
        self._log_cmd_hist()
        self._logger.warning(' '*indentation + colorama.Style.BRIGHT + colorama.Fore.YELLOW + str(message))

    def log_debug(self, message, indentation=None):
        if indentation == None:
            indentation = self._indent
        self._log_cmd_hist()
        self._logger.debug(' '*indentation + colorama.Fore.BLUE + str(message))

    def log_error(self, message, indentation=None):
        if indentation == None:
            indentation = self._indent
        self._log_cmd_hist()
        self._logger.error(' '*indentation + colorama.Style.BRIGHT + colorama.Fore.RED + str(message))

    def log_critical(self, message, indentation=None):
        if indentation == None:
            indentation = self._indent
        self._log_cmd_hist()
        self._logger.critical(' '*indentation + colorama.Style.BRIGHT + colorama.Fore.RED + str(message))

    def log_header(self, message, indentation=None):
        if indentation == None:
            indentation = self._indent
        self._log_cmd_hist()
        self._logger.info(' '*indentation + colorama.Style.BRIGHT + str(message))

    def _log_cmd_hist(self):
        current_hist_length = self.readline.get_current_history_length()
        if current_hist_length > self._last_hist_item_idx:
            for index in range(self._last_hist_item_idx, current_hist_length+1):
                self._logger.debug(self.readline.get_history_item(index))
        self._last_hist_item_idx = current_hist_length

