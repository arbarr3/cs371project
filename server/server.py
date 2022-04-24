#==============================================================================
#
#   Authors:    Alexander Barrera & Robert Crispen
#   Date:       24 April 2022
#   Org:        University of Kentucky
#   Class:      CS371 - Computer Networking
#
#   Purpose:    This file runs a basic socket server
#               
#==============================================================================

from calendar import c
from cmath import inf
import csv
import datetime
import os               # Used for filepath referencing
import sys
import time
import warnings               
import tqdm             # Used to display file transfer progess within terminal
import shutil           # Used for deleting directories
import socket           # Used to implement python socket networking functionality
import threading        # Used to grant each client connection a seperate thread
import pickle
import json             # Used to access the user plain text file for authentication
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings( "ignore", module = "seaborn")  # Ignore seaborn warning regarding MatPlotLib running on multiple threads

#============================= Private Variables ===============================
# 
#   _location_      :  (str)   :   Defines the server root as the real filepath of the current working directory
#   _userfiles_     :  (str)   :   The path to the users directory
#   _users_         :  (Dict)  :   Plain text dictory of user:password strings
#   _dirTree_       :  (List)  :   Lists the files and directories of the entire server
#   _fileDownloads_ :  (Dict)  :   Keys: filepath, Value: Number of times the file has been downloaded
#
#------------------------------------------------------------------------------
_location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

_userfiles_ = os.path.join(_location_, "users")
if not os.path.isdir(_userfiles_):
    os.mkdir(_userfiles_)

_sharedfiles_ = os.path.join(_location_, "shared")
if not os.path.isdir(_sharedfiles_):
    os.mkdir(_sharedfiles_)

_users_ = os.path.join(_location_, "users.json")

filesPath = os.path.join(_location_, "files.json")
if os.path.exists(filesPath):
    with open(filesPath, 'r') as inFile:
        _fileDownloads_ = json.load(inFile)
else:
    with open(filesPath, 'w') as outFile:
        json.dump({}, outFile)
    _fileDownloads_ = {}

_downloadFiles_ = os.path.realpath(os.path.join(_location_, "downloadLogs"))
_upFiles_ = os.path.realpath(os.path.join(_location_, "uploadLogs"))

#============================= Global Variables ===============================
# 
#   IP      :  (str)     :   IP address the server is run on
#   PORT    :  (int)     :   Port the server is accessed through
#   SIZE    :  (int)     :   Buffer size (in bytes) of the server  
#   FORMAT  :  (str)     :   Encoding format of the server
#
#------------------------------------------------------------------------------
IP = "localhost"
PORT = 4450
SIZE = 1024
RETRYLIMIT = 5
FORMAT = "utf-8"
LOCK = threading.Lock()

