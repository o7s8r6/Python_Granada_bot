__author__ = 'Usuario'

import logging
import telegram
import cleverbot
import string
import tools
import time
import os
import threading
import uuid
import bot_commands
from collections import Counter

#Create logger for module
module_logger = logging.getLogger('Python_granada_bot.bot_library')

class MasterBot(object):
    """This class manages the bot at a local level. A brief list of taks of this class is:
    -Echo to the server for updates.
    -Manage the creation and deletion of new and old conversations.
    -Organize conversations in new and old depending of the status of the conversation list.
    -Update the status of the conversation if needed (parallelization)


    When instantiate the class you must provide nothing. ToDo: Provide the

    Properties:

        bot -> The telegram API high level wrapper (object of class telegram.bot)
        command_library -> An instantiation of the command library class (mainly a dict with the functions).
        chat_engine -> The Markovian cleverbot chat engine class (object).
    """

    def __init__(self,bot_key):

        # Create custom logger to the master to keep track of general things in a master log.
        self.logger = logging.getLogger('Python_granada_bot.bot_library.MasterBot')
        self.logger.debug('Instanciating class Masterbot.')
        #Instantiate the telegram bot
        self.bot = telegram.Bot(bot_key)
        #Create empty list of active conversations
        self.active_conversations = []

        try:
            self.last_update_ID = self.bot.getUpdates()[0].update_id
        except IndexError:
            self.last_update_ID = None

        self.chat_engine = cleverbot.Cleverbot()


    def echo(self):
        """
        This method queries the server for updates. In the case that we find updatesm then we
        start n threads (where n is the number of updates to process) to manage each one).

        When each thread is started, we increase the update_number, so when we query the server again
        the server will know that we are done with the processed updates.

        At the end of each update group, we wait for all threads to end and repeat.

        :return: Nothing
        """

        #Get number of new updates
        num_updates = len(self.bot.getUpdates(offset=self.last_update_ID))

        #If we have updates we do stuff
        if num_updates > 0:

            self.logger.debug('Received '+str(num_updates)+' messages to process.')

            # To avoid problems with sequenciality, if there is more that one message of the same user,
            # manage the updates in serial mode, if not, run in parallel.

            #Initialize list of ids for the users
            list_of_ids=[]

            # Loop over the updates to get the ID's and then construct a dictionary using Counter
            for update in self.bot.getUpdates(offset=self.last_update_ID):
                list_of_ids.append(update.message.chat_id)
            list_of_ids=Counter(list_of_ids)

            #If we have more than one message for the same user
            if any([item > 1 for item in list_of_ids.values()]):

                self.logger.debug('Processing updates in serial.')
                update_num=1
                # Bucle para gestionar cada una de las updates que tenemos
                for update in self.bot.getUpdates(offset=self.last_update_ID):

                    self.process_update(update=update,update_num=update_num)
                    update_num =  update_num +1
                    self.last_update_ID = update.update_id + 1

            #If we NOT have more than one message for the same user
            else:
                self.logger.debug('Processing updates in parallel.')
                update_num=1
                # Bucle para gestionar cada una de las updates que tenemos
                for update in self.bot.getUpdates(offset=self.last_update_ID):

                    #Paralelizing threads
                    thr=threading.Thread(target=self.process_update, args=(update,update_num), kwargs={})
                    thr.start()
                    update_num =  update_num +1
                    self.last_update_ID = update.update_id + 1


                thr.join()  # This will wait until the last one is done! :)



    def process_update(self,update,update_num):

        """
        This method process each update. The tasks are organisez as follows:

            1) Check if the message is text, if not, send a error message to the user.
            2) If is text:
                3) Look in the conversation list to see if we have already a conversation pending with the user
                    3.1) If we have a conversation, call the ManageUpdate method in the old conversation and mark
                         the need_for_new_conversation flag False.
                    3.2) If wee do not find and old conversation (the need_for_new_conversation flag is True) create
                         a new conversation and call the ManageUpdate method in it.
            4) Look for ended conversations in the list and delete them. -> This must be done here because as the
               updates run in parallel we need to delete old conversation to avoid the case when for updating a
               conversation we must look up in the list for active conversations and find some of them that are ended.


        :param update: Each (JSON) update to process (property of telegram bot class). - bot.getUpdates property
        :param update_num: The update number in the update group (for logger pourposes) - Integer
        :return: Nothing
        """

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
                    conversation.ManageUpdate(bot=self.bot,chat_ID=chat_id, raw_message=message,
                                              chat_engine=self.chat_engine,conversation_list=self.active_conversations)
                    break

            if need_for_new_conversation:
                self.logger.info('Creating new conversation for the message')
                new_conversation =ActiveConversation(chat_id,message)
                self.active_conversations.append(  new_conversation  )
                self.logger.info('There are '+str(len(self.active_conversations))+ ' active conversations')
                self.logger.info('Updating the status of the conversation.')
                new_conversation.ManageUpdate(bot=self.bot,chat_ID=chat_id, raw_message=message,
                                              chat_engine=self.chat_engine,conversation_list=self.active_conversations)

        else: # If is not a text message
            self.bot.sendMessage(chat_id=chat_id,text='Other formats than text are not supported yet')

        for conversation in self.active_conversations:

            if not conversation.active:
                #conversation.logger.handlers = [] # Delte the object logger to avoid duplicate messages
                self.active_conversations.remove(conversation)
                self.logger.info('Deleting conversation')
                self.logger.info('There are '+str(len(self.active_conversations))+ ' active conversations')


