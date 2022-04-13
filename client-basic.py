#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Author : Ayesha S. Dina

import os
import socket
import pickle


IP = "localhost"
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
        data = client.recv(SIZE).decode(FORMAT)
        cmd, msg = data.split("@")
        if cmd == "OK":
            print(f"{msg}")
        elif cmd == "DISCONNECTED":
            print(f"{msg}")
            break
        elif cmd == "INFO":
            info = b''
            receiving = True
            while(receiving):
                buffer = client.recv(16)
                bufferLen = int(buffer[:SIZE])
                info += buffer

                if(len(info)-SIZE == bufferLen):
                    print(pickle.loads(info[SIZE:]))
                    receiving = False
            break
        
        data = input("> ") 
        cmd = data.strip("\n")
        
        #cmd = data[0]

        if cmd == "TASK":
            client.send(cmd.encode(FORMAT))
        elif cmd == "INFO":
            client.send(cmd.encode(FORMAT))
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