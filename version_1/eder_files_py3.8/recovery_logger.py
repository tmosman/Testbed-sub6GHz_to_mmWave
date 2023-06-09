import os
import logging

class RecoveryLogger(object):

    import readline

    __instance = None

    replacement_vector = {'<__main__.Eder'     : 'eder.', 
                          '<rf_tx.Tx'          : 'eder.tx.',
                          '<rf_rx.Rx'          : 'eder.rx.',
                          '<tx_dco.TxDco'      : 'eder.tx.dco.',
                          '<register.Register' : 'eder.regs.'}

    def __new__(cls, fname='recovery.log'):
        if cls.__instance is None or fname != 'recovery.log':
            if not cls.__instance == None:
                del cls.__instance
            cls.__instance = super(RecoveryLogger, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __del__(self): 
        self._logger.removeHandler(self._fh)

    def __init__(self, fname='recovery.log'):
        if self.__initialized:
            return
        self._recovery_log_file_name = fname
        self._logger = logging.getLogger('recovery_logger')
        self._logger.setLevel(logging.INFO)
        self._fh = logging.FileHandler(fname)
        file_format = logging.Formatter('%(message)s')
        self._fh.setFormatter(file_format)
        self._logger.addHandler(self._fh)
        self._indented = False
        self.__initialized = True

    def clear(self):
        #print('CLEARING RECOVERY LOG {}'.format(self._recovery_log_file_name))
        f = open(self._recovery_log_file_name, "w")
        f.write('')
        f.close()

    def disable(self):
        pass

    def enable(self):
        pass

recovery_logger = RecoveryLogger()
recovery_file = 'recovery.log'

def create_recovery_log(fname):
    global recovery_file
    recovery_file = fname
    global recovery_logger
    recovery_logger = RecoveryLogger(fname)

def log_call(fn):
    if recovery_logger == None:
        return
    if recovery_logger._indented:
        tag = ''
    else:
        tag = ''
        recovery_logger._indented = True
    def func(*a):
        try:
            prefix = RecoveryLogger.replacement_vector[str(a[0]).split()[0]]
            recovery_logger._logger.info(tag + prefix + '%s%s', fn.__name__, a[1:])
        except:
            recovery_logger._logger.info(tag + '%s%s', fn.__name__, a)
        recovery_logger._fh.flush()
        return fn(*a)
    return func

def log_info(msg):
    recovery_logger._logger.info(msg)
    recovery_logger._fh.flush()

def log_clear(fn):
    def func(*a):
        try:
            recovery_logger.clear()
        except:
            pass
        return fn(*a)
    return func

# @log_call
# def print_x_plus_y(x, y):
#     print (x + y)

# @log_call
# def print_x_minus_y(x, y):
#     print (x - y)

# @log_call
# def print_x_plus_minus_y(x, y):
#     print_x_plus_y(x, y)
#     print_x_minus_y(x, y)


# print_x_plus_y(9,10)
# print_x_minus_y(1,2)
# print_x_plus_minus_y(5, 6)