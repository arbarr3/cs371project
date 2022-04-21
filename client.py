import sys
import tkinter as tk
from tkinter import SUNKEN, ttk
from tkinter import StringVar
import socket
import pickle


class UIClickable(tk.Canvas):
    def __init__(
        self,
        window,
        width = 0,
        height = 0,
        image = None,
        clickFun = None,
        hoverFun = None,
        description = None,
        descriptionText = "",
        hoverInColor = "#e1e1e1",
        hoverOutColor = "white"
        ):
        tk.Canvas.__init__(self, window, width=width, height=height)

        self.clickFun = clickFun
        self.hoverFun = hoverFun
        self.description = description
        self.descriptionText = descriptionText
        self.hoverInColor = hoverInColor
        self.hoverOutColor = hoverOutColor

        self.button = self.create_image(5,4, anchor="nw", image=image)
        
        self.tag_bind(self.button, "<Enter>", self.hover)
        self.tag_bind(self.button, "<Leave>", self.outHover)
        self.tag_bind(self.button, "<Button-1>", self.onClick)
    
    def hover(self, e):
        self.configure(bg=self.hoverInColor)
        if self.description is not None:
            self.description.set(self.descriptionText)
        if self.hoverFun is not None:
            self.hoverFun()
    def outHover(self, e):
        if self.description is not None:
            self.description.set("")
        self.configure(bg=self.hoverOutColor)
    def onClick(self, e):
        if self.clickFun is not None:
            self.clickFun()

