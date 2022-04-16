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
import os               # Used for filepath referencing
import tqdm             # Used to display file transfer progess within terminal
import shutil
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
#IP = "10.113.32.57"
PORT = 4450
SIZE = 1024
FORMAT = "utf-8"

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

        # Loop continues provided client has not disconnected
        # Server recognizes disconnects via the LOGOUT command
        while (userConnected):                  
            credentials = self.sock.recv(SIZE).decode(FORMAT)   # In response to LOGIN@ request, client transmits credentials to authenticate
            user, password = credentials.split("@")             # Split credentials from "username@password" into seperate (str) variables

            # Iterate through the _users_ dict to determine if supplies credentials match a user:password pair
            for key, value in _users_.items():
                if key == user and value == password:
                    userAuth = True                             # Enables entry into main while loop of run method for ClientHandler
                    self.sock.send("ACCEPT".encode(FORMAT))     # Send response to client
                    print(" > " + user + " has successfully logged in")
                    break                                       

            # If credential pair was not found in _users_ dict, a response needs to be sent to client
            # Because userAuth is false, the main while loop will not be entered and server will wait for new credentials
            if(not userAuth):
                self.sock.send("REJECT".encode(FORMAT))
                print(" > " + user + " failed login attempt.")  

            # Once user credentials are authenticated, the server begins to accept client requests
            # This loop will run until the LOGOUT command is transmitted
            while(userAuth):
                self.sock.send("OK@Welcome to the server".encode(FORMAT))
                send_data = ""
                data = self.sock.recv(SIZE).decode(FORMAT).split("@")
                cmd = data[0]

                # If an argument is passed with the command, capture that as arg
                if(len(data) > 1):
                    arg = data[1]

                if cmd == "LOGOUT":
                    userConnected = False
                    break
                
                # Client UPLOAD file to server
                    # @cmd: UPLOAD@filename@filesize
                elif cmd == "UPLOAD":
                    filename = arg
                    filesize = int(data[2])
                    progressBar = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=SIZE)

                    with open(filename, "wb") as f:
                        while True:
                            # Read SIZE (1024) bytes from socket
                            bytes_read = self.sock.recv(SIZE)

                            if not bytes_read: # Nothing is recieved or transmission is over
                                break

                            f.write(bytes_read)
                            progressBar.update(len(bytes_read))

                    send_data += "OK@"
                    send_data += "I think I sent " + filename + " of size " + filesize
                    self.sock.send(send_data.encode(FORMAT))


                #DOWNLOAD
                #elif cmd == "DOWNLOAD":

                    


                # Delete Single File
                    # @cmd: DELFILE@file_name
                elif cmd == "DELFILE":
                    file = arg
                    if os.path.exists(_location_):
                        os.remove(file)
                        print(" > File " + file + " has been deleted.")
                        self.sock.send("OK@File has been deleted".encode(FORMAT))
                
                # Delete Directory (and all its' contents!!!)
                #DELDIR@directory_name
                elif cmd == "DELDIR":
                    dir = arg
                    if os.path.exists(_location_):
                        shutil.rmtree(dir)
                        print(" > Directory " + dir + " has been deleted.")
                        self.sock.send("OK@Directory has been deleted".encode(FORMAT))   

                #DIR CREATE 
                elif cmd == "MKDIR":
                    dir = arg
                    # Determine if arg is a key in the dirTree at the current dir
                    # if arg is a key in thisDict
                        # self.sock.send("NK@Error. Directory with that filename exists. Please retry.").encode(FORMAT))
                    # else (indent and do the rest)
                    path = os.path.join(_location_, dir)
                    os.mkdir(path)
                    print(" > New directory " + dir + " has been created")
                    self.sock.send("OK@New directory has been created".encode(FORMAT))
                
                #DIR LIST (ls) TODO
                #DIR CHANGE (cd) TODO

                #TESTING
                #TASK
                elif cmd == "TASK":
                    send_data += "OK@"
                    send_data += "CREATE new file on the server.\n" 
                    send_data += "LOGOUT from the server."
                    self.sock.send(send_data.encode(FORMAT))
                
                #TESTING
                #INFO send Pickled Server Directory as Python Dict
                elif cmd == "INFO":
                    send_data += "INFO@"
                    self.sock.send(send_data.encode(FORMAT))

                    info = pickle.dumps(_dirTree_)
                    info = bytes(f"{len(info):<{SIZE}}", 'utf-8') + info
                    self.sock.send(info)

        print(" > Terminating connection thead on " + self.ip + ":" + str(self.port))
        self.sock.close()

# Server Startup    
server = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # used IPV4 and TCP connection
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Prevent bind() exceptions
server.bind((IP, PORT)) # bind the address
threads = []
print("Starting the server")
print(f"server is listening on {IP}: {PORT}")
print("Waiting for incoming connections...")

userPath = os.path.join(_location_, "users.json")
with open(userPath, "r") as read_file:
    _users_ = json.load(read_file)
    
while True:
    server.listen() # start listening with default size backlog
    (conn, (ip,port)) = server.accept()
    print('Got connection from ', (ip,port))
    newthread = ClientThread(ip,port,conn)
    newthread.start()
    threads.append(newthread)
