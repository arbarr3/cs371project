
from calendar import c
import os
import socket
import threading

# Initialize global variables to define local server
IP = "localhost"
PORT = 4450
ADDR = (IP,PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_PATH = "server"

# Client Handler
def handleClient(connection, address):

    print(f"[NEW CONNECTION] {address} connectedl.")
    connection.send("OK@Welcome to the server".encode(FORMAT))

    while True:
        data = connection.recv(SIZE).decode(FORMAT)
        data = data.split("@")
        command = data[0]

        send_data = "Ok@"

        #LOGIN PROMPT

        # Command Input Blocks
        if command == "LOGOUT":
            break

        #AUTH
        #UPLOAD
        #DOWNLOAD
        #DELETE 
        #DIR LIST (ls)
        #DIR CHANGE (cd)
