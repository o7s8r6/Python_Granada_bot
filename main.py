__author__ = 'Usuario'

#!/usr/bin/env python
#
# Simple Bot to reply Telegram messages


import logging
import telegram
import time
import logging, argparse
import bot_library
import os,sys


#  _____      _ _   _       _ _          _   _
# |_   _|    (_) | (_)     | (_)        | | (_)
#   | | _ __  _| |_ _  __ _| |_ ______ _| |_ _  ___  _ __
#   | || '_ \| | __| |/ _` | | |_  / _` | __| |/ _ \| '_ \
#  _| || | | | | |_| | (_| | | |/ / (_| | |_| | (_) | | | |
#  \___/_| |_|_|\__|_|\__,_|_|_/___\__,_|\__|_|\___/|_| |_|
#

######## START OF PARSER CREATION #########

parser = argparse.ArgumentParser(description='Bot para python granada.')

parser.add_argument('-v', dest='verbose_flag', action='store_const',
                   const=True, default=False,
                   help='Prints more info (default: False)')

args = parser.parse_args()

# Create logger-------------------------------------------------

######## START OF LOGGER CREATION #########
# create logger with 'spam_application'
logger = logging.getLogger('Python_granada_bot')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(os.path.dirname(os.path.realpath(__file__))+'/logs/Talos_bot.log')
fh.setLevel(logging.INFO)
# create console handler
ch = logging.StreamHandler()

if args.verbose_flag:
    ch.setLevel(logging.DEBUG)
else:
    ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)
######## END OF LOGGER CREATION #########

# Variable to get the las update
LAST_UPDATE_ID = None


# ___  ___      _
# |  \/  |     (_)
# | .  . | __ _ _ _ __
# | |\/| |/ _` | | '_ \
# | |  | | (_| | | | | |
# \_|  |_/\__,_|_|_| |_
#

def main():


    PythonGranadaBot = bot_library.MasterBot()

    while True:
        logger.debug('Awaiting for new imput')
        PythonGranadaBot.echo()
        time.sleep(3)


if __name__ == '__main__':
    main()

