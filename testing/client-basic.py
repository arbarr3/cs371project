#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Author : Ayesha S. Dina

import os
import sys
import tqdm
import socket
import pickle


IP = "localhost"
#IP = "169.254.40.234"
#IP = "10.113.32.57"
PORT = 4450
ADDR = (IP,PORT)
SIZE = 1024 ## byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"

def main():
    
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDR)
    while True:  ### multiple communications
        #====================== Client Recieve Logic ==========================
        #----------------------------------------------------------------------
        #----------------------------------------------------------------------
        data = client.recv(SIZE).decode(FORMAT)
        cmd, msg = data.split("@")
        if cmd == "OK":
            print(f"{msg}")
        elif cmd == "LOGIN":
            auth = False
            while(not auth):
                user = input("User: ")
                user = user.strip("\n")
                password = input("Password: ")
                password = password.strip("\n")
                attempt = user + "@" + password
                client.send(attempt.encode(FORMAT))

                response = client.recv(SIZE).decode(FORMAT)
                if response == "ACCEPT":
                    auth = True
                    data = client.recv(SIZE).decode(FORMAT)
                    cmd, msg = data.split("@")
                    if cmd == "OK":
                        print(f"{msg}")
                else:
                    print("Invalid, try again")
        elif cmd == "DISCONNECTED":
            print(f"{msg}")
            break
                

        #====================== Client Transmit Logic ==========================
        #----------------------------------------------------------------------
        #----------------------------------------------------------------------
        data = input("> ") 
        cmd = data.strip("\n")

        if cmd == "TASK":
            client.send(cmd.encode(FORMAT))
        elif "UPLOAD@" in cmd:
            #filename = "Test.jpg"
            filename = "371Test.txt"
            filesize = os.path.getsize(filename)
            cmd += filename + "@" + str(filesize)
            client.sendall(cmd.encode(FORMAT))
            
            print("> Sending " + filename + " of size " + str(filesize) + " bytes")
            bytes_sent = 0

            f = open(filename, "rb")
            while bytes_sent < filesize:
                bytes_read = f.read(SIZE)
                client.send(bytes_read)
                bytes_sent += len(bytes_read)
            f.close()

        elif "DELFILE@" in cmd:
            client.send(cmd.encode(FORMAT))
        elif "DELDIR@" in cmd:
            client.send(cmd.encode(FORMAT))
        elif "MKDIR@" in cmd:
            client.send(cmd.encode(FORMAT))
        elif cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break

    print("Disconnected from the server.")
    client.close() ## close the connection

if __name__ == "__main__":
    main()