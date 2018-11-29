####=================####
#Authors: Alex Leith, Duri Bradshaw
#Date: 09/09/18
#Purpose: Download files from theLIST to a local directory over FTP, will skip any file that has not changed since last update.
####=================####

import os.path, time
import ftplib
import socket #used to catch ftp error
import ExtendedMethods
import globals


def syncDirectory(server,files):
    
    #connect to FTP
    try:
        globals.logging.info('Connecting to FTP site')
        ftp = ftplib.FTP(server.url)
        ftp.login(server.username,server.password)
        ftp.cwd(server.directory)
        connected = 1
    except (EOFError, socket.error, ftplib.error_perm, ftplib.error_temp):
        print('Error: FTP Connection failed.')
        globals.logging.error("FTP Connection Failed...")
        connected = 0
    
    if (connected):
        countMatches = 0

        #some lists
        tempList = []
        remoteFiles = []
        
        #Find remote files
        print('REMOTE: %s@%s' % (server.username,server.url))
        tempList = ftp.nlst()
        
        for file in tempList:
            if (os.path.splitext(file)[1].lower() in files.fileTypes):
                timestamp = ftp.sendcmd('MDTM %s' % (file))[4:]
                remoteFiles.append([file,ftp.size(file),int(timestamp)])
                
        #Fine local files
        print('LOCAL: %s' % files.localPath)
        localFiles = ExtendedMethods.getLocalFiles(files)
        
        #Check for changes
        for remoteFile,remoteSize,remoteTimestamp in remoteFiles:
            print('Remote file:' + remoteFile)
            matchNotFound = 1
            for localFile,localSize,localTimestamp in localFiles:
                if (remoteFile == localFile):
                    matchNotFound = 0
                    if(remoteSize == localSize) and (remoteTimestamp < localTimestamp):
                        globals.logging.debug('Skip download for %s, unchanged file: size %i and timestamp %i' % (remoteFile,remoteSize,remoteTimestamp))
                        countMatches += 1
                    else:                
                        globals.logging.info("File has changed:" + remoteFile)
                        
                        print('Size %i:%i' % (remoteSize, localSize))
                        print('Time %i:%i' % (remoteTimestamp, localTimestamp))
                        
                        ftpDownloadFile(ftp, remoteFile, os.path.join(files.localPath, localFile), files)
            
            if(matchNotFound):
                globals.logging.info("New file found: " + remoteFile)

                ftpDownloadFile(ftp, remoteFile, os.path.join(files.localPath, remoteFile), files)
            
        globals.logging.info("%i unchanged files found, not downloading." % countMatches)

    else:
        #Script Failed to Connect to FTP
        subjectText = "NOTICE! FTP Script Failed to Connect"
        messageText = "Download Failed, check FTP connection manually and rerun."

# Download over FTP
def ftpDownloadFile(connection, remoteFile, localFile, files):
    f = open(localFile,"wb")

    print("Downloading: "+remoteFile)
    try:
        connection.retrbinary("RETR " + remoteFile, f.write)
        f.close()

        globals.downloadedFiles.append(remoteFile)
        globals.logging.info("Retrieved: " + remoteFile + " to: " + localFile)
        if files.unzip == "True":
            globals.logging.info("Unzipping...")
            ExtendedMethods.unzip(localFile, files.localPath)
    except Exception as e:
        globals.logging.error("Failed to retrieve: " + remoteFile + " to: " + localFile + " error was: " + str(e))
        f.close()