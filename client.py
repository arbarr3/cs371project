import sys
import tkinter as tk
from tkinter import SUNKEN, ttk
from tkinter import StringVar
import socket
import pickle
import time

class GUIWindow:
    SIZE = 1024
    FORMAT = 'utf-8'
    STDGEO = "800x600"
    
    def __init__(self, rootWindow, clientSocket:socket):
        self.rootWindow = rootWindow
        self.window = tk.Toplevel(rootWindow)
        self.window.geometry(self.STDGEO)
        self.window.protocol("WM_DELETE_WINDOW", self.dieGracefully)
        self.client = clientSocket
        self.folderImage = tk.PhotoImage(file="./images/folder.png")
        self.fileImage = tk.PhotoImage(file="./images/file.png")
        self.dirButtons = {}
        self.dirLabels = {}
        self.fileButtons = {}
        self.fileLabels = {}
        self.updateDirectory()
    
    def updateDirectory(self):
        self.client.send("GETDIR".encode(self.FORMAT))
        data = self.client.recv(self.SIZE)
        dirsAndFiles = pickle.loads(data)

        for i in [*self.dirButtons, *self.dirLabels, *self.fileButtons, *self.fileLabels]:
            i.destroy()

        c = 0
        r = 0
        print(f"received: {dirsAndFiles}")
        for dir in dirsAndFiles["dirs"]:
            self.dirButtons[dir] = tk.Button(self.window, image=self.folderImage, command=lambda d = dir: self.navigateTo(d))
            self.dirButtons[dir].grid(column=c, row=r, padx=5, pady=5)
            r += 1
            self.dirLabels[dir] = tk.Label(self.window, text=dir)
            self.dirLabels[dir].grid(column=c, row=r, padx=5)
            r -= 1

            c += 1
            if c > 5:
                c = 0
                r += 1
        for file in dirsAndFiles["files"]:
            self.fileButtons[file] = tk.Button(self.window, image=self.fileImage, command=lambda f = file: self.downloadFile(f))
            self.fileButtons[file].grid(column=c, row=r, padx=5, pady=5)
            r += 1
            self.fileLabels[file] = tk.Label(self.window, text=file)
            self.fileLabels[file].grid(column=c, row=r, padx=5)
            r -= 1

            c += 1
            if c > 5:
                c = 0
                r += 1

    def dieGracefully(self):
        self.client.send("LOGOUT".encode(self.FORMAT))
        self.rootWindow.destroy()
    
    def navigateTo(self, dir):
        print(f"trying to navigate to {dir}")
    
    def downloadFile(self, file):
        print(f"trying to download {file}")

class ConnectionWindow:
    SIZE = 1024
    FORMAT = 'utf-8'
    xpad = 5
    
    def __init__(self, rootWindow):
        self.rootWindow = rootWindow
        self.window = tk.Toplevel(rootWindow)
        self.window.protocol("WM_DELETE_WINDOW", self.dieGracefully)
        ipLabel = tk.Label(self.window, text="IPv4 Address:")
        ipLabel.grid(column=0, row=0, sticky="E", padx=self.xpad)
        portLabel = tk.Label(self.window, text="Port:")
        portLabel.grid(column=0, row=1, sticky="E", padx=self.xpad)
        userNameLabel = tk.Label(self.window, text="Username:")
        userNameLabel.grid(column=0, row=2, sticky="E", padx=self.xpad)
        passwordLabel = tk.Label(self.window, text="Password:")
        passwordLabel.grid(column=0, row=3, sticky="E", padx=self.xpad)
        self.ipEntry = tk.Entry(self.window)
        self.ipEntry.grid(column=1, row=0, padx=self.xpad)
        self.portEntry = tk.Entry(self.window)
        self.portEntry.grid(column=1, row=1, padx=self.xpad)
        self.userNameEntry = tk.Entry(self.window)
        self.userNameEntry.grid(column=1, row=2, padx=self.xpad)
        self.passwordEntry = tk.Entry(self.window)
        self.passwordEntry.config(show="*")
        self.passwordEntry.grid(column=1, row=3, padx=self.xpad)
        self.statusMessage = StringVar()
        self.statusMessageBox = tk.Message(self.window, textvariable=self.statusMessage, relief=SUNKEN)
        self.statusMessageBox.grid(row=4, columnspan=2, sticky="EW", padx=self.xpad)
        self.statusMessageBox.configure(width=300)
        connectButton = tk.Button(self.window, text="Connect")
        connectButton.grid(row=5, column=0, columnspan=2, padx=self.xpad)
        connectButton.bind("<Button-1>", self.connect)

    def connect(self, event):
        loggingIn = True
        self.ip = self.ipEntry.get()
        self.port = self.portEntry.get()
        self.client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.client.connect((self.ip, int(self.port)))
        while loggingIn:
            data = self.client.recv(self.SIZE).decode(self.FORMAT)
            if "LOGIN@" in data:
                sending = self.userNameEntry.get()+"@"+self.passwordEntry.get()
                self.client.send(sending.encode(self.FORMAT))
            elif "ACCEPT" in data:
                gW = GUIWindow(self.rootWindow, self.client)
                self.window.destroy()
                loggingIn = False
                break
            elif "REJECT" in data:
                rejectMessage = data.split("@")[1]
                self.statusMessage.set(rejectMessage)
                break
            else:
                print(f"Error: Unexpected response -> {data}")
    
    def dieGracefully(self):
        self.client.send("LOGOUT".encode(self.FORMAT))
        self.rootWindow.destroy()


        



window = tk.Tk()
window.title("CS371 Client")
window.withdraw()
cW = ConnectionWindow(window)
window.mainloop()
