#!/usr/bin/env python
# -*- coding:utf-8 -*-
import imaplib
import email
import os
import time
import commands
from smtplib import SMTP


def __send(conf,t,body):
    smtp = SMTP()
    smtp.connect(conf['smtpserver'], conf['smtpsport'])
    smtp.login(conf['login'], conf['passwd'])

    from_addr = "Major <{}>".format(conf['login'])
    to_addr = t[1]

    msg = "From: {}\nTo: {}<{}>\nSubject: Major report\n\n{}".format(from_addr,t[0],t[1],body) 

    smtp.sendmail(conf['login'], t[1], msg)
    smtp.quit()    



def __save(subj,body,f):
    print ("Call __save:\n\tsubj:{}\n".format(subj))
    file = ''
    try:
        c,file = subj.split(None, 1)
    except Exception as e:
        print ("Error on split: {}".format(e));
        file = ("{}/{}.txt".format(os.path.expanduser('~'),"-".join( [str(k) for k in time.localtime()] )))

    if not file:
        print "file так и нет";
        return False

    print ("\tfile={}".format(file))

    try:
        pass
        f = open (file,'w')
        f.write(body)
        f.close()
    except Exception as e:      
        print ("Ошибка при записи файла: {}".format(e))

def __shell(subj,body,f):
    print ("Call __shell")
    command = ";".join ( [str(c) for c in __split2command(body,conf)]  )
    # for s in __split2command(body,conf):
    #   print "\t\t\t!{}!".format(s)
    print "\t\texec: {}".format(command);
    output = commands.getoutput(command)
    print ("---\n{}\n---\n".format(output))
    __send(conf,f,output)
    # popen
    # http://plumbum.readthedocs.org/en/latest/



# Главная функция, она описывает, что делать с файлом
def parse_command(com,body,f,css):
    print ("Получили команду!{}!".format(com))
    print ("Отчет для !{}!".format(f))
    for func in css['parse']:
        if com.lower().startswith(func.lower()):
            css['parse'][func](com,body,f)
            return True

    print ("Не понял, что делать")
    return False

def __correct_from(e,cfs):
    '''
    проверяем, что письмо от хозяина
    '''
    for cf in cfs:
        if cf == e:
            return True
    return False

def __is_comment_string(s,css):
    '''
    проверяем строку на пустоту и то, что она комментарий
    '''
    if s=='':
        return True
    for cs in css:
        if s.startswith(cs):
            return True
    return False


def __split2command(body,css):
    ret = []
    for s in body.split("\n"):
        if not __is_comment_string(s,css['begin_of_comment_string']):
            ret.append(s)
    return ret


def make_command_list(cc):
    '''
    создаем список команд по конфигу
    '''
    ret = []

    imap = imaplib.IMAP4_SSL(cc['server'])
    try:
        imap.login(cc['login'],cc['passwd'])
        imap.select('INBOX')
        result, data = imap.uid('search',None, '(UNSEEN)')
        # result, data = imap.search(None, "(UNSEEN)")
        if data[0]:
            for mail_id in data[0].split():
                # imap.uid('store',mail_id, "+FLAGS","(\SEEN)")

                result,body = imap.uid('fetch',mail_id, "(RFC822)")
                
                raw_mail = body[0][1]
                mail = email.message_from_string(raw_mail)
                email_from = email.utils.parseaddr(mail['From'])
                email_subj = mail['Subject']
                email_type = mail.get_content_maintype()
                email_charset = mail.get_content_charset()
                # print ("\tsubj=!{}!\n\ttype=!{}!\n\tcharset=!{}!\n".format(email_subj,email_type,email_charset))

                # помечаем письмо, как прочитанное #TK - не пашет
                # if cc['debug'] == :
                
                # главный разбор
                if __correct_from(email_from[1], cc['correct_from']) and email_type=='text':
                    # plain text
                    ret.append((email_subj, __read_mail(mail,email_charset),email_from))
                elif __correct_from(email_from[1], cc['correct_from']) and email_type!='text':
                    # html и прочее
                    # print ("\ttype={}".format(email_type))
                    for part in mail.walk():
                        body = ''
                        email_charset = part.get_content_charset()
                        if part.get_content_type() == 'text/plain':
                            ret.append((email_subj, __read_mail(part,email_charset),email_from))

                        # elif part.get_content_type() == 'text/html':
                        #     email_charset = part.get_content_charset()
                        #     body = part.get_payload(decode=True)
                        #     body = unicode(body,str(email_charset),"ignore").encode('utf8','replace')
                        #     ret.append(("{}.html".format(email_subj),body))
                        #     print ("html={}".format(body))

                        
                        # if part.get_content_type() == 'application/octet-stream':
                        #   if check(part.get_filename()):
                        #     return part.get_payload(decode=1)


        # Заканчиваем работу c почтой
        imap.close()
        imap.logout()
            
    except Exception as e:
        print ("Ошибка при работе с почтой: {}".format(e))

    return ret  

def __read_mail(part,email_charset):
    body = ""
    for ss in part.get_payload(decode=True).split("\n"):
        # print ("ss={}".format(ss))
        ss = unicode(ss,str(email_charset),"ignore").encode('utf8','replace')
        ss = ss.strip('\r')
        if ss.startswith('--'):
            # вываливаемся, если пошла подпись
            break
        else:
            body = "{}\n{}".format(body,ss)
    return body
    # return ((email_subj,body))


# Конфиг
conf = {'debug':False,
        'server':'imap.yandex.ru',
        'smtpserver':'smtp.yandex.ru',
        'login':'email_robot@email_robor.ru',
        'passwd':'email_robot_password',
        'smtpsport':25,
        'begin_of_comment_string':[' ','#','!','//','%'],
        'correct_from':['dev@email_robot.ru',
                        'dev@gmail.com',
                        'dev@email_robot.net'],
        'parse':{'Save':__save,
                 'Lets':__save,
                 'Shell':__shell
        }
}


# MAIN
if __name__ == '__main__':
    print ("Старт")

    # Получаем команды из почты 
    commds = make_command_list(conf)

    # Работаем с командами
    for s,c,f in commds:
        parse_command(s,c,f,conf)


    print ("Финиш")
