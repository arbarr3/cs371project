from calendar import c
import os
import shutil
import socket
import threading
import pickle

# Define server's filepath location
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

# Global variable to store the server directory information
__dirTree__ = [
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

# Initialize global variables to define local server
IP = "localhost"
#IP = "10.113.32.57"
PORT = 4450
ADDR = (IP,PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_PATH = "server"

# Async Client Handler via Threading
class ClientThread(threading.Thread):

    # On each client initialization create a new thread
    def __init__(self, ip, port, sock):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = sock
        print(" > New client thread started on " + ip + ":" + str(port))
    
    def run(self):
        # Use the sock param to as the connection to send/receive data between this thread (the server) and the client
        self.sock.send("OK@Welcome to the server".encode(FORMAT))

        userConnected = True # Provided the user remains logged in, maintain functionality of thread
        userAuth = True #TODO change to false when authentication is added

        while (userConnected):
            # Send ACK that connection is established
            # Authenticate user TODO fix isUserAuthed above
                # Auth successfull, allow user intents
                # Auth unsuccessfull, reprompt suer
            
            while(userAuth):
                send_data = ""
                data = self.sock.recv(SIZE).decode(FORMAT).split("@")
                cmd = data[0]
                if(len(data) > 1):
                    arg = data[1]

                if cmd == "LOGOUT":
                    userConnected = False
                    break
                
                #UPLOAD
                #DOWNLOAD

                # Delete Single File
                #DELFILE@file_name
                elif cmd == "DELFILE":
                    file = arg
                    if os.path.exists(__location__):
                        os.remove(file)
                        print(" > File " + file + " has been deleted.")
                        self.sock.send("OK@File has been deleted".encode(FORMAT))
                
                # Delete Directory (and all its' contents!!!)
                #DELDIR@directory_name
                elif cmd == "DELDIR":
                    dir = arg
                    if os.path.exists(__location__):
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
                    path = os.path.join(__location__, dir)
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

                    info = pickle.dumps(__dirTree__)
                    info = bytes(f"{len(info):<{SIZE}}", 'utf-8') + info
                    self.sock.send(info)


        
        print(" > Terminating connection thead on " + self.ip + ":" + str(self.port))
        self.sock.close()

# Server Startup    
server = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # used IPV4 and TCP connection
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Prevent bind() exceptions
server.bind(ADDR) # bind the address
threads = []
print("Starting the server")
print(f"server is listening on {IP}: {PORT}")
print("Waiting for incoming connections...")
    
while True:
    server.listen() # start listening with default size backlog
    (conn, (ip,port)) = server.accept()
    print('Got connection from ', (ip,port))
    newthread = ClientThread(ip,port,conn)
    newthread.start()
    threads.append(newthread)
