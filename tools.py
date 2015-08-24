__author__ = 'Usuario'

import logging
from numpy import *

def setup_logger(logger_name, log_file, level=logging.INFO):
    '''Clase to create new file loggers.
    Al the info can be found in:
    http://stackoverflow.com/questions/17035077/python-logging-to-multiple-log-files-from-different-classes'''
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)


def p_Eval_(args):

    if "__import__" in args:
        raise NameError
    else:
        return str(eval(args))



# import signal
# import time
#
# class Timeout(Exception):
#     pass
#
# def Time_limiter(func,t):
#     def timeout_handler(signum, frame):
#         raise Timeout()
#
#     old_handler = signal.signal(signal.SIGALRM, timeout_handler)
#     signal.alarm(t) # triger alarm in 3 seconds
#
#     try:
#         t1=time.clock()
#         func()
#         t2=time.clock()
#
#     except Timeout:
#         print('{} timed out after {} seconds'.format(func.__name__,t))
#         return None
#     finally:
#         signal.signal(signal.SIGALRM, old_handler)
#
#     signal.alarm(0)
#     return t2-t1
#
# def troublesome():
#     while True:
#         pass
#
# Time_limiter(troublesome,2)