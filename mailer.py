__author__ = 'Usuario'

import smtplib

def send_mail(dest_mail,message):

    fromaddr = 'pablogsal@gmail.com'
    toaddrs  = dest_mail
    msg = "\r\n".join([
      "From: user_me@gmail.com",
      "To: user_you@gmail.com",
      "Subject: Just a message",
      "",
      message
      ])
    username = 'pablogsal@gmail.com'
    password = '((asdas))'
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(username,password)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()