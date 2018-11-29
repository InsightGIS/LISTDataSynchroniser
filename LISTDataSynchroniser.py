####=================####
#Authors: Alex Leith, Duri Bradshaw
#Date: 09/09/18
#Version: 2.0.0
#Purpose: To automate the downloading and uploading of GIS data from the LIST FTP server
#Usage: LISTDataSynchroniser.py -c "c:\Path\to\config.ini" (-t 1) the () bit is optional 
#       and will run the method 'processTriggers' from the ExtendedMethods file..
####=================####

##Import statements (could be pared down a bit)
import configparser
from optparse import OptionParser #parse command line arguments
import ExtendedMethods #a file full of custom methods including triggers.
import httpsync
import ftpsync
import globals

#handle command line arguments
processTriggersScript = 0;
configFile = "config.ini"
parser = OptionParser()
parser.add_option("-c", "--config", dest="configFile",
                  help="File to load configuration from", metavar="FILE")
parser.add_option("-t", "--triggers", dest="processTriggersScript",
                  help="True or false for processing the triggers script", metavar="FILE")
(options, args) = parser.parse_args()
if(options.configFile):
    configFile = options.configFile
processTriggersScript = options.processTriggersScript
#load config
config = configparser.ConfigParser()
config.read(configFile)

#[log]
lf = config.get("log","logFile")

#set up global variable file
globals.init(lf)

#[files]
localPath = config.get("files","localPath")
unzip = config.get("files","unzip")
fileTypes = [f.strip().lower() for f in config.get("files","fileTypes").split(',')]
files = ExtendedMethods.Files(localPath,unzip,fileTypes)

#[email]
globals.sendmail = config.get("email","sendmail")
globals.emailAddress = config.get("email","emailAddress")
globals.mailServer = config.get("email","mailServer")
#globals.emailAddressLIST = [i[1] for i in config.items("listEmail")]

#[serverdetails]
TYPE = config.get("server","TYPE").upper()
URL = config.get("server","URL")
UN = config.get("server","UN")
PW = config.get("server","PW")
baseDir = config.get("server","BASEDIR")
server = ExtendedMethods.Server(TYPE,URL,UN,PW,baseDir)

#email strings
warnText = ""
subjectText = "FTP Download Script Run"
messageText = ""

# Downlaod files
if server.protocol == 'FTP':
    globals.logging.info("Connecting over FTP")
    ftpsync.syncDirectory(server,files)
    
else:
    globals.logging.error("Invalid server URL (" + URL + ")")

#Send email
if (globals.sendmail == "True"):
    ##email details##
    for i in globals.downloadedFiles:
        messageText = messageText + "\n- %s" %i

    messageText += "\nFiles were downloaded to %s" % localPath

    if(len(warnText) > 1):
        messageText = messageText + "\n\n~~~Warning!~~~\n" + warnText

    globals.logging.info("Sending email")
    ExtendedMethods.sendEmail(globals.emailAddress, globals.emailAddress, subjectText, messageText, globals.logFile)
    globals.logging.debug("Email sent")


globals.logging.info("Script Ends")