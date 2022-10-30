from tkinter import *
from tkinter import ttk
import time
#Info on multithreading: https://www.tutorialspoint.com/python/python_multithreading.htm#:~:text=Multiple%20threads%20within%20a%20process,if%20they%20were%20separate%20processes.
from threading import Thread
from PIL import Image, ImageTk, ImageDraw, ImageFont

class wrappedCanvas(Canvas):
    def __init__(self, root,width,height):
        #Call logging system originally used in 112 graphics
        self.drawLogs = []
        self.canvas = super().__init__(root,width=width,height=height)
        self.grid(column=0, row=0, sticky=(N, W, E, S))
        self.create_line(0,0,100,100)

    #Call logging system originally used in 112 graphics
    def logMethod(self, method, *args, **kwargs):
        self.drawLogs.append((method, args, kwargs))

    def clearMethods(self):
        self.drawLogs = []

    #Adds to call list
    def create_image(self, *args, **kwargs):
        self.logMethod(super().create_image, args, kwargs)

    def create_line(self, *args, **kwargs):
        self.logMethod(super().create_line, args, kwargs)

    def create_rectangle(self, *args, **kwargs):
        self.logMethod(super().create_rectangle, args, kwargs)

    def create_text(self, *args, **kwargs):
        self.logMethod(super().create_text, args, kwargs)

class App:
    def __init__(self, startCall, timerCall, drawCall, mousePressCall, mouseMovedCall, keyboardPressCall, keyboardReleaseCall):
        #Initializes direct calls to functions
        self.startCall = startCall
        self.timerCall = timerCall
        self.drawCall = drawCall
        self.mousePressCall = mousePressCall
        self.mouseMovedCall = mouseMovedCall
        self.keyboardPressCall = keyboardPressCall
        self.keyboardReleaseCall = keyboardReleaseCall

    #Image loading taken from CMU 112 graphics
    def loadImage(self,path):
        return Image.open(path)

    #Adaptor for mouse presses
    def mousePressAdapter(self, event, type):
        event.button = type
        self.mousePressCall(self, event)

    #Adaptor for key presses
    def keyPressAdapter(self,event):
        self.keyboardPressCall(self,event)

    #Adaptor for key releases
    def keyReleaseAdapter(self,event):
        self.keyboardReleaseCall(self,event)

    #Sets the title of the window
    def setTitle(self, title):
        #Info on title: https://www.geeksforgeeks.org/python-gui-tkinter/
        self.root.title(title)

    def start(self):
        #Info on making Tkinter applications: https://www.geeksforgeeks.org/python-gui-tkinter/
        self.startCall(self)
        self.root = Tk()
        self.frame = ttk.Frame(self.root,padding=10)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.canvas = wrappedCanvas(self.root,400,400)
        #Info on setting window size: https://pythonexamples.org/python-tkinter-set-window-size/
        self.root.geometry("400x400")
        self.root.update()
        #Dimension getting derived from CMU 112 graphics
        geometry = self.root.winfo_geometry().split("x")
        self.width = (eval(geometry[0]))
        self.height = (eval(geometry[1].split("+")[0]))
        #Pointer position from Bryan Oakley and Chris Emerson: https://stackoverflow.com/questions/22925599/mouse-position-python-tkinter
        self.mouseX = self.root.winfo_pointerx() - self.root.winfo_rootx()
        self.mouseY = self.root.winfo_pointery() - self.root.winfo_rooty()
        #Mouse and key events: https://www.nurmatova.com/mouse-and-keyboard-events.html
        if self.keyboardPressCall != None:
            self.root.bind("<KeyPress>", lambda event: self.keyboardPressCall(self,event))
        if self.keyboardReleaseCall != None:
            self.root.bind("<KeyRelease>", lambda event: self.keyboardReleaseCall(self,event))
        if self.mousePressCall != None:
            self.canvas.bind("<Button-1>", lambda event: self.mousePressAdapter(event,0))
            self.canvas.bind("<Button-2>", lambda event: self.mousePressAdapter(event,1))
            self.canvas.bind("<Button-3>", lambda event: self.mousePressAdapter(event,1))
        #Info on multithreading: https://www.tutorialspoint.com/python/python_multithreading.htm#:~:text=Multiple%20threads%20within%20a%20process,if%20they%20were%20separate%20processes.
        updateThread = Thread(target=self.threadUpdate,args=[])
        updateThread.start()
        drawThread = Thread(target=self.threadDraw,args=[])
        drawThread.run()
        self.root.mainloop()

    def threadUpdate(self):
        while True:
            ox = self.mouseX
            oy = self.mouseY
            #Pointer position from Bryan Oakley and Chris Emerson: https://stackoverflow.com/questions/22925599/mouse-position-python-tkinter
            self.mouseX = self.root.winfo_pointerx() - self.root.winfo_rootx()
            self.mouseY = self.root.winfo_pointery() - self.root.winfo_rooty()
            if ox != self.mouseX or oy != self.mouseY:
                self.mouseMovedCall(self,self.mouseX,self.mouseY)
            #Dimension getting derived from CMU 112 graphics
            geometry = self.root.winfo_geometry().split("x")
            self.width = (eval(geometry[0]))
            self.height = (eval(geometry[1].split("+")[0]))
            self.timerCall(self)
            time.sleep(0.0)

    def threadDraw(self):
        #Tests the canvas
        self.canvas.create_line(self.width/2,self.height/2,200,20)
        self.canvas.clearMethods()
        self.drawCall(self,self.canvas)
        #From CMU 112 graphics
        self.canvas.delete(ALL)
        #Runs through every logged method
        for method in self.canvas.drawLogs:
            method[0](*method[1],**method[2])
        #update() caused waiting for mouse. Fix found using update_idletasks(): https://www.tutorialspoint.com/what-s-the-difference-between-update-and-update-idletasks-in-tkinter#:~:text=The%20update()%20and%20update_idletask,are%20not%20running%20or%20stable.
        self.canvas.update_idletasks()
        #Fix to graphical flickering expained by milanbalazs: https://stackoverflow.com/questions/41308900/tkinter-canvas-flickering
        self.canvas.after(0,self.threadDraw)


def runApp(startCall=None, timerCall=None, drawCall=None, mousePressCall=None, mouseMovedCall=None, keyboardPressCall=None, keyboardReleaseCall=None):
    app = App(startCall, timerCall, drawCall, mousePressCall, mouseMovedCall, keyboardPressCall, keyboardReleaseCall)
    app.start()
