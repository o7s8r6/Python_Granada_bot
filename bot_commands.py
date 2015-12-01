__author__ = 'pablogsal'
# -*- coding: utf-8 -*-


import telegram
import tools
import subprocess
import mailer,smtplib
import string
import bot_library
from numpy import *
import matplotlib
matplotlib.use('Agg') #Matplotlib without X: To run in text server.
import numpy as np
import pylab as pl
import os


class BotCommands(object):
    """
    This class represent a collection of commands that the bot can execute. Basically, each command is a method of
    the class that has the same I/O structure. To make a new function you must follow these steps:

        1) Create a function that recieves as Input parameters this list:
                -:bot: A object of the class TelegramBot that represents the TelegramBot API (To send messages to the
                       users using the telegram API, basically. (Object of class Telegram.Bot)
                -:chat_id: The chat id of the user. (Integer).
                -:args: A string representing the arguments of the command executed by the user. The structure of the
                command is: /command args , where "args" is everything that is after a space after /command".
                Notice that if the message of the user is not in a command structure, then "args" is ALL the message.
                This situation can occur when there is a multi-phase conversation and the user no longer have to
                explicit the command (for example in phase 2 or 3 of a conversation, the user do not need to write
                /command each time because we know that we are in a multi-phase conversation). (String)
                -:phase: A Integer representing the phase of the conversation. Starts at 0. (Integer).
                -:cache: Whatever we return in the :cache: argument the last time we update our conversation. The use is
                very simple: If we need to record something from the last time we update the conversation (in a multi-p
                hase conversation) we return the cache and the next time we will receive this thing in the next
                update of the conversation. ( List of objects of unkwown nature).
                -:conversation_list: The list of active conversations from the class MasterBot (for example). (List of
                Active Conversation objects).

            and returns this Output parameters:

                -:Phase: One String of the following:

                        "Ended"
                        "Next_phase"
                        "Same_phase"

                -:Cache: Whatever you want to receive in the cache Input argument in the next phase.

                Example definition:

                >>def start(bot,chat_id,args,phase,cache,conversation_list):

                    if phase == 0:
                        bla bla bla
                        return 'Next phase',["Quiero recuperar esta bonita string"]
                    else:
                        # En esta fase habremos recivido en cache la lista:
                                    cache=["Quiero recuperar esta bonita string"]
                        bli bli bli
                        return 'Ended',[]

        2) Add the function to this class as a method using the decorator @staticmethod (to avoid receieving self as an
           argument).

        3) Add to the get_commands_dict method of this class (the first one after this texts in the source code) a entry
           to the return dict in the following form:

                '/yourcoolcommand':self.your_cool_function_name_as_defined_in_the_source_code.

            Do not forget to put a comma in what was the last function before you put yours ( captain obvious
            speaking here ).

        4) Profit.


        Here are some method of the bot argument that you may need:

            bot.sendMessage
            bot.sendAudio
            bot.sendLocation
            bot.sendPhoto
            bot.sendSticker
            bot.sendChatAction

            and from the telegram module:

            telegram.ReplyKeyboardMarkup

        To know how to use these commands: https://github.com/leandrotoledo/python-telegram-bot


    """


    def get_commands_dict(self):

        return {'/start': self.start,
                              '/talk': self.submit_talk,
                              '/peval': self.python_eval,
                              '/log': self.get_log,
                              '/cluster': self.get_cluster_status,
                              '/sim': self.run_sim,
                              '/sendq': self.SendQuestionary,
                              '/questionary':self.questionary,
                              '/addQuestion':self.UpdateQuestionary,
                              '/addme':self.AddQuestionaryUser,
                              '/getq':self.printquestionary

                }
    @staticmethod
    def start(bot,chat_id,args,phase,cache,conversation_list):

        exit = """Available commands:
            - /start -> muestra este mismo texto.
            - /addme -> Adjunta al usuario al grupo dinamico.
            - /peval -> Evalua codigo python.
            - /log -> Devuelve las n ultimas lineas del log. E.g. /log 5..
            - /talk -> Permite enviar una propuesta de charla a Python Granada."""
        bot.sendMessage(chat_id=chat_id,text=exit)
        return 'Ended',[]

    @staticmethod
    def submit_talk(bot,chat_id,args,phase,cache,conversation_list):

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
    def python_eval(bot,chat_id,args,phase,cache,conversation_list):

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
    def get_log(bot,chat_id,args,phase,cache,conversation_list):

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
    def get_cluster_status(bot,chat_id,args,phase,cache,conversation_list):

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
    def run_sim(bot,chat_id,args,phase,cache,conversation_list):

        initiate_sim =subprocess.Popen('python /home/pablogal/Code/HADES-master/HADES.py '
                                       '/home/pablogal/Code/HADES-master/data.dat -quiet  '
                                       '--keys=YOSUKE_KEYS -images ',
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)

        simulations, err = initiate_sim.communicate()


        if err == "":

            image1 = open('/home/pablogal/Code/HADES-master/results/Polarization_map.png', 'rb')
            image2 = open('/home/pablogal/Code/HADES-master/results/Polarization_contours.png', 'rb')

            bot.sendPhoto(chat_id=chat_id,photo=image1)
            bot.sendPhoto(chat_id=chat_id,photo=image2)

        else:

            bot.sendMessage(chat_id=chat_id,text='Error: '+err)

        return 'Ended',[]


    @staticmethod
    def SendQuestionary(bot,chat_id,args,phase,cache,conversation_list):

        with open("./interactions/questionary_users.txt",'r') as questionfile:

            lines=questionfile.read().split('\n')

        for user in lines:

            if user != "":
                new_conversation =bot_library.ActiveConversation(int(user),'/questionary')
                conversation_list.append(new_conversation)
                new_conversation.ManageUpdate(bot,raw_message=args,chat_engine=None,
                                              conversation_list=conversation_list)

        return 'Ended',[]



    @staticmethod
    def UpdateQuestionary(bot,chat_id,args,phase,cache,conversation_list):

        if phase == 0: # This is when the command is only /UpdateQuestionary

            #Delete old stats
            try:
                os.remove('./interactions/questionary_stats.txt')
            except OSError:
                pass

            # Set the answer
            with open("./interactions/questionary.txt",'w') as questionfile:

                questionfile.write(args+'\n')

            bot.sendMessage(chat_id=chat_id, text="Set question to: "+args)
            return 'Next_phase',[]

        else:

            if ".end" not in args:
                with open("./interactions/questionary.txt",'a') as questionfile:
                    questionfile.write(args+'\n')

                bot.sendMessage(chat_id=chat_id, text="Set possible answer to: "+args)
                bot.sendMessage(chat_id=chat_id, text="Awaiting new answer")
                return 'Next_phase',[]

            else:

                last_possible_answer=args.split('.')[0]

                with open("./interactions/questionary.txt",'a') as questionfile:
                    questionfile.write(last_possible_answer)

                bot.sendMessage(chat_id=chat_id, text="Set possible answer to: "+last_possible_answer)
                bot.sendMessage(chat_id=chat_id, text="Questionary correctly setted")
                return 'Ended',[]


    @staticmethod
    def questionary(bot,chat_id,args,phase,cache,conversation_list):

        with open("./interactions/questionary.txt",'r') as questionfile:

            lines=questionfile.read().split('\n')
            question=lines[0]
            options=lines[1:]


        if phase == 0: # This is when the command is only /questionary : The first time we visit this

            custom_keyboard = [options]
            reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,one_time_keyboard=True)
            bot.sendMessage(chat_id=chat_id, text=question, reply_markup=reply_markup)

            return 'Next_phase',[]

        elif phase == 1:

            if args not in options:

                bot.sendMessage(chat_id=chat_id, text="Please, use the keyboard to answer.")

                return 'Same_phase',[]

            else:

                reply_markup = telegram.ReplyKeyboardHide()
                bot.sendMessage(chat_id=chat_id, text="Computing your response.....", reply_markup=reply_markup)
                bot.sendMessage(chat_id=chat_id, text="Received "+args)

                with open("./interactions/questionary_stats.txt",'a') as questionstats:
                    questionstats.write(args+'\n')


                return 'Ended',[]

    @staticmethod
    def AddQuestionaryUser(bot,chat_id,args,phase,cache,conversation_list):

        with open("./interactions/questionary_users.txt",'r') as questionfile:

            lines=questionfile.read().split('\n')

        # Update (or not) the users file

        if str(chat_id) not in lines:

            with open("./interactions/questionary_users.txt",'a') as questionfile:
                questionfile.write(str(chat_id)+'\n')
            bot.sendMessage(chat_id=chat_id, text="You are successfully inscribed as: "+str(chat_id))
        else:

            bot.sendMessage(chat_id=chat_id, text="You are already inscribed")

        return 'Ended',[]

    @staticmethod
    def printquestionary(bot,chat_id,args,phase,cache,conversation_list):

        from collections import Counter,OrderedDict

        with open("./interactions/questionary_stats.txt",'r') as questionstats:
                    keys=questionstats.read().split('\n')


        keynumber=Counter(filter(None, keys))
        keynumber2=OrderedDict(sorted(keynumber.items(), reverse=True));

        bar_width = 2.0
        X = np.arange(0,len(keynumber)*2,2)
        vals=keynumber2.values()
        keys=keynumber2.keys()
        for i in range(0,len(X)):
            pl.bar(X[i],float(vals[i]),bar_width,align='center',color=matplotlib.cm.jet(1.*i/len(X)), hatch="//")

        pl.xticks(X, keys, fontsize = 30);
        pl.yticks(fontsize=30)
        fig = matplotlib.pyplot.gcf()
        fig.set_size_inches(18.5, 10.5)
        pl.grid(True)
        ax=pl.gca()
        [i.set_linewidth(2) for i in ax.spines.itervalues()]
        pl.savefig('./interactions/stats.png')
        pl.close()
        image1 = open('./interactions/stats.png', 'rb')
        bot.sendPhoto(chat_id=chat_id,photo=image1)

        return 'Ended',[]