# Async Client Handler
class ClientThread(threading.Thread):   
    # Constructor
    def __init__(self, ip, port, sock):
        self.ip = ip                            # IP address of the socket server
        self.port = port                        # Port of the socket server
        self.sock = sock                        # Server socket
        threading.Thread.__init__(self)         # Execute async run(self) method
        print(" > New client thread started on " + ip + ":" + str(port))
    
    #--------------------------------------------------------------------------
    # Threading run() method
    # Purpose:  Handles the intents of a connected client by mapping requests to server responses
    # Pre:      Initialized ClientThread, invoked on new client connection to server
    # Exit:     Terminates server connection to client by closing the socket
    #--------------------------------------------------------------------------
    def run(self):
        verbose = True                          # Display communication in the terminal
        userConnected = True                    # Maintains functionality of the running thread, when set to false connection is terminating and socket closes
        userAuth = False                        # Prevents execution of main while loop in this run method until user credentials are authenticated
        self.sendIt("LOGIN",[],verbose=verbose, verboseText=" > Requesting login credentials.") # Prompt the client for login credentials upon connection

        #===================================== LOGIN Logic ===================================================
        #-----------------------------------------------------------------------------------------------------
        #
        #            Server                                              Client
        #   1   Sends "LOGIN@"                      --->        <Enters authentication loop>
        #   2   <Checks credentials for auth>       <---        Sends "<users>@<password>"
        #   3   Auth Success: sends "ACCEPT"        --->        <Waits for welcome message, exits auth loop>
        #   3   Auth Fail:    sends "REJECT"        --->        <Prints error, reprompts for credentials>
        #                                                       <Does NOT wait for second message>
        #   4   Auth Success: sends "OK@Welcome"    --->        <Sends welcome message using to client>
        #
        #----------------------------------------------------------------------------------------------------

        # Loop continues provided client has not disconnected
        # Server recognizes disconnects via the LOGOUT command
        while (userConnected):
            credentials = self.sock.recv(SIZE).decode(FORMAT)   # In response to LOGIN@ request, client transmits credentials to authenticate
            user, password = credentials.split("@")             # Split credentials from "username@password" into seperate (str) variables

            if verbose:
                print(f" > {user} has requested to log in.")

            # Iterate through the _users_ dict to determine if supplies credentials match a user:password pair
            for key, value in _users_.items():
                if key == user and value == password:
                    userAuth = True                                             # Enables entry into main while loop of run method for ClientHandler
                    self.sendIt("ACCEPT",[],verbose=verbose, verboseText=f" > Accepting {user}'s credentials.") # Send a response to the client to vaidate client-side authentication was successful
                    currentDir = os.path.join(_userfiles_, user)                # Setting the current directory to the user's directory
                    if not os.path.isdir(currentDir):                           # If the user doesn't have a directory yet...
                        os.mkdir(currentDir)                                    # make one

                    print(" > " + user + " has successfully logged in.")
                    break                                       

            # If credential pair was not found in _users_ dict, a response needs to be sent to client
            # Because userAuth is false, the main while loop will not be entered and server will wait for new credentials
            if(not userAuth):
                self.sendIt("REJECT",["Invalid username or password."], verbose=verbose, verboseText=f" > {user} failed login attempt.") # Sending anything other than ACCEPT will cause client to loop back into resending credentials
                print(" > " + user + " failed login attempt.")  

            # Once user credentials are authenticated, the server begins to accept client requests
            # This loop will run until the LOGOUT command is transmitted
            while(userAuth):
                #========================================= Main Command Flow Control #==============================================
                #-------------------------------------------------------------------------------------------------------------------
                #
                #                        Server                                                 Client
                #      1      <Seperates command and args>              <---   Sends "<command>@<arg>" from client intent
                #      2      <Executes command control block>
                #      3      Sends "OK@<response>" upon completion     --->   <Displays message to client. Prompts for new command>
                #
                #--------------------------------------------------------------------------------------------------------------------
                
                # Receive client intent in "<cmd>@<arg1>@<arg2>@....<argN>" format
                data = self.sock.recv(SIZE).decode(FORMAT).split("@")   
                cmd = data[0]                   # Used to enter server flow control blocks                                           
                args = []                       # Used withing flow control blocks to perform command
                for i in range (1, len(data)):  # Capture all sent arguments
                    args.append(data[i])        # Populate list with command's arguments
                
                if verbose:
                    print(f" > User {user} requested: {cmd} with arguments: {args}")

                #-----------------------------------------------------------------------------
                #   Command:    GETDIR
                #   Args   :    []
                #   Purpose:    Client requests the structure of the current directory
                #   Returns:    Sends a dictionary containing current directory's subdirs and files
                #   Status :    
                #-----------------------------------------------------------------------------
                if cmd == "GETDIR":
                    dirContent = self.getDirectory(currentDir)
                    if currentDir != os.path.join(_userfiles_, user) and currentDir != _sharedfiles_:
                        dirContent["dirs"].insert(0,"..")
                    send_data = pickle.dumps(dirContent)
                    if verbose:
                        print(f" > Sending directory structure for: {currentDir}.")
                    self.sock.send(send_data)
                
                #-----------------------------------------------------------------------------
                #   Command:    CHANGEDIR
                #   Args   :    [dirname]
                #   Purpose:    Client requests to navigate to another directory.  Must be navigable from current directory (i.e. no jumping to root or bottom of tree).
                #   Returns:    Sends the client the new directory tree once dir's changed or FAIL@message.
                #   Status :    
                #-----------------------------------------------------------------------------
                if cmd == "CHANGEDIR":
                    navigableDirs = [x for x in os.listdir(currentDir) if not os.path.isfile(x)]                # Get a list of directorys in the current directory
                    if args[0] == "..":                                                                         # If the user wants to navigate up
                        if currentDir == os.path.join(_userfiles_, user):                                       # if we're already in the user's top directory
                            self.sendIt("FAIL",["Already at root, cannot navigate higher."], verbose=verbose, verboseText=f" > {user} (somehow) attempted to escape their home directory.  This shouldn't be possible.")
                        else:
                            currentDir = os.path.abspath(os.path.join(currentDir, os.pardir))
                            dirContent = self.getDirectory(currentDir)
                            if currentDir != os.path.join(_userfiles_, user):
                                dirContent["dirs"].insert(0,"..")
                            self.sendIt("SUCCESS",[currentDir],verbose=verbose, verboseText=f" > {user} navigated to {currentDir}.")
                    elif args[0] == "home":
                        currentDir = os.path.join(_userfiles_, user)
                        self.sendIt("SUCCESS",[currentDir],verbose=verbose, verboseText=f" > {user} navigated to {currentDir}.")
                    elif args[0] == "shared":
                        currentDir = _sharedfiles_
                        self.sendIt("SUCCESS",[currentDir],verbose=verbose, verboseText=f" > {user} navigated to {currentDir}.")
                    elif args[0] in navigableDirs:
                        currentDir = os.path.join(currentDir, args[0])
                        self.sendIt("SUCCESS",[currentDir],verbose=verbose, verboseText=f" > {user} navigated to {currentDir}.")
                    else:
                        self.sendIt("FAIL", ["Attempted to navigate to an unknown directory."], verbose=verbose, verboseText=f" > {user} attempted to navigate to an unknown directory: {args[0]}.")

                #-----------------------------------------------------------------------------
                #   Command:    LOGOUT
                #   Args   :    []
                #   Purpose:    Terminates both while loops causing the closing of the socket
                #   Status :    100% TODO Remove me
                #-----------------------------------------------------------------------------
                if cmd == "LOGOUT":
                    userConnected = False
                    break
                
                #-----------------------------------------------------------------------------
                #   Command:    UPLOAD
                #   Args   :    [filename, filesize]
                #   Purpose:    Server receives the specified file to the current working directory of the socket
                #   Status :    TODO
                #-----------------------------------------------------------------------------
                elif cmd == "UPLOAD":
                    filesize = int(args.pop())
                    filename = args.pop()
                    filepath = os.path.join(currentDir, filename)
                    
                    print(" > Uploading " + filename)

                    _fileDownloads_[filepath] = 0
                    with open(os.path.join(_location_, "files.json"), 'w') as outFile:
                        json.dump(_fileDownloads_, outFile)

                    bytesReceived = 0      # Compared to the filesze to determine when transmission is complete
                    transferRows = []      # List of lists to capture the row data for generating a CSV file of data transfer rates

                    progressBar = tqdm.tqdm(range(filesize), f" > Sending {filename}", unit="B", unit_scale=True, unit_divisor=SIZE)
                    
                    log = []
                    timeStart = time.perf_counter()
                    f = open(filepath, "wb")

                    while bytesReceived < int(filesize):
                        bytesRead = self.sock.recv(SIZE)  
                        delta = time.perf_counter() - timeStart

                        bps = (bytesReceived / 1000000) / delta
                        transferRows.append([delta, bps])
                        
                        alexBPS = bytesReceived/delta
                        temp = {}
                        temp["bps"] = alexBPS
                        temp["time"] = delta
                        log.append(temp)

                        f.write(bytesRead)
                        bytesReceived += len(bytesRead)
                        progressBar.update(len(bytesRead))

                    progressBar.close()
                    f.close()

                    with open(os.path.join(_location_,"uploadLogs",f"{filename}.csv"), 'w') as outFile:
                        outFile.write(f"Time,Bytes Per Second\n")
                        for i in log:
                            outFile.write(f"{i['time']},{i['bps']}\n")
                    
                    if os.path.getsize(filepath) == filesize:
                        self.sendIt("SUCCESS", [f"File {filename} was transferred."], verbose=verbose, verboseText=f" > {filename} was successfully saved in {filepath}.")
                    else:
                        self.sendIt("FAIL",[f"File {filename} was not received in its entirety."], verbose=verbose, verboseText=f" > Upload failed, only received {bytesReceived} bytes of {filesize}.")

                    #self.makeGraph(transferRows, filename, True)  # True denotes uploaded file

                #-----------------------------------------------------------------------------
                #   Command:    DOWNLOAD
                #   Args   :    [filename]
                #   Purpose:    Server sends the specified file to the current working directory of the client
                #   Status :    75% TODO - Needs testing.
                #-----------------------------------------------------------------------------
                elif cmd == "DOWNLOAD":
                    dirsAndFiles = self.getDirectory(currentDir)
                    if args[0] in dirsAndFiles["files"]:
                        filepath = os.path.join(currentDir, args[0])
                        baseFilename = os.path.basename(args[0])
                        
                        if filepath in _fileDownloads_.keys():
                            _fileDownloads_[filepath] += 1
                        else:
                            _fileDownloads_[filepath] = 1

                        
                        bytesSent = 0
                        fileSize = os.path.getsize(filepath)
                        self.sendIt("SUCCESS", [fileSize], verbose=verbose, verboseText=f" > Sending {user} file: {baseFilename}.")
                        progressBar = tqdm.tqdm(range(fileSize), f" > Sending {args[0]}", unit="B", unit_scale=True, unit_divisor=SIZE)
                        with open(filepath, 'rb') as inFile:
                            start = time.perf_counter()
                            
                            log = []
                            while bytesSent < fileSize:
                                bytesRead = inFile.read(SIZE)
                                self.sock.send(bytesRead)
                                
                                delta = time.perf_counter() - start
                                bps = (bytesSent*8)/delta
                                temp = {}
                                temp["bps"] = str(bps)
                                temp["time"] = delta
                                log.append(temp)
                                bytesSent += len(bytesRead)
                                progressBar.update(len(bytesRead))
                        progressBar.close()

                        with open(os.path.join(_location_,"downloadLogs",f"{args[0]}.csv"), 'w') as outFile:
                            outFile.write(f"Time,Bytes Per Second\n")
                            for i in log:
                                outFile.write(f"{i['time']},{i['bps']}\n")
                        
                        with open(os.path.join(_location_, "files.json"), 'w') as outFile:
                            json.dump(_fileDownloads_, outFile)

                    else:
                        self.sendIt("FAIL",[f"Could not find file: {baseFilename}"], verbose=verbose, verboseText=f" > {user} requested a file {baseFilename} that doesn't exist in {currentDir}.")
                
                #-----------------------------------------------------------------------------
                #   Command:    DELETE
                #   Args   :    [directory_name] or [file_name]
                #   Purpose:    Deletes the supplied directory and all it contains
                #   Status :    50% TODO Needs to evaluate based on socket's current working directory, not _location_
                #-----------------------------------------------------------------------------
                elif cmd == "DELETE":
                    toDelete = os.path.join(currentDir, args[0])
                    if os.path.exists(toDelete):
                        if not os.path.isfile(toDelete):
                            shutil.rmtree(toDelete)
                        else:
                            os.remove(toDelete)
                        self.sendIt("SUCCESS",[f"{args[0]} has been deleted."], verbose=verbose, verboseText=f" > Deleted {args[0]} in {currentDir}.")
                    else:
                        self.sendIt("FAIL",[f"Could not find {toDelete}."], verbose=verbose, verboseText=f" > Could not find {args[0]} in {currentDir}.")

                #-----------------------------------------------------------------------------
                #   Command:    MKDIR
                #   Args   :    [directory_name]
                #   Purpose:    Creates a new directory at the current working directory
                #   Status :    100%
                #-----------------------------------------------------------------------------
                elif cmd == "MKDIR":
                    newDir = args[0]
                    dirContent = self.getDirectory(currentDir)
                    if newDir not in dirContent["dirs"]:
                        os.mkdir(os.path.join(currentDir,newDir))
                        self.sendIt("SUCCESS",[f"New Directory {newDir} was created."], verbose=verbose, verboseText=f" > Created {newDir} under {currentDir}.")
                    else:
                        self.sendIt("FAIL", [f"The directory {newDir} aleady exists."], verbose=verbose, verboseText=f" > {newDir} already exists in {currentDir}.")
                
                #-----------------------------------------------------------------------------
                #   Command:    RENAME
                #   Args   :    [oldName]@[newName]
                #   Purpose:    This lets the user rename a file or directory.
                #   Status :    100%
                #-----------------------------------------------------------------------------
                elif cmd == "RENAME":
                    os.rename(os.path.join(currentDir, args[0]), os.path.join(currentDir, args[1]))
                    dirsAndFiles = self.getDirectory(currentDir)
                    if args[1] in dirsAndFiles["files"] or args[1] in dirsAndFiles["dirs"]:
                        self.sendIt("SUCCESS",[f"Renamed {args[0]} to {args[1]}"], verbose=verbose, verboseText=f" > Renamed {args[0]} to {args[1]}")
                    else:
                        self.sendIt("FAIL", [f"Failed to rename {args[0]} to {args[1]}"], verbose=verbose, verboseText=f" > Failed to rename {args[0]} to {args[1]}")

                #-----------------------------------------------------------------------------
                #   Command:    INFO
                #   Args   :    [filename]
                #   Purpose:    Requests info about a file: file name, size, upload date and time, number of downloads.
                #   Status :    
                #-----------------------------------------------------------------------------
                elif cmd == "INFO":
                    dirsAndFiles = self.getDirectory(currentDir)
                    filepath = os.path.join(currentDir, args[0])
                    if args[0] in dirsAndFiles["files"]:
                        creationEpochTime = os.path.getctime(filepath)
                        fileSize = os.path.getsize(filepath)
                        numDownloads = _fileDownloads_[filepath]
                        self.sendIt("SUCCESS", [creationEpochTime, fileSize, numDownloads], verbose=verbose, verboseText=f" > Sending info for {args[0]} in {currentDir}.")
                    else:
                        self.sendIt("FAIL", [f"Could not find {args[0]} in the current directory."], verbose=verbose, verboseText=f" > {args[0]} does not exist in {currentDir}")

                #TESTING
                #TASK
                elif cmd == "TASK":
                    self.sendIt("OK",["CREATE new file on the server.\nLOGOUT from the server."])

        # Executes once userConnected is false
        # Close the socket and end the running loop 
        self.sock.close()
        print(f" > Closing connection thead with {user} at {self.ip} on port {self.port}")

    def getDirectory(self, currentDir:str) -> dict:
        return {"dirs": [x for x in os.listdir(currentDir) if not os.path.isfile(os.path.join(currentDir,x))],
                "files": [x for x in os.listdir(currentDir) if (os.path.isfile(os.path.join(currentDir,x)) and x[0] != ".") ]}
    
    def sendIt(self, command:str, args:list, seperator="@", verbose=False, verboseText="", attempts=0):
        try:
            if verbose:
                print(verboseText)
            message = command+seperator+seperator.join([str(x) for x in args])
            self.sock.send(message.encode(FORMAT))
        except Exception as e:
            if attempts < RETRYLIMIT:
                print(f"Error: Exception ({e}), retrying {attempts}/{RETRYLIMIT}...")
                self.sendIt(command, args, seperator=seperator, verbose=verbose, verboseText=verboseText, attempts=attempts+1)
            else:
                print(f"Error: Reached maximum number of transmit attempts: {RETRYLIMIT}.  Closing connection.")
                self.sock.close()


    def makeGraph(self, dataRows, filename, isUpload):
        filename = filename.split(".")
        filetype = filename[1]  
        filename = filename[0]

        fieldHeaders = ["Seconds", "MB/s"]

        if(isUpload):
            transferType = "Upload"
            targetServerDir = _upFiles_
        else:
            transferType = "Download"
            targetServerDir = _downloadFiles_

        with open("MostRecentTransfer.csv", 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fieldHeaders)
            for row in dataRows[1:]:
                csvwriter.writerow(row)

        df = pd.read_csv("MostRecentTransfer.csv")
        timestamp = datetime.datetime.now()
        timestamp = timestamp.strftime("%d-%B-%Y %H-%M-%S")
        filename = timestamp + " " + transferType + " " + filename
        filename = os.path.realpath(os.path.join(targetServerDir, filename))
        sns.lineplot(data=df, x="Seconds", y="MB/s", label= "Data Transfer Performance").set(title="" + transferType + " Data Transfer Performance", xlabel="Seconds", ylabel="Megabytes per Second (MB/s)")
        plt.savefig(filename, transparent=False)


                
# Server Startup    
server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)       # Using IPV4 and TCP connection
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    # Prevent bind() exceptions
server.bind((IP, PORT))                                         # Bind the address to the server
threads = []                                                    # TODO am I needed? Test me!
print("Starting the server")
print(f"server is listening on {IP}: {PORT}")
print("Waiting for incoming connections...")

# Load users JSON into _users_
userPath = os.path.join(_location_, "users.json")
with open(userPath, "r") as read_file:
    _users_ = json.load(read_file)
    
while True:
    server.listen() # start listening with default size backlog
    (conn, (ip,port)) = server.accept()
    print('Got connection from ', (ip,port))
    newthread = ClientThread(ip,port,conn)
    newthread.start()
    threads.append(newthread)                                   # TODO am I needed? Test me!