class GUIWindow:
    SIZE = 1024
    FORMAT = 'utf-8'
    STDGEO = "800x600"
    
    def __init__(self, rootWindow, clientSocket:socket):
        self.rootWindow = rootWindow
        self.window = tk.Toplevel(rootWindow)
        self.window.geometry(self.STDGEO)
        self.window.protocol("WM_DELETE_WINDOW", self.dieGracefully)
        self.window.bind("<Return>", lambda e: self.window.focus_force())
        self.client = clientSocket
        self.folderImage = tk.PhotoImage(file="./images/folder.png")
        self.fileImage = tk.PhotoImage(file="./images/file.png")
        self.uploadImage = tk.PhotoImage(file="./images/upload.png")
        self.newFolderImage = tk.PhotoImage(file="./images/newFolder.png")
        self.dirButtons = {}
        self.dirLabels = {}
        self.dirLabelText = {}
        self.fileButtons = {}
        self.fileLabels = {}
        self.fileLabelText = {}
        self.gridColumn = 0
        self.gridRow = 0

        self.buildMenubar()
        self.updateDirectory()
    
    def buildMenubar(self):
        localRow = 0
        localCol = 0
        menuFrame = tk.Frame(self.window)
        menuFrame.grid(row=self.gridRow, column=self.gridColumn, sticky="nw")
        self.gridRow += 1

        buttonDescriptionString = tk.StringVar()
        buttonDescription = tk.Message(menuFrame, textvariable=buttonDescriptionString)
        buttonDescription.configure(width=300)

        newFolder = UIClickable(menuFrame, 36, 34, image=self.newFolderImage, clickFun=self.makeNewFolder, description=buttonDescriptionString, descriptionText="New Folder")
        newFolder.grid(row=localRow, column=localCol, sticky="nw")
        localCol += 1
        uploadButton = UIClickable(menuFrame, 36, 34, image=self.uploadImage, clickFun=self.uploadFile, description=buttonDescriptionString, descriptionText="Upload File")
        uploadButton.grid(row=localRow, column=localCol, sticky="nw")
        localCol += 1
        
        buttonDescription.grid(row=localRow, column=localCol, sticky="w")
        
        menuBarFrame = tk.Frame(self.window)
        menuBarFrame.grid(row=self.gridRow, column=self.gridColumn, sticky="nw")
        bar = tk.Canvas(menuBarFrame, height=6, width=800)
        bar.grid(row=localRow, column=localCol, sticky="nw")
        bar.create_line(5,5,790,5)
        self.gridRow += 1

    def makeNewFolder(self):
        print("make a new folder bro")
        

    def uploadFile(self):
        print("upload some shit bro")

    def updateDirectory(self):
        self.client.send("GETDIR".encode(self.FORMAT))
        data = self.client.recv(self.SIZE)
        dirsAndFiles = pickle.loads(data)

        for i in self.dirButtons.keys():
            self.dirButtons[i].destroy()
        for i in self.dirLabels.keys():
            self.dirLabels[i].destroy()
        for i in self.fileButtons.keys():
            self.fileButtons[i].destroy()
        for i in self.fileLabels.keys():
            self.fileLabels[i].destroy()

        print(f"received: {dirsAndFiles}")
        itemsFrame = tk.Frame(self.window)
        itemsFrame.grid(row=self.gridRow, column=self.gridColumn, sticky="nw")
        localRow = 0
        localCol = 0
        callback = self.window.register(self.sendFilename)
        for dir in dirsAndFiles["dirs"]:
            self.dirButtons[dir] = tk.Button(itemsFrame, image=self.folderImage, command=lambda d = dir: self.navigateTo(d))
            self.dirButtons[dir].grid(column=localCol, row=localRow, padx=5, pady=5, sticky="nw")
            localRow += 1
            self.dirLabelText[dir] = tk.StringVar(value=dir)
            self.dirLabels[dir] = tk.Entry(itemsFrame, width=9, textvariable=self.dirLabelText[dir], readonlybackground="white", disabledforeground="black", relief=tk.FLAT, state=tk.DISABLED)
            self.dirLabels[dir].grid(column=localCol, row=localRow, padx=5)
            self.dirLabels[dir].bind("<Button-1>", lambda e, f=dir: self.changeDirname(e,f))
            self.dirLabels[dir].config(validate="focusout", validatecommand=(callback, "%s", dir))
            localRow -= 1

            localCol += 1
            if localCol > 5:
                localCol = 0
                localRow += 1

        for file in dirsAndFiles["files"]:
            self.fileButtons[file] = tk.Button(itemsFrame, image=self.fileImage, command=lambda f = file: self.downloadFile(f))
            self.fileButtons[file].grid(column=localCol, row=localRow, padx=5, pady=5, sticky="nw")
            localRow += 1
            self.fileLabelText[file] = tk.StringVar(value=file)
            self.fileLabels[file] = tk.Entry(itemsFrame, width=9, textvariable=self.fileLabelText[file], readonlybackground="white", disabledforeground="black", relief=tk.FLAT, state=tk.DISABLED)
            self.fileLabels[file].grid(column=localCol, row=localRow, padx=5)
            self.fileLabels[file].bind("<Button-1>", lambda e, f=file: self.changeFilename(e,f))
            self.fileLabels[file].config(validate="focusout", validatecommand=(callback, "%s", file))
            localRow -= 1

            localCol += 1
            if localCol > 5:
                localCol = 0
                localRow += 1

    def changeFilename(self, e, file):
        self.fileLabels[file].configure(state=tk.NORMAL)
        self.fileLabels[file].select_range(0, tk.END)
    
    def changeDirname(self, e, dir):
        self.dirLabels[dir].configure(state=tk.NORMAL)
        self.dirLabels[dir].select_range(0, tk.END)

    def sendFilename(self, newName, oldName):
        self.client.send(f"RENAME@{oldName}@{newName}".encode(self.FORMAT))
        data = self.client.recv(self.SIZE).decode(self.FORMAT)
        if "SUCCESS" in data:
            return True
        else:
            print(data.split("@")[1])
            return False

    def dieGracefully(self):
        self.client.send("LOGOUT".encode(self.FORMAT))
        self.rootWindow.destroy()
    
    def navigateTo(self, dir):
        print(f"trying to navigate to {dir}")
        self.client.send(f"CHANGEDIR@{dir}".encode(self.FORMAT))
        data = self.client.recv(self.SIZE).decode(self.FORMAT)
        if "SUCCESS" in data:
            self.updateDirectory()

    
    def downloadFile(self, file):
        print(f"trying to download {file}")

class ConnectionWindow:
    SIZE = 1024
    FORMAT = 'utf-8'
    xpad = 5
    
    def __init__(self, rootWindow):
        self.client = None
        self.rootWindow = rootWindow
        self.window = tk.Toplevel(rootWindow)
        self.window.focus_force()
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
        self.window.bind("<Return>", self.connect)

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
        if self.client is not None:
            self.client.send("LOGOUT".encode(self.FORMAT))
        self.rootWindow.destroy()


        



window = tk.Tk()
window.title("CS371 Client")
window.withdraw()
cW = ConnectionWindow(window)
window.mainloop()
