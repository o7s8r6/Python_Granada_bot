__author__ = 'Usuario'

import logging
import telegram
import cleverbot
import string
import mailer, smtplib
import tools
import time
import os
import threading
import uuid
import subprocess


#Create logger for module
module_logger = logging.getLogger('Python_granada_bot.bot_library')

class MasterBot(object):

    def __init__(self):

        self.logger = logging.getLogger('Python_granada_bot.bot_library.MasterBot')
        self.logger.debug('Instanciating class Masterbot.')

        self.bot = telegram.Bot('126412682:AAEABq7JHJVRJ2lv4YqxVYWiwlWko4QgB_g')
        self.command_library = BotCommands()
        self.active_conversations = []

        try:
            self.last_update_ID = self.bot.getUpdates()[0].update_id
        except IndexError:
            self.last_update_ID = None

        self.chat_engine = cleverbot.Cleverbot()


    def echo(self):

        #Get number of new updates
        num_updates = len(self.bot.getUpdates(offset=self.last_update_ID))

        #If we have updates we do stuff
        if num_updates > 0:

            self.logger.debug('Received '+str(num_updates)+' messages to process.')

            # Bucle para gestionar cada una de las updates que tenemos
            update_num=1
            for update in self.bot.getUpdates(offset=self.last_update_ID):

                #Paralelizing threads Good thing?
                thr=threading.Thread(target=self.process_update, args=(update,update_num), kwargs={})
                thr.start()
                update_num =  update_num +1
                self.last_update_ID = update.update_id + 1


            thr.join()  # This will wait until the last one is done! :)



    def process_update(self,update,update_num):

        self.logger.info('Analizing update '+str(update_num)+'.')
        # Cogemos el chat_id de la conversacion y el mensaje
        chat_id = update.message.chat_id
        message = update.message.text.encode('utf-8')

        if (message): # If the message is made out of text, we can answer it
            need_for_new_conversation = True

            for conversation in self.active_conversations:
                if conversation.chatID == chat_id:
                    self.logger.info('The message is part of an old conversation')
                    need_for_new_conversation = False
                    self.logger.info('Updating the status of the conversation.')
                    conversation.ManageUpdate(self.bot,chat_id,message,self.chat_engine)

            if need_for_new_conversation:
                self.logger.info('Creating new conversation for the message')
                new_conversation =ActiveConversation(chat_id,message,self.command_library)
                self.active_conversations.append(  new_conversation  )
                self.logger.info('There are '+str(len(self.active_conversations))+ ' active conversations')
                self.logger.info('Updating the status of the conversation.')
                new_conversation.ManageUpdate(self.bot,chat_id,message,self.chat_engine)

        else: # If is not a text message
            self.bot.sendMessage(chat_id=chat_id,text='Other formats than text are not supported yet')

        for conversation in self.active_conversations:

            if not conversation.active:
                #conversation.logger.handlers = [] # Delte the object logger to avoid duplicate messages
                self.active_conversations.remove(conversation)
                self.logger.info('Deleting conversation')
                self.logger.info('There are '+str(len(self.active_conversations))+ ' active conversations')



class ActiveConversation(object):

    def __init__(self,chatID,raw_message,bot_commands):


        self.chatID = chatID
        self.active = True
        self.ActualMessage = raw_message

        self.conversation_phase = 0 #For multiple-phase conversations
        self.uniqueID = uuid.uuid4().get_hex()
        newlogger = tools.setup_logger(self.uniqueID,os.path.dirname(os.path.realpath(__file__))+'/logs/'+str(self.chatID)+'.log')
        self.logger = logging.getLogger(self.uniqueID)

        if self.commandsQ(raw_message,bot_commands):

            self.function = self.AssignCommand(raw_message,bot_commands)
            self.logger.info('Conversation marked as command.')
            self.function_type = 'BotCommand'

        else:

            self.function = None
            self.function_type = 'ChatEngine'
            self.logger.info('Conversation marked as chat.')


        self.cache =[]

    def ManageUpdate(self,bot,chat_ID,raw_message,chat_engine):

        self.logger.info('Received: '+raw_message+' from '+str(chat_ID)+'.')
        try:
            if self.function_type == 'ChatEngine':
                self.args = raw_message
                cleverbot_answer=chat_engine.ask(self.args)


                self.logger.info('Answering: '+cleverbot_answer+'.')

                if cleverbot_answer == "":
                    cleverbot_answer = "I am sleeping now. Try it later or use a command from /start"

                bot.sendMessage(chat_id=chat_ID,text=cleverbot_answer)
                self.active = False

            if self.function_type == 'BotCommand':

                if '/' in raw_message:
                    self.args = string.join(raw_message.split(' ')[1:],' ')
                else:
                    self.args = raw_message

                talk_status, self.cache = self.function(bot,chat_ID,self.args,self.conversation_phase,self.cache)
                self.logger.info('Talk status code recieved: '+talk_status+'.')
                if talk_status == 'Next_phase':
                    is_the_conversation_ended = False
                    self.conversation_phase = self.conversation_phase + 1

                elif talk_status == 'Same_phase':
                    is_the_conversation_ended = False

                else :
                    is_the_conversation_ended = True


                if is_the_conversation_ended :

                    self.active = False

        except telegram.TelegramError:
                self.logger.info('Telegram Error. Going to sleep 0.5 second.')
                time.sleep(4)

                self.ManageUpdate(bot,chat_ID,raw_message,chat_engine)




    def commandsQ(self,raw_message,bot_commands):

        command = raw_message.split(' ')[0]
        if command in bot_commands.commands_dict: # Si reconocemos el mensaje
            return True
        else:  # Si no reconocemos el mensaje
            return False

    def AssignCommand(self,raw_message,bot_commands):

        command = raw_message.split(' ')[0] # Get the /command part of the message

        return bot_commands.commands_dict[command]  # To get the actual command and args


