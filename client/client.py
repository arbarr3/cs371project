from ctypes import alignment
import os
import tkinter as tk
from tkinter import SUNKEN, ttk, filedialog
from tkinter import StringVar
import socket
import pickle
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


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
        hoverOutColor = "white",
        toggleBorderColor = "red"
        ):
        tk.Canvas.__init__(self, window, width=width, height=height)

        self.clickFun = clickFun
        self.hoverFun = hoverFun
        self.description = description
        self.descriptionText = descriptionText
        self.hoverInColor = hoverInColor
        self.hoverOutColor = hoverOutColor
        self.toggleBorderColor = toggleBorderColor
        self.toggled = False

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
    def toggle(self, toggledText=""):
        if not self.toggled:
            self.toggled = True
            self.configure(bg=self.hoverInColor, highlightbackground=self.toggleBorderColor)
            self.tag_unbind(self.button,"<Leave>")
        else:
            self.toggled = False
            self.configure(bg=self.hoverOutColor, highlightbackground=self.hoverOutColor)
            self.tag_bind(self.button, "<Leave>", self.outHover)

class GUIWindow:
    SIZE = 1024
    FORMAT = 'utf-8'
    STDGEO = "800x600"
    cwd = os.getcwd()
    
    def __init__(self, rootWindow, clientSocket:socket):
        self.rootWindow = rootWindow
        self.window = tk.Toplevel(rootWindow)
        self.window.geometry(self.STDGEO)
        self.window.protocol("WM_DELETE_WINDOW", self.dieGracefully)
        self.window.bind("<Return>", lambda e: self.window.focus_force())
        self.client = clientSocket
        self.folderImage = tk.PhotoImage(file=os.path.join(self.cwd,"images", "folder.png"))
        self.fileImage = tk.PhotoImage(file=os.path.join(self.cwd,"images", "file.png"))
        self.uploadImage = tk.PhotoImage(file=os.path.join(self.cwd,"images", "upload.png"))
        self.downloadImage = tk.PhotoImage(file=os.path.join(self.cwd,"images", "download.png"))
        self.newFolderImage = tk.PhotoImage(file=os.path.join(self.cwd,"images", "newFolder.png"))
        self.deleteImage = tk.PhotoImage(file=os.path.join(self.cwd,"images", "delete.png"))
        self.infoImage = tk.PhotoImage(file=os.path.join(self.cwd,"images", "info.png"))
        self.dirButtons = {}
        self.dirLabels = {}
        self.dirLabelText = {}
        self.fileButtons = {}
        self.fileLabels = {}
        self.fileLabelText = {}
        self.gridColumn = 0
        self.gridRow = 0

        self.downloadMode = False
        self.deleteMode = False
        self.infoMode = False

        self.buildMenubar()
        self.updateDirectory()
    
    def buildMenubar(self):
        localRow = 0
        localCol = 0
        menuFrame = tk.Frame(self.window)
        menuFrame.grid(row=self.gridRow, column=self.gridColumn, sticky="nw", pady=5)
        

        buttonDescriptionString = tk.StringVar()
        buttonDescription = tk.Message(menuFrame, textvariable=buttonDescriptionString)
        buttonDescription.configure(width=300)

        newFolder = UIClickable(menuFrame, 36, 34, image=self.newFolderImage, clickFun=self.makeNewFolder, description=buttonDescriptionString, descriptionText="New Folder")
        newFolder.grid(row=localRow, column=localCol, sticky="w")
        localCol += 1
        uploadButton = UIClickable(menuFrame, 36, 34, image=self.uploadImage, clickFun=self.uploadFile, description=buttonDescriptionString, descriptionText="Upload File")
        uploadButton.grid(row=localRow, column=localCol, sticky="w")
        localCol += 1
        self.infoButton = UIClickable(menuFrame, 36, 34, image=self.infoImage, clickFun=self.getInfo, description=buttonDescriptionString, descriptionText="File Info", toggleBorderColor="blue")
        self.infoButton.grid(row=localRow, column=localCol, sticky="w")
        localCol += 1
        self.downloadButton = UIClickable(menuFrame, 36, 34, image=self.downloadImage, clickFun=self.downloadFile, description=buttonDescriptionString, descriptionText="Download File", toggleBorderColor="green")
        self.downloadButton.grid(row=localRow, column=localCol, sticky="w")
        localCol += 1
        
        buttonDescription.grid(row=localRow, column=localCol, sticky="w")
        
        self.deleteButton = UIClickable(self.window, 36, 34, image=self.deleteImage, clickFun=self.deleteObject, description=buttonDescriptionString, descriptionText="Delete")
        self.deleteButton.grid(row=self.gridRow, column=self.gridColumn, sticky="e", padx=10, pady=5)
        self.gridRow += 1
        self.gridColumn = 0
        
        
        
        menuBarFrame = tk.Frame(self.window)
        menuBarFrame.grid(row=self.gridRow, column=self.gridColumn, sticky="nw")
        bar = tk.Canvas(menuBarFrame, height=6, width=800)
        bar.grid(row=0, column=0, sticky="nw", columnspan=2)
        bar.create_line(5,5,790,5)
        self.gridRow += 1

    def downloadFile(self):
        self.downloadButton.toggle()
        self.downloadMode = self.downloadButton.toggled
    
    def deleteObject(self):
        self.deleteButton.toggle()
        self.deleteMode = self.deleteButton.toggled
    
    def getInfo(self):
        self.infoButton.toggle()
        self.infoMode = self.infoButton.toggled

    def makeNewFolder(self):
        makeFolderCallback = self.window.register(self.sendNewFolder)
        dir = str(len(self.dirButtons))
        self.dirButtons[dir] = tk.Button(self.dirsAndFilesFrame, image=self.folderImage, command=lambda d = dir: self.navigateTo(d))
        self.dirButtons[dir].grid(column=self.dirsAndFilesCol, row=self.dirsAndFilesRow, padx=5, pady=5, sticky="nw")
        self.dirsAndFilesRow += 1
        self.dirLabelText[dir] = tk.StringVar(value="New Folder")
        self.dirLabels[dir] = tk.Entry(self.dirsAndFilesFrame, width=9, textvariable=self.dirLabelText[dir], readonlybackground="white", disabledforeground="black", relief=tk.FLAT)
        self.dirLabels[dir].grid(column=self.dirsAndFilesCol, row=self.dirsAndFilesRow, padx=5)
        self.dirLabels[dir].bind("<Button-1>", lambda e, f=dir: self.changeDirname(e,f))
        self.dirLabels[dir].config(validate="focusout", validatecommand=(makeFolderCallback, "%s", dir))
        self.dirLabels[dir].focus_set()
        self.dirLabels[dir].select_range(0, tk.END)
        self.dirsAndFilesRow -= 1

    def sendNewFolder(self, folderName, dir):
        if folderName != dir:
            self.dirButtons[dir].configure(command=lambda d = folderName: self.navigateTo(d))
            self.client.send(f"MKDIR@{folderName}".encode(self.FORMAT))
            data = self.client.recv(self.SIZE).decode(self.FORMAT)
            if "SUCCESS" in data:
                self.updateDirectory()
                return True
        
            print(data.split("@")[1])
            self.dirButtons[dir].destroy()
            self.dirLabels[dir].destroy()
        return False

    def fileButtonInteraction(self, file):
        if self.deleteMode:
            self.client.send(f"DELETE@{file}".encode(self.FORMAT))
            data = self.client.recv(self.SIZE).decode(self.FORMAT)
            if "SUCCESS" in data:
                self.updateDirectory()
            else:
                print(data) # TODO Handle this better
        
        elif self.infoMode:
            self.client.send(f"INFO@{file}".encode(self.FORMAT))
            data = self.client.recv(self.SIZE).decode(self.FORMAT)
            epochTime, fileSize, downloads = data.split("@")[1:]
            
            popup = tk.Toplevel(self.window)
            popup.title(f"{file} Info")

            timeLabel = tk.Label(popup, text="Created:")
            timeLabel.grid(row=0, column=0, sticky="nw", padx=5, pady=2)
            timeLabelValue = tk.Label(popup, text=time.ctime(float(epochTime)))
            timeLabelValue.grid(row=0, column=1, sticky="nw", padx=5, pady=2)
            sizeLabel = tk.Label(popup, text="File size:")
            sizeLabel.grid(row=1, column=0, sticky="nw", padx=5, pady=2)
            sizeLabelValue = tk.Label(popup, text=self.stringifyFileSize(int(fileSize),"B"))
            sizeLabelValue.grid(row=1, column=1, sticky="nw", padx=5, pady=2)
            downloadsLabel = tk.Label(popup, text="Downlods:")
            downloadsLabel.grid(row=2, column=0, sticky="nw", padx=5, pady=2)
            downloadsLabelValue = tk.Label(popup, text=downloads)
            downloadsLabelValue.grid(row=2, column=1, sticky="nw", padx=5, pady=2)
            
            logpaths = [f"./uploadLogs/{file}.csv", f"./downloadLogs/{file}.csv"]
            lrow = 3
            lcol = 0
            for path in logpaths:
                if os.path.exists(path):
                    xVals = []
                    yVals = []
                    with open(path, 'r') as inFile:
                        trash = inFile.readline()
                        for line in inFile:
                            line = line.strip().split(',')
                            xVals.append(float(line[0]))
                            yVals.append(float(line[1]))
                            
                    figure = plt.Figure(figsize=(6,5), dpi=100)
                    ax = figure.add_subplot()
                    ax.clear()
                    ax.plot(xVals,yVals, 'r')
                    title = f"Upload Transfer Rate" if "upload" in path else "Download Transfer Rate"
                    ax.set_title(title)
                    ax.set_xlabel("Time (seconds)")
                    ax.set_ylabel("Transfer Rate (bits/second)")
                    chartType = FigureCanvasTkAgg(figure, master=popup)
                    chartType.draw()
                    chartType.get_tk_widget().grid(row=lrow, column=lcol, columnspan=2)
                    lrow += 1
                    



                

        
        elif self.downloadMode:
            outFile = filedialog.asksaveasfile(initialfile=file, mode="wb")
            
            self.client.send(f"DOWNLOAD@{file}".encode(self.FORMAT))
            data = self.client.recv(self.SIZE).decode(self.FORMAT)
            
            log = []
            if "SUCCESS" in data:
                bytesReceived = 0
                fileSize = int(data.split("@")[1])
                start = time.perf_counter()

                while bytesReceived < fileSize:
                    
                    bytesRead = self.client.recv(self.SIZE)
                    delta = time.perf_counter() - start
                    
                    bps = (len(bytesRead) * 8)/delta
                    temp = {}
                    temp["bps"] = bps
                    temp["time"] = delta
                    log.append(temp)

                    outFile.write(bytesRead)
                    bytesReceived += len(bytesRead)

            else:
                print(data) # TODO Notify the user that this failed and why
                outFile.close()
                return
            outFile.close()

            with open(f"./downloadLogs/{file}.csv", "w") as outFile:
                outFile.write("Time,Bits Per Second\n")
                for i in log:
                    outFile.write(f"{i['time']},{i['bps']}\n")

        else:
            print("Do something here")


    def uploadFile(self):
        filename = filedialog.askopenfilename()
        if filename != "":
            fileSize = os.path.getsize(filename)
            baseFilename = os.path.basename(filename)
            self.client.send(f"UPLOAD@{baseFilename}@{fileSize}".encode(self.FORMAT))
            bytesSent = 0

            fileFrame = tk.Frame(self.dirsAndFilesFrame, height=90, width=90)
            fileFrame.grid(row=self.dirsAndFilesRow, column=self.dirsAndFilesCol, padx=5, sticky="nw")
            self.dirsAndFilesRow += 1

            speedVal = tk.StringVar(value="Uploading\nat\n0 bps")
            uploadSpeed = tk.Label(fileFrame, textvariable=speedVal)
            uploadSpeed.grid(row=0, column=0, sticky="n")
            progress = ttk.Progressbar(fileFrame, length=90)
            progress.grid(row=1, column=0, padx=5, pady=25, sticky="s")          
            
            progressLabel = tk.Label(self.dirsAndFilesFrame, text=filename.split("/")[-1])
            progressLabel.grid(row=self.dirsAndFilesRow, column=self.dirsAndFilesCol, padx=5, sticky="nw")
            
            with open(filename, 'rb') as inFile:
                start = time.perf_counter()
                log = []
                while bytesSent < fileSize:
                    
                    bytesRead = inFile.read(self.SIZE)
                    self.client.send(bytesRead)
                    delta = time.perf_counter() - start
                    
                    if int(delta) % 2 == 0:
                        progress["value"] = (bytesSent/fileSize)*100
                        self.window.update()

                    bps = int((bytesSent*8)/delta)
                    temp = {}
                    temp["bps"] = str(bps)
                    temp["time"] = delta
                    log.append(temp)

                    displayBPS = self.stringifyFileSize(bps, "bps")
                    # if bps // 2**20 > 0:
                    #     displayBPS = str(bps//2**20)+" Mbps"
                    # elif bps // 2**10 > 0:
                    #     displayBPS = str(bps//2**10)+" kbps"
                    # else:
                    #     displayBPS = str(bps)+" bps"


                    speedVal.set(value=f"Uploading\nat\n{displayBPS}")
                    
                    bytesSent += len(bytesRead)
            data = self.client.recv(self.SIZE).decode(self.FORMAT)
            
            with open(f"./uploadLogs/{baseFilename}.csv", "w") as outFile:
                outFile.write("Time,Bits Per Second\n")
                for i in log:
                    outFile.write(f"{i['time']},{i['bps']}\n")
            
            if "OK" in data:
                fileFrame.destroy()
                progressLabel.destroy()
                self.updateDirectory()

    def stringifyFileSize(self, value, units:str):
        if value // 2**20 > 0:
            return str(value//2**20)+" M"+units
        elif value // 2**10 > 0:
            return str(value//2**10)+" k"+units
        else:
            return str(value)+" "+units

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
        self.dirsAndFilesFrame = tk.Frame(self.window)
        self.dirsAndFilesFrame.grid(row=self.gridRow, column=self.gridColumn, sticky="nw", columnspan=2)
        self.dirsAndFilesRow = 0
        self.dirsAndFilesCol = 0
        
        renameEntryCallback = self.window.register(self.rename)
        for dir in dirsAndFiles["dirs"]:
            self.dirButtons[dir] = tk.Button(self.dirsAndFilesFrame, image=self.folderImage, command=lambda d = dir: self.navigateTo(d))
            self.dirButtons[dir].grid(column=self.dirsAndFilesCol, row=self.dirsAndFilesRow, padx=5, pady=5, sticky="nw")
            self.dirsAndFilesRow += 1
            self.dirLabelText[dir] = tk.StringVar(value=dir)
            self.dirLabels[dir] = tk.Entry(self.dirsAndFilesFrame, width=9, textvariable=self.dirLabelText[dir], readonlybackground="white", disabledforeground="black", relief=tk.FLAT, state=tk.DISABLED)
            self.dirLabels[dir].grid(column=self.dirsAndFilesCol, row=self.dirsAndFilesRow, padx=5)
            self.dirLabels[dir].bind("<Button-1>", lambda e, f=dir: self.changeDirname(e,f))
            self.dirLabels[dir].config(validate="focusout", validatecommand=(renameEntryCallback, "%s", dir))
            self.dirsAndFilesRow -= 1

            self.dirsAndFilesCol += 1
            if self.dirsAndFilesCol > 5:
                self.dirsAndFilesCol = 0
                self.dirsAndFilesRow += 2

        for file in dirsAndFiles["files"]:
            self.fileButtons[file] = tk.Button(self.dirsAndFilesFrame, image=self.fileImage, command=lambda f = file: self.fileButtonInteraction(f))
            self.fileButtons[file].grid(column=self.dirsAndFilesCol, row=self.dirsAndFilesRow, padx=5, pady=5, sticky="nw")
            self.dirsAndFilesRow += 1
            self.fileLabelText[file] = tk.StringVar(value=file)
            self.fileLabels[file] = tk.Entry(self.dirsAndFilesFrame, width=9, textvariable=self.fileLabelText[file], readonlybackground="white", disabledforeground="black", relief=tk.FLAT, state=tk.DISABLED)
            self.fileLabels[file].grid(column=self.dirsAndFilesCol, row=self.dirsAndFilesRow, padx=5)
            self.fileLabels[file].bind("<Button-1>", lambda e, f=file: self.changeFilename(e,f))
            self.fileLabels[file].config(validate="focusout", validatecommand=(renameEntryCallback, "%s", file))
            self.dirsAndFilesRow -= 1

            self.dirsAndFilesCol += 1
            if self.dirsAndFilesCol > 5:
                self.dirsAndFilesCol = 0
                self.dirsAndFilesRow += 2

    def changeFilename(self, e, file):
        self.fileLabels[file].configure(state=tk.NORMAL)
        self.fileLabels[file].focus_set()
        self.fileLabels[file].select_range(0, tk.END)
        self.window.update()
    
    def changeDirname(self, e, dir):
        self.dirLabels[dir].configure(state=tk.NORMAL)
        self.dirLabels[dir].focus_set()
        self.dirLabels[dir].select_range(0, tk.END)
        self.window.update()

    def rename(self, newName, oldName):
        self.client.send(f"RENAME@{oldName}@{newName}".encode(self.FORMAT))
        data = self.client.recv(self.SIZE).decode(self.FORMAT)
        if "SUCCESS" in data:
            #widget.configure(command=lambda d = newName: self.navigateTo(d))
            if oldName in self.dirButtons.keys():
                self.dirButtons[oldName].configure(command=lambda d = newName: self.navigateTo(d))
                
            elif oldName in self.fileButtons.keys():
                self.fileButtons[oldName].configure(command=lambda d = newName: self.navigateTo(d))
            return True
        else:
            print(data.split("@")[1])
            return False

    def dieGracefully(self):
        try:
            self.client.send("LOGOUT".encode(self.FORMAT))
        except:
            print("Warning: Problem closing the connection.")
        self.rootWindow.destroy()
    
    def navigateTo(self, dir):
        if self.deleteMode and dir != "..":
            self.client.send(f"DELETE@{dir}".encode(self.FORMAT))
        else:
            print(f"trying to navigate to {dir}")
            self.client.send(f"CHANGEDIR@{dir}".encode(self.FORMAT))
        data = self.client.recv(self.SIZE).decode(self.FORMAT)
        if "SUCCESS" in data:
            self.updateDirectory()


class ConnectionWindow:
    SIZE = 1024
    FORMAT = 'utf-8'
    xpad = 5
    
    def __init__(self, rootWindow):
        self.client = None
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
        self.ipEntry.focus()
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
        try:
            self.client.send("LOGOUT".encode(self.FORMAT))
        except:
            print("Warning: Problem closing the connection.")
        self.rootWindow.destroy()

window = tk.Tk()
window.title("CS371 Client")
window.withdraw()
cW = ConnectionWindow(window)
window.mainloop()
