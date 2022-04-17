from cProfile import label
import tkinter as tk
from tkinter import ttk
import socket

class GUIWindow:
    def __init__(self, rootWindow, dirTree:list):
        self.window = tk.Toplevel(rootWindow)

class ConnectionWindow:
    SIZE = 1024
    FORMAT = 'utf-8'
    def __init__(self, rootWindow):
        self.rootWindow = rootWindow
        self.window = tk.Toplevel(rootWindow)
        ipLabel = tk.Label(self.window, text="IPv4 Address:")
        ipLabel.grid(column=0, row=0, sticky="E")
        portLabel = tk.Label(self.window, text="Port:")
        portLabel.grid(column=0, row=1, sticky="E")
        userNameLabel = tk.Label(self.window, text="Username:")
        userNameLabel.grid(column=0, row=2, sticky="E")
        passwordLabel = tk.Label(self.window, text="Password:")
        passwordLabel.grid(column=0, row=3, sticky="E")
        self.ipEntry = tk.Entry(self.window)
        self.ipEntry.grid(column=1, row=0)
        self.portEntry = tk.Entry(self.window)
        self.portEntry.grid(column=1, row=1)
        self.userNameEntry = tk.Entry(self.window)
        self.userNameEntry.grid(column=1, row=2)
        self.passwordEntry = tk.Entry(self.window)
        self.passwordEntry.config(show="*")
        self.passwordEntry.grid(column=1, row=3)
        connectButton = tk.Button(self.window, text="Connect")
        connectButton.grid(row=4, columnspan=2)
        connectButton.bind("<Button-1>", self.connect)

    def connect(self, event):
        loggingIn = True
        self.ip = self.ipEntry.get()
        self.port = self.portEntry.get()
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.connect((self.ip, int(self.port)))
        while loggingIn:
            data = client.recv(self.SIZE).decode(self.FORMAT)
            if "LOGIN@" in data:
                sending = self.userNameEntry.get()+"@"+self.passwordEntry.get()
                print(f"sending: {sending}")
                client.send(sending.encode(self.FORMAT))
            if "ACCEPT" in data:
                gW = GUIWindow(self.rootWindow, client)
                self.window.destroy()
                loggingIn = False
                break
            if "REJECT" in data:
                pass


        



window = tk.Tk()
window.title("CS371 Client")
window.withdraw()
cW = ConnectionWindow(window)


dirTree = [ 
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

#gW = GUIWindow(window, dirTree)

window.mainloop()
