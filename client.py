from cProfile import label
import tkinter as tk

class ConnectionWindow():
    def __init__(self, rootWindow):
        self.window = rootWindow
        ipLabel = tk.Label(self.window, text="IP Address:").grid(column=0, row=0)
        portLabel = tk.Label(self.window, text="Port:").grid(column=0, row=1)
        ipEntry = tk.Entry(self.window).grid(column=1, row=0)
        portEntry = tk.Entry(self.window).grid(column=1, row=1)
        connectButton = tk.Button(self.window, text="Connect")
        connectButton.bind("<connect>", self.connect)
    def connect(self, event):
        pass



window = tk.Tk()



window.mainloop()

# def funFunction(bob):
#     print(bob)


# funFunction(1)

# class steve():
#     def __init__(self):
#         pass

# s = steve()

# print(s)