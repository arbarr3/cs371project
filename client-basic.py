#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Author : Ayesha S. Dina

import os
import tqdm
import socket
import pickle


IP = "localhost"
IP = "10.113.32.57"
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
                
        data = input("> ") 
        cmd = data.strip("\n")

        if cmd == "TASK":
            client.send(cmd.encode(FORMAT))
        elif cmd == "INFO":
            client.send(cmd.encode(FORMAT))
        elif "UPLOAD@" in cmd:
            path = "C:/Users/crisp/Downloads/hw4.pdf"
            filename = "hw4.pdf"
            filesize = os.path.getsize(path)
            cmd += "client.py@" + str(filesize)
            client.send(cmd.encode(FORMAT))
            progressBar = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=SIZE)

            with open(path, "rb") as f:
                while True:
                    bytes_read = f.read(SIZE)
                    if not bytes_read:
                        break

                    client.sendfile(bytes_read)
                    progressBar.update(len(bytes_read))



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