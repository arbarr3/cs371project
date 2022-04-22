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
import csv
import os
import sys
import time               # Used for filepath referencing
import tqdm             # Used to display file transfer progess within terminal
import shutil           # Used for deleting directories
import socket           # Used to implement python socket networking functionality
import threading        # Used to grant each client connection a seperate thread
import pickle
import json             # Used to access the user plain text file for authentication

#============================= Private Variables ===============================
# 
#   _location_ :  (str)   :   Defines the server root as the real filepath of the current working directory
#   _users_    :  (Dict)  :   Plain text dictory of user:password strings
#   _dirTree_  :  (List)  :   Lists the files and directories of the entire server  
#
#------------------------------------------------------------------------------
_location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

_userfiles_ = os.path.join(_location_, "users")
if not os.path.isdir(_userfiles_):
    os.mkdir(_userfiles_)

_users_ = os.path.join(_location_, "users.json")
_dirTree_ = [ 
    {
        "dir1": [
            {
                "dir1Subdir1": [],
                "dir1Subdir2": []
            },
            "dir1File1.txt"
            "dir1File2.jpg"
        ],
        "dir2": [],
        "dir3": []
    },
    "file1.txt",
    "file2.mp3",
    "file3.jpg"
]

#============================= Global Variables ===============================
# 
#   IP      :  (str)     :   IP address the server is run on
#   PORT    :  (int)     :   Port the server is accessed through
#   SIZE    :  (int)     :   Buffer size (in bytes) of the server  
#   FORMAT  :  (str)     :   Encoding format of the server
#
#------------------------------------------------------------------------------
IP = "localhost"
#IP = "10.113.32.63"
PORT = 4450
SIZE = 1024
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
        userConnected = True                    # Maintains functionality of the running thread, when set to false connection is terminating and socket closes
        userAuth = False                        # Prevents execution of main while loop in this run method until user credentials are authenticated
        self.sock.send("LOGIN@".encode(FORMAT)) # Prompt the client for login credentials upon connection

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

            # Iterate through the _users_ dict to determine if supplies credentials match a user:password pair
            for key, value in _users_.items():
                if key == user and value == password:
                    userAuth = True                                             # Enables entry into main while loop of run method for ClientHandler
                    self.sock.send("ACCEPT".encode(FORMAT))                     # Send a response to the client to vaidate client-side authentication was successful                    
                    currentDir = os.path.join(_userfiles_, user)                # Setting the current directory to the user's directory
                    if not os.path.isdir(currentDir):                           # If the user doesn't have a directory yet...
                        os.mkdir(currentDir)                                    # make one

                    print(" > " + user + " has successfully logged in")
                    break                                       

            # If credential pair was not found in _users_ dict, a response needs to be sent to client
            # Because userAuth is false, the main while loop will not be entered and server will wait for new credentials
            if(not userAuth):
                self.sock.send("REJECT@Invalid username or password.".encode(FORMAT))   # Sending anything other than ACCEPT will cause client to loop back into resending credentials
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

                #-----------------------------------------------------------------------------
                #   Command:    GETDIR
                #   Args   :    []
                #   Purpose:    Client requests the structure of the current directory
                #   Returns:    Sends a dictionary containing current directory's subdirs and files
                #   Status :    
                #-----------------------------------------------------------------------------
                if cmd == "GETDIR":
                    dirContent = self.getDirectory(currentDir)
                    if currentDir != os.path.join(_userfiles_, user):
                        dirContent["dirs"].insert(0,"..")
                    print(f"sending: {dirContent}")
                    send_data = pickle.dumps(dirContent)
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
                            self.sock.send("FAIL@Already at root, cannot navigate higher.".encode(FORMAT))      # Tell them to knock that l337 h4X0r shit off
                        else:
                            currentDir = os.path.abspath(os.path.join(currentDir, os.pardir))
                            dirContent = self.getDirectory(currentDir)
                            if currentDir != os.path.join(_userfiles_, user):
                                dirContent["dirs"].insert(0,"..")
                            self.sock.send(f"SUCCESS@{currentDir}".encode(FORMAT))
                    elif args[0] in navigableDirs:
                        currentDir = os.path.join(currentDir, args[0])
                        self.sock.send(f"SUCCESS@{currentDir}".encode(FORMAT))
                    else:
                        self.sock.send("FAIL@Attempted to navigate to unknown directory.".encode(FORMAT))

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

                    #filepath = os.path.join(os.getcwd(), "bar")
                    #filepath = os.path.join(filepath, filename)
                    filepath = os.path.join(currentDir, filename)
                    print(" > Attempting to upload " + filename + " to " + filepath)

                    bytesReceived = 0      # Compared to the filesze to determine when transmission is complete
                    transferRows = []    # List of lists to capture the row data for generating a CSV file of data transfer rates

                    timeStart = time.perf_counter()

                    progressBar = tqdm.tqdm(range(filesize), f" > Sending {filename}", unit="B", unit_scale=True, unit_divisor=SIZE)
                    
                    f = open(filepath, "wb")

                    while bytesReceived < int(filesize):
                        bytesRead = self.sock.recv(SIZE)  
                        delta = time.perf_counter() - timeStart
                        bps = (bytesReceived / 1000000) / delta
                        transferRows.append([delta, bps])
                        f.write(bytesRead)
                        bytesReceived += len(bytesRead)
                        progressBar.update(len(bytesRead))




                    #while bytes_received < int(filesize):
                    #    bytes_read = self.sock.recv(SIZE)                       # Read 1024 bytes from the socket (receive)
                    #    timeStamp = round(time.perf_counter() - timeStart, 1)
                    #    countBytesRead = len(bytes_read)                        # Write to the file the bytes we just received
                    #    transferRows.append([timeStamp, countBytesRead])        # Add this current data transfer as a data point to data list#

                    #    f.write(bytes_read)

                    #    bytes_received += countBytesRead
                    #    progressBar.update(len(bytes_read))
                    progressBar.close()
                    f.close()

                    send_data = "OK@File " + filename + " was transferred"
                    self.sock.send(send_data.encode(FORMAT))
                    self.makeCSV(transferRows, "UploadServerView")

                #-----------------------------------------------------------------------------
                #   Command:    DOWNLOAD
                #   Args   :    [filename]
                #   Purpose:    Server sends the specified file to the current working directory of the client
                #   Status :    75% TODO - Needs testing.
                #-----------------------------------------------------------------------------
                elif cmd == "DOWNLOAD":
                    dirsAndFiles = self.getDirectory(currentDir)
                    if args[0] in dirsAndFiles["files"]:
                        bytesSent = 0
                        fileSize = os.path.getsize(args[0])
                        self.sock.send(f"SUCCESS@{fileSize}".encode(FORMAT))
                        with open(os.path.join(currentDir, args[0]), 'rb') as inFile:
                            start = time.time()
                            log = []
                            while bytesSent < fileSize:
                                bytesRead = inFile.read(SIZE)
                                self.sock.send(bytesRead)
                                
                                delta = time.time() - start
                                bps = (bytesSent*8)/delta
                                temp = {}
                                temp["bps"] = str(bps)
                                temp["time"] = delta
                                log.append(temp)

                                bytesSent += len(bytesRead)
                        with open(os.path.join(_location_,"serverDownloadLog.csv"), 'a') as outFile:
                            outFile.write(f"Time,Bits Per Second,Filename,Filesize\n{log[0]['time']},{log[0]['bps']},{baseFilename},{fileSize}\n")
                            for i in log[1:]:
                                outFile.write(f"{i['time']},{i['bps']}\n")

                    else:
                        self.sock.send(f"FAIL@Could not find file: {args[0]}".encode(FORMAT))
                #-----------------------------------------------------------------------------
                #   Command:    DELFILE
                #   Args   :    [filename]
                #   Purpose:    Delete the file specified at the current location, provided the file exists
                #   Status :    33% TODO Needs validation / Edge case considerations for missing files
                #               TODO Needs to use socket's current working directory, not _location_
                #-----------------------------------------------------------------------------
                elif cmd == "DELFILE":
                    filename = args.pop()
                    if os.path.exists(_location_):
                        os.remove(filename)
                        print(" > File " + filename + " has been deleted.")
                        self.sock.send("OK@File has been deleted".encode(FORMAT))
                
                #-----------------------------------------------------------------------------
                #   Command:    DELETE
                #   Args   :    [directory_name] or [file_name]
                #   Purpose:    Deletes the supplied directory and all it contains
                #   Status :    50% TODO Needs to evaluate based on socket's current working directory, not _location_
                #-----------------------------------------------------------------------------
                elif cmd == "DELETE":
                    # dir = args.pop()
                    # dirPath = os.path.join(_location_, dir)
                    # if os.path.exists(dirPath):
                    #     shutil.rmtree(dir)
                    #     print(" > Directory " + dir + " has been deleted.")
                    #     self.sock.send("OK@Directory has been deleted".encode(FORMAT))
                    toDelete = os.path.join(currentDir, args[0])
                    if os.path.exists(toDelete):
                        if not os.path.isfile(toDelete):
                            shutil.rmtree(toDelete)
                        else:
                            os.remove(toDelete)
                        send_data = f"SUCCESS@{args[0]} has been deleted."
                    else:
                        send_data = f"FAIL@Could not find {toDelete}."
                    self.sock.send(send_data.encode(FORMAT))


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
                        send_data = f"SUCCESS@New Directory {newDir} was created."
                    else:
                        send_data = f"FAIL@The directory {newDir} aleady exists."
                    self.sock.send(send_data.encode(FORMAT))
                
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
                        send_data = f"SUCCESS@Renamed {args[0]} to {args[1]}"
                    else:
                        send_data = f"FAIL@Failed to rename {args[0]} to {args[1]}"
                    self.sock.send(send_data.encode(FORMAT))

                
                #DIR LIST (ls) TODO
                #DIR CHANGE (cd) TODO

                #TESTING
                #TASK
                elif cmd == "TASK":
                    send_data = "OK@"
                    send_data += "CREATE new file on the server.\n" 
                    send_data += "LOGOUT from the server."
                    self.sock.send(send_data.encode(FORMAT))

        # Executes once userConnected is false
        # Close the socket and end the running loop 
        self.sock.close()
        print(" > Terminating connection thead on " + self.ip + ":" + str(self.port))

    def getDirectory(self, currentDir:str) -> dict:
        return {"dirs": [x for x in os.listdir(currentDir) if not os.path.isfile(os.path.join(currentDir,x))],
                "files": [x for x in os.listdir(currentDir) if os.path.isfile(os.path.join(currentDir,x))]}
    
    def makeCSV(self, dataRows, filename):
        filename += ".csv"
        fieldHeaders = ["Microseconds", "Bytes"]
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fieldHeaders)
            for row in dataRows[1:]:
                csvwriter.writerow(row)
                
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
