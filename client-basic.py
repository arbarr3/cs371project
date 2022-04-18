#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Author : Ayesha S. Dina

import os
import tqdm
import socket
import pickle


IP = "localhost"
IP = "169.254.40.234"
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
            filename = "users.json"
            filesize = os.path.getsize(filename)
            cmd += filename + "@" + str(filesize)

            client.send(cmd.encode(FORMAT))
            #progressBar = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=SIZE)

            f = open(filename, "rb")
            l = f.read(SIZE)
            while(l):
                print("Reading...")
                client.send(l)
                print("Sent a buffer size of data...")
                l = f.read(SIZE) # TODO FIX THIS LINE
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