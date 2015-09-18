__author__ = 'Usuario'

import logging
from numpy import *
import os as os_library_protected
import sys as sys_library_protected

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


def update_progress(progress, time):
    barLength = 30  # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength * progress))
    text = "\rPercent: [{0}] {1:.2f}% --- {3:.2f} s. remain. {2}".format(
        "=" * (block - 1) + ">" + " " * (barLength - (block - 1)-1), progress * 100, status, time)
    sys_library_protected.stdout.write(text)
    sys_library_protected.stdout.flush()