class ActiveConversation(bot_commands.BotCommands):
    """
    This class represents each active conversation. To initialize the class you must provide:

        -The ChatId representing the userID of the message -> String
        -The rawmessage to process -> The text message in raw format to process -> String
    """
    def __init__(self,chatID,raw_message):

        #Instantiate the command library from the parent class with Super!
        self.commands_dict = super(ActiveConversation, self).get_commands_dict()
        # Instantiate properties with the ChatId and Message
        self.chatID = chatID
        self.active = True
        self.ActualMessage = raw_message
        #Instantiate phase indicator and get Unique id
        self.conversation_phase = 0 #For multiple-phase conversations
        self.uniqueID = uuid.uuid4().get_hex()
        #Set conversation logger.
        newlogger = tools.setup_logger(self.uniqueID,os.path.dirname(os.path.realpath(__file__))
                                       +'/logs/'+str(self.chatID)+'.log')
        self.logger = logging.getLogger(self.uniqueID)
        #Set error counter
        self.errorcounter = 0
        if self.commandsQ(raw_message):

            self.function = self.AssignCommand(raw_message)
            self.logger.info('Conversation marked as command.')
            self.function_type = 'BotCommand'

        else:

            self.function = None
            self.function_type = 'ChatEngine'
            self.logger.info('Conversation marked as chat.')


        self.cache =[]

    def ManageUpdate(self,bot,chat_ID,raw_message,chat_engine,conversation_list):


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

                talk_status, self.cache = self.function(bot,chat_ID,self.args,self.conversation_phase,self.cache
                                                        ,conversation_list)

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
                self.errorcounter += 1

                if self.errorcounter < 5:
                    self.logger.info('Telegram Error. Going to sleep 4 seconds.')
                    time.sleep(4)
                    self.ManageUpdate(bot,chat_ID,raw_message,chat_engine,conversation_list)
                else:

                    self.active = False




    def commandsQ(self,raw_message):

        command = raw_message.split(' ')[0]
        if command in self.commands_dict: # Si reconocemos el mensaje
            return True
        else:  # Si no reconocemos el mensaje
            return False

    def AssignCommand(self,raw_message):

        command = raw_message.split(' ')[0] # Get the /command part of the message

        return self.commands_dict[command]  # To get the actual command and args












