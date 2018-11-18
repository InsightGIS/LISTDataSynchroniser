####=================####
#Author: Alex Leith
#Date: 26/08/13
#Version: 0.0.1
#Purpose: Gets methods out of the main body. There is a custom 'processTriggers' method that needs to be removed for most people.
####=================####

from ftplib import FTP
import configparser
import socket
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
#from email.MIMEMultipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import COMMASPACE
from email import encoders
import types
import globals
import zipfile

#Server details
class Server:
    def __init__(self, protocol, url, username, password, directory):
        self.protocol = protocol
        self.url = url
        self.username = username
        self.password = password
        self.directory = directory

#File details
class Files:
    def __init__(self,localPath,unzip,fileTypes):
        self.localPath = localPath
        self.unzip = unzip
        self.fileTypes = fileTypes
    
#Shared Methods

#Find local files.
def getLocalFiles(files):
    localFiles = []

    for file in os.listdir(files.localPath):
        if (os.path.splitext(file)[1].lower() in files.fileTypes):
            path = os.path.join(files.localPath, file)
            size = os.path.getsize(path)
            timestamp = time.strftime('%Y%m%d%H%M%S', time.gmtime(os.path.getmtime(path)))
            
            localFiles.append([file,size,int(timestamp)])            
            
            globals.logging.debug('found local: %s, file size is: %s, timestamp is %s' %(file,size,timestamp))

    return localFiles

#Sends an email with one subject, message and attachment
def sendEmail(emailFrom, emailTo, subject, message, attachment):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = emailFrom
    
    if(type(emailTo) == types.ListType):
        msg['To'] = COMMASPACE.join(emailTo)
    else:
        msg['To'] = emailTo
        emailTo = [emailTo]
    
    msg.attach(MIMEText(message))
    
    if(attachment != "0"):
        #attach the log file
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(globals.logFile,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(globals.logFile))
        msg.attach(part)
    
    s = smtplib.SMTP(globals.mailServer)
    s.sendmail(emailFrom, emailTo, msg.as_string())
    s.quit()
    

#Unzip files
def unzip(zipFilePath, destDir):
    zfile = zipfile.ZipFile(zipFilePath)
    for name in zfile.namelist():
        (dirName, fileName) = os.path.split(name)
        if fileName == '':
            # directory
            newDir = destDir + '/' + dirName
            if not os.path.exists(newDir):
                os.mkdir(newDir)
        else:
            # file
            fd = open(destDir + '/' + name, 'wb')
            fd.write(zfile.read(name))
            fd.close()
    zfile.close()