class BotCommands(object):

    def __init__ (self):

        self.commands_dict = {'/start': self.start,
                              '/talk': self.submit_talk,
                              '/peval': self.python_eval,
                              '/log': self.get_log,
                              '/cluster': self.get_cluster_status,
                              '/sim': self.run_sim}
    @staticmethod
    def start(bot,chat_id,args,phase,cache):

        exit = """Available commands:
            - /start -> muestra este mismo texto.
            - /peval -> Evalua codigo python.
            - /log -> Devuelve las n ultimas lineas del log. E.g. /log 5..
            - /talk -> Permite enviar una propuesta de charla a Python Granada."""
        bot.sendMessage(chat_id=chat_id,text=exit)
        return 'Ended',[]

    @staticmethod
    def submit_talk(bot,chat_id,args,phase,cache):

        if phase == 0: # This is when the command is only /cluster : The first time we visit this

            custom_keyboard = [['Yes', 'No' ]]
            reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,resize_keyboard=True,one_time_keyboard=True)
            bot.sendMessage(chat_id=chat_id, text="Do you want to submit a talk?.", reply_markup=reply_markup)

            return 'Next_phase',[]

        elif phase == 1:

            if args != 'Yes' and args != 'No':

                bot.sendMessage(chat_id=chat_id, text="Please, use the keyboard to answer.")

                return 'Same_phase',[]

            else:

                reply_markup = telegram.ReplyKeyboardHide()
                bot.sendMessage(chat_id=chat_id, text="Computing your response.....", reply_markup=reply_markup)

                if args == 'Yes' :
                    bot.sendMessage(chat_id=chat_id, text="Received 'Yes'")
                    bot.sendMessage(chat_id=chat_id, text="Please, write the title of the talk")
                    return 'Next_phase',[]
                else:
                    bot.sendMessage(chat_id=chat_id, text="Received 'No'")
                    return 'Ended',[]

        elif phase == 2:

            bot.sendMessage(chat_id=chat_id, text="The title for your talk is: "+args)
            custom_keyboard = [['Yes', 'No' ]]
            reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,resize_keyboard=True,one_time_keyboard=True)
            bot.sendMessage(chat_id=chat_id, text="Do you want to submit it?.", reply_markup=reply_markup)

            return 'Next_phase',args

        elif phase == 3:

            if args != 'Yes' and args != 'No':

                bot.sendMessage(chat_id=chat_id, text="Please, use the keyboard to answer.")

                return 'Same_phase',cache

            else:

                reply_markup = telegram.ReplyKeyboardHide()
                bot.sendMessage(chat_id=chat_id, text="Computing your response.....", reply_markup=reply_markup)

                if args == 'Yes' :
                    bot.sendMessage(chat_id=chat_id, text="Received 'Yes'")
                    try:
                        mailer.send_mail('contacto@python-granada.es ',cache)
                        bot.sendMessage(chat_id=chat_id, text="Ok, talk submitted!")
                    except smtplib.SMTPAuthenticationError:
                        bot.sendMessage(chat_id=chat_id, text="Oooops...problem with the mail.")
                        bot.sendMessage(chat_id=chat_id, text="Please, try it later!")



                    return 'Ended',[]
                else:
                    bot.sendMessage(chat_id=chat_id, text="Received 'No'")
                    bot.sendMessage(chat_id=chat_id, text="Please, try again using the command /talk")
                    return 'Ended',[]

    @staticmethod
    def python_eval(bot,chat_id,args,phase,cache):

        try:
            evaluation=tools.p_Eval_(args)
            bot.sendMessage(chat_id=chat_id,text=evaluation)

        except SyntaxError:
            bot.sendMessage(chat_id=chat_id,text='Error evaluating your command.')
            bot.sendMessage(chat_id=chat_id,
            text='''You can use a lot of python commands: All the standard library is available as well as numpy.
             If you want to use numpy you can do it without having to use np.something().
             You can use sin([1,2,3,4,5,6]) and have fun immediately!''')

        except NameError:

            bot.sendMessage(chat_id=chat_id,text='Error evaluating your command.')
            bot.sendMessage(chat_id=chat_id,
            text='''Your request raised NameError.
            My creators programmed me to be strong against 'clever' people.
            Be nice with me!
            ''')


        return 'Ended',[]

    @staticmethod
    def get_log(bot,chat_id,args,phase,cache):

        if args == "" :

            with open (os.path.dirname(os.path.realpath(__file__))+'/logs/Talos_bot.log', "r") as log_file:
                data=log_file.read()
                last_lines = string.split(data, '\n')[-4:-1]
                #last_lines = string.join(last_lines,'\n')

                if len(last_lines) == 1:
                    bot.sendMessage(chat_id=chat_id,text=last_lines[0])
                else:
                    for line in last_lines:
                        bot.sendMessage(chat_id=chat_id,text=line)

            return 'Ended',[]

        else :

            try:
                number_of_lines=int(args)+1
                with open (os.path.dirname(os.path.realpath(__file__))+'/logs/Talos_bot.log', "r") as log_file:
                    data=log_file.read()
                    last_lines = string.split(data, '\n')[-number_of_lines:-1]
                    #last_lines = string.join(last_lines,'\n')

                    if len(last_lines) == 1:
                        bot.sendMessage(chat_id=chat_id,text=last_lines[0])
                    else:
                        for line in last_lines:
                            bot.sendMessage(chat_id=chat_id,text=line)

                    return 'Ended',[]

            except ValueError:

                bot.sendMessage(chat_id=chat_id,text='Please, provide an integer number')
                return 'Ended',[]


    @staticmethod
    def get_cluster_status(bot,chat_id,args,phase,cache):

        get_simulations = subprocess.Popen(['ssh', 'cluster','ls /home/users/dreg/pablogal/RMHD/datafiles | wc -l'],
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        n_simulations, err = get_simulations.communicate()

        get_schedule = subprocess.Popen(['ssh', 'cluster','cat  /home/users/dreg/pablogal/RMHD/simulation_schedule_list.txt | tail -5'],
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        schedule, err = get_schedule.communicate()

        bot.sendMessage(chat_id=chat_id,text='There are '+str(n_simulations)+' simulation bundles in the cluster')

        bot.sendMessage(chat_id=chat_id,text='Last 3 simulations:')

        clean_schedule= filter(None,schedule.split('\n'))

        for line in clean_schedule:

            bot.sendMessage(chat_id=chat_id,text=line.replace('       ','')) # replace is for propper formating of te
             #  lines

	get_qstat = subprocess.Popen(['ssh', 'cluster','qstat | tail -n +3'],
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE)

	qstat, err = get_qstat.communicate()

	clean_qstat= qstat.split('\n')
	
	for line in clean_qstat:
		if line:	
			bot.sendMessage(chat_id=chat_id,text=line) # replace is for propper formating of the lines

        return 'Ended',[]


    @staticmethod
    def run_sim(bot,chat_id,args,phase,cache):

        initiate_sim =subprocess.Popen('python /home/pablogal/Code/HADES-master/HADES.py /home/pablogal/Code/HADES-master/data.dat -v  '
                                       '--keys=YOSUKE_KEYS -images ',
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)

        simulations, err = initiate_sim.communicate()

        if err == None:

            image1 = open('/home/pablogal/Code/HADES-master/results/Polarization_map.png', 'rb')
            image2 = open('/home/pablogal/Code/HADES-master/results/Polarization_contours.png.png', 'rb')

            bot.sendPhoto(chat_id=chat_id,photo=image1)
            bot.sendPhoto(chat_id=chat_id,photo=image2)

        else:

            bot.sendMessage(chat_id=chat_id,text='Error: '+err)

        return 'Ended',[]









