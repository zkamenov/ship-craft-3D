
#############
## IMPORTS ##
#############

import math
import string
from cfuncts import cRender
import os
from math import sin, cos, sqrt, floor, ceil, tanh
import random

#############
## HELPERS ##
#############

#Constrains a value
def constrain(min,n,max):
    if n > max:
        return max
    elif n < min:
        return min
    return n

##################
## 3D MECHANICS ##
##################

#X is left/right
#Y is up/down
#Z is forward/backward

#A point in a 3D world
class Point3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    def __add__(self, other):
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)
    def add(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z
    def set(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    def tupleSet(self, tuple):
        if tuple == None:
            self.x = None
            self.y = None
            self.z = None
            return
        self.x = tuple[0]
        self.y = tuple[1]
        self.z = tuple[2]
    def rotateRight(self, angle):
        #I found these rotation equations through mathematical thinking
        x = self.x*math.cos(angle) + self.z*math.sin(angle)
        z = self.z*math.cos(angle) - self.x*math.sin(angle)
        return Point3D(x, self.y ,z)
    def rotateUp(self, angle):
        y = self.y*math.cos(angle) + self.z*math.sin(angle)
        z = self.z*math.cos(angle) - self.y*math.sin(angle)
        return Point3D(self.x, y, z)
    def destructiveRotateRight(self, angle):
        ox = self.x
        self.x = self.x*math.cos(angle) + self.z*math.sin(angle)
        self.z = self.z*math.cos(angle) - ox*math.sin(angle)
    def destructiveRotateUp(self, angle):
        oy = self.y
        self.y = self.y*math.cos(angle) + self.z*math.sin(angle)
        self.z = self.z*math.cos(angle) - oy*math.sin(angle)
    def pointHitX(self, faceX):
        if self.x == 0:
            return None
        ratio = faceX/self.x
        return Point3D(faceX, self.y * ratio, self.z * ratio)
    def pointHitY(self, faceY):
        if (self.y == 0):
            return None
        ratio = faceY/self.y
        if ratio < 0:
            return None
        return Point3D(self.x * ratio, faceY, self.z * ratio)
    def pointHitZ(self, faceZ):
        if self.z == 0:
            return None
        ratio = faceZ/self.z
        return Point3D(self.x * ratio, self.y * ratio, faceZ)
    def distance(self):
        #Pythagorean theorem
        return (self.x**2+self.y**2+self.z**2)**0.5
    def yDist(self):
        return abs(self.y)

#The camera of the player
class Camera:
    def __init__(self, x, y, z, angleX, angleY, resolutionX, resolutionY, zoom, skybox, maxDist):
        self.pos = Point3D(x,y,z)
        self.angleX = angleX
        self.angleY = angleY
        self.resolutionX = resolutionX
        self.resolutionY = resolutionY
        self.zoom = zoom
        self.skybox = skybox
        #Information from the notes about images
        self.out = Image.new(mode="RGB", size=(self.resolutionX, self.resolutionY))
        self.maxDist = maxDist

    #Sets the position
    def setPosition(self, x, y, z):
        self.pos.set(x, y, z)

    #Calls C rendering function
    def renderC(self, app, img, world):
        #Information from the notes about images
        self.out = Image.new(mode="RGB", size=(self.resolutionX, self.resolutionY))
        cRender(self.pos.x, self.pos.y, self.pos.z, self.angleX, self.angleY, self.resolutionX, self.resolutionY, self.zoom,
        world, app.mapWidth, app.mapLength, app.mapHeight, img, self.out.load(), app.breakBlock, self.skybox, self.maxDist,
        True if app.dimension == "Venus" else False)
        return self.out




#####################
## WORLD OPERATORS ##
#####################

#Relplaces a part of a string
def replace(string, start, end, replacement):
    return string[:start] + replacement + string[end:]

#Returns the index of the map string
def mapIndex(app, x, y, z):
    return math.floor(y) + app.mapHeight * (math.floor(x) + app.mapWidth * math.floor(z))

#Fills an array of voxels stacked on top of each other
def fillDownToUp(app, x, z, y1, y2, blockID):
    i1 = mapIndex(app, x, constrain(0,y1,app.mapHeight), z)
    i2 = mapIndex(app, x, constrain(0,y2,app.mapHeight), z)
    app.map = replace(app.map, i1, i2, chr(blockID) * (i2-i1))

#Sets a block
def setBlock(app, x, y, z, blockID):
    i = mapIndex(app, x, y, z)

    selector = f"{app.dimension},{floor(x+app.xShift)},{floor(z+app.zShift)}"

    if selector in app.blockDict:
        app.blockDict[selector][floor(y+app.yShift)] = blockID
    else:
        app.blockDict[selector] = {floor(y+app.yShift):blockID}
    app.map = replace(app.map, i, i+1, chr(blockID))

#Gets a block's ID
def getBlock(app, x, y, z):
    i = mapIndex(app, x, y, z)%(app.mapWidth*app.mapHeight*app.mapLength)
    return ord(app.map[i])

#Lays the ground
def layGround(app, heightCall, shift):
    surface = 1
    mountainStart = 45
    mountainSurface = 4
    subSurface = 2
    if app.dimension == "Moon":
        surface = 5
        mountainSurface = 5
        subSurface = 6
    if app.dimension == "Venus":
        surface = 7
        mountainSurface = 7
        subSurface = 7
    shift *= -1
    for i in range(1,app.mapWidth-1):
        for j in range(1,app.mapLength-1):
            height = heightCall(i,j)
            fillDownToUp(app, i, j, height+shift-1, height+shift, surface if height < mountainStart else mountainSurface)
            fillDownToUp(app, i, j, 1, height+shift-1, subSurface)
            #Credit to course notes for idea of using dictionaries
            selector = f"{app.dimension},{floor(i+app.xShift)},{floor(j+app.zShift)}"
            if selector in app.blockDict:
                for y in app.blockDict[selector]:
                    fillDownToUp(app, i, j, y+shift, y+shift+1, app.blockDict[selector][y])
            fillDownToUp(app, i, j, 0, 1, 3)
            fillDownToUp(app, i, j, app.mapHeight-1, app.mapHeight, 3)

#################
## CONTROLLERS ##
#################

#Updates camera angle
def mouseMoved(app, x, y):
    app.camera.angleX = (x-app.width/2)/50
    app.camera.angleY = constrain(-1.5708,-(y-app.height/2)/50+0.001,1.5708)

#Key controls for movement
def keyPressed(app, event):
    #event.char derived from question asked: https://stackoverflow.com/questions/36855725/cannot-print-out-event-char-using-tkinter
    if event.char == "":#If shift key pressed, do nothing
        return
    #print(ord(event.char))
    if app.nameScreen:
        if event.char == chr(13):#Enter
            app.target = app.nameScreenInput
            app.nameScreen = False
            appStarted(app,nameView=False,targetChange=False)
        elif event.char == chr(127):#Backspace
            if app.nameScreenInput != "":
                app.nameScreenInput = app.nameScreenInput[:-1]
        elif ord(event.char) < 256:
            app.nameScreenInput += event.char
        return
    if app.loadScreenView:
        if event.char == "s":
            if app.loadScreenScroll < len(app.saves)*app.slotHeight:
                app.loadScreenScroll += app.loadScreenScrollSpeed
        elif event.char == "w":
            if app.loadScreenScroll > 0:
                app.loadScreenScroll -= app.loadScreenScrollSpeed
        return
    if event.char.lower() == "w":
        app.forward = True
    elif event.char.lower() == "a":
        app.leftward = True
    elif event.char.lower() == "s":
        app.backward = True
    elif event.char.lower() == "d":
        app.rightward = True
    elif event.char.lower() == chr(32): #Space bar
        app.jump = True
    elif event.char.lower() == "e":
        app.inventoryView = not app.inventoryView
    elif event.char.isdigit():
        app.hotbarSelect = constrain(1,int(event.char),app.inventoryWidth)-1
    #print(event.char)

def keyReleased(app, event):
    if app.loadScreenView or app.nameScreen:
        return
    if event.char.lower() == "w":
        app.forward = False
    elif event.char.lower() == "a":
        app.leftward = False
    elif event.char.lower() == "s":
        app.backward = False
    elif event.char.lower() == "d":
        app.rightward = False
    elif event.char.lower() == chr(32):
        app.jump = False
    elif event.char.lower() == "r":
        reload(app, xShift=floor(app.xShift+app.x-50), yShift=floor(app.yShift+app.y-50), zShift=floor(app.zShift+app.z-50))
    elif event.char.lower() == "k":
        reload(app, xShift=floor(app.xShift+app.x-50), yShift=floor(app.yShift+app.y-50), zShift=floor(app.zShift+app.z-50))
        save(app,target=app.target)
    elif event.char.lower() == "l":
        app.saves = ["Create New"] + os.listdir("saves/")
        app.loadScreenView = not app.loadScreenView#load(app)
    elif event.char.lower() == "o":
        if app.camera.resolutionX > 50:
            app.camera.resolutionX //=2
            app.camera.resolutionY //=2
    elif event.char.lower() == "p":
        if app.camera.resolutionX < 400:
            app.camera.resolutionX *=2
            app.camera.resolutionY *=2
    elif event.char.lower() == "m":
        if app.camera.maxDist < 100:
            app.camera.maxDist += 1
    elif event.char.lower() == "n":
        if app.camera.maxDist > 4:
            app.camera.maxDist -= 1
    elif event.char.lower() == "i":
        if app.dimension == "Earth":
            app.dimension = "Moon"
        elif app.dimension == "Moon":
            app.dimension = "Venus"
        else:
            app.dimension = "Earth"
        reload(app, xShift=floor(app.xShift+app.x-50), yShift=floor(app.yShift+app.y-50), zShift=floor(app.zShift+app.z-50))

def mousePressed(app, event):
    if app.loadScreenView == True:
        targetSave = (app.mouseY + app.loadScreenScroll)//app.slotHeight
        if targetSave == 0:
            app.loadScreenView = False
            app.nameScreen = True
        elif targetSave < len(app.saves):
            load(app, target=app.saves[targetSave])
            app.target = app.saves[targetSave]
            app.loadScreenView = False
        return
    if app.inventoryView == True:
        col = floor((app.mouseX - app.width/2)/32 + app.inventoryWidth/2 + 0.5)
        row = floor((app.mouseY - app.height/2)/32 + app.inventoryHeight/2 + 0.5)
        if col >= 0 and col < app.inventoryWidth and row >= 0 and row < app.inventoryHeight:
            if app.inventorySelect == None:
                app.inventorySelect = (col,row)
            else:
                app.inventory[app.inventorySelect[1]][app.inventorySelect[0]],app.inventory[row][col] = (
                app.inventory[row][col],app.inventory[app.inventorySelect[1]][app.inventorySelect[0]])
                app.inventorySelect = None
        return

    if getBlock(app, app.breakBlock[0], app.breakBlock[1], app.breakBlock[2]) == 0:
        return
    if (app.inventory[0][app.hotbarSelect][0] == chr(0)):
        if getBlock(app, app.breakBlock[0], app.breakBlock[1], app.breakBlock[2]) != 3:
            obtainItem(app, getBlock(app, app.breakBlock[0], app.breakBlock[1], app.breakBlock[2]))
            setBlock(app, app.breakBlock[0], app.breakBlock[1], app.breakBlock[2], 0)
    elif (floor(app.placeBlock[0]), floor(app.placeBlock[1]), floor(app.placeBlock[2])) != (floor(app.x), floor(app.y), floor(app.z)):
        setBlock(app, app.placeBlock[0], app.placeBlock[1], app.placeBlock[2], ord(app.inventory[0][app.hotbarSelect][0]))
        popItem(app,app.hotbarSelect,0)


#########################
## CENTRAL INITIALIZER ##
#########################

def appStarted(app, nameView=True, xShift=None, targetChange = True, yShift=0, zShift=None):

    #Dictionary that stores modified blocks for generation
    app.blockDict = {}

    #Player properties
    app.dimension = "Earth"
    app.xvel = 0
    app.yvel = 0
    app.zvel = 0
    app.x = 50.5
    app.y = 50.5
    app.z = 50.5

    #Player properties
    app.breakBlock = (2,2,2)
    app.walkSpeed = 0.2
    app.jumpPower = 0.5
    app.inventoryWidth = 6
    app.inventoryHeight = 6
    app.hotbarSelect = 0
    app.inventoryView = False
    app.loadScreenView = nameView
    app.nameScreen = False
    app.nameScreenInput = ""
    app.loadScreenScrollSpeed = 20
    app.slotHeight = 50
    app.loadScreenScroll = 0
    app.saves = ["Create New"] + os.listdir("saves/")[1:]
    if targetChange: app.target = f"w{len(app.saves)}"
    app.inventorySelect = None
    app.inventory = []
    for i in range(app.inventoryHeight):
        app.inventory.append([chr(0)+chr(255)]*app.inventoryWidth)
    app.inventory[0][0] = chr(1)+chr(4)

    #Player controls
    app.forward = False
    app.backward = False
    app.leftward = False
    app.rightward = False
    app.jump = False

    #Map dimensions
    #app.mapWidth = 100
    #app.mapLength = 100
    #app.mapHeight = 100

    #Map is represented as a single string, each block consuming one byte as...
    #...a character, representable as an int through ord() function
    #app.map = chr(0) * app.mapHeight * app.mapWidth * app.mapLength

    #Derived from notes on images
    skybox = app.loadImage(f"skyboxes/{app.dimension}.png").convert('RGB')

    #Camera object
    app.camera = Camera(app.x,app.y,app.z,0.0,0.1,100,100,100,skybox,20)

    #Textures
    app.textures = [None]*256
    app.itemImages = [None]*256

    #Builds array of image pointers to texture
    for i in range(0,256):
        try:
            #Image pixel loading: https://www.geeksforgeeks.org/python-pil-getpixel-method/
            app.itemImages[i] = app.loadImage(f"textures/{i}.png").convert('RGB')
            app.textures[i] = app.itemImages[i].load()
        except Exception as e:
            app.itemImages[i] = Image.new(mode="RGB", size=(16, 16))
            app.textures[i] = app.itemImages[i].load()

    app.screen = None
    reload(app, xShift=xShift, yShift=yShift, zShift=zShift)



###########################
## MAIN ACTION FUNCTIONS ##
###########################

def reload(app, xShift=None, yShift=0, zShift=None):

    if xShift == None or zShift == None:
        xShift = random.randrange(0,1000)*1000
        zShift = random.randrange(0,1000)*1000
    app.xShift = xShift
    app.yShift = yShift
    app.zShift = zShift

    #Player properties
    app.xvel = 0
    app.yvel = 0
    app.zvel = 0
    app.x = 50.5
    app.y = 50.5
    app.z = 50.5

    #Derived from notes on images
    skybox = app.loadImage(f"skyboxes/{app.dimension}.png").convert('RGB')

    #Camera object
    app.camera = Camera(app.x,app.y,app.z,0.0,0.1,100,100,100,skybox,20)

    #Map dimensions
    app.mapWidth = 100
    app.mapLength = 100
    app.mapHeight = 100

    #Map is represented as a single string, each block consuming one byte as...
    #...a character, representable as an int through ord() function
    app.map = chr(0) * app.mapHeight * app.mapWidth * app.mapLength

    #Planar generation algorithms
    #Produced by playing with planar functions on GeoGebra: https://www.geogebra.org/calculator

    def genHeightEarth(x,y):
        x += xShift
        y += zShift
        z = 40

        rk=sin(sin(cos(2*x)+sin(3*y))*sin(7*x))**2

        x /= 20
        y /= 20
        mt = 1+tanh(10*(sin(sin(2*x+3*y)+2*x)*cos(1*x)+cos(y+sin(x+y))*cos(x)))

        z += 3*mt*(rk+2)
        return z

    def genHeightMoon(x,y):
        x += xShift
        y += zShift
        z = 40

        mt = 1 + tanh(-10-10*cos(sin(0.03*x-0.05*y)+cos(0.02*x+0.01*y)+sin(0.09*x+0.08*y)+cos(0.04*x-0.02*y)))
        z += 15*mt
        return z

    def genHeightVenus(x,y):
        x += xShift
        y += zShift
        z = 40

        mt = 1.3**(sin(0.02*x-0.03*y)+cos(0.05*x+0.06*y)+sin(0.03*x+0.04*y)+cos(0.07*x-0.05*y))
        z += 10*mt
        return z
    #Generates the world
    call = genHeightEarth
    if app.dimension == "Moon":
        call = genHeightMoon
    elif app.dimension == "Venus":
        call = genHeightVenus
    layGround(app, call, yShift)

    #World Edges
    for i in range(0,app.mapWidth):
        fillDownToUp(app,i,0,0,app.mapHeight-1,3)
        fillDownToUp(app,i,app.mapLength-1,0,app.mapHeight-1,3)

    for i in range(0,app.mapLength):
        fillDownToUp(app,0,i,0,app.mapHeight-1,3)
        fillDownToUp(app,app.mapWidth-1,i,0,app.mapHeight-1,3)

#Removes one itme from the inventory
def popItem(app, col, row):
    if ord(app.inventory[row][col][1]) > 0: #If item count is more than 1, reduce item count by 1
        app.inventory[row][col] = chr(ord(app.inventory[row][col][0]))+chr(ord(app.inventory[row][col][1])-1)
    else: # If item count is 1, change item to empty slot
        app.inventory[row][col] = chr(0)+chr(255)

#Adds item to the inventory
def obtainItem(app, itemID):
    #Searches for existing non full stack of items in inventory
    for i in range(len(app.inventory)):
        for j in range(len(app.inventory[i])):
            if ord(app.inventory[i][j][0]) == itemID and ord(app.inventory[i][j][1]) != 255:
                app.inventory[i][j] = chr(ord(app.inventory[i][j][0]))+chr(ord(app.inventory[i][j][1])+1)
                return True
    #If no existing item stack is found, create new stack at blank slot
    for i in range(len(app.inventory)):
        for j in range(len(app.inventory[i])):
            if app.inventory[i][j][0] == chr(0):
                app.inventory[i][j] = chr(itemID)+chr(0)
                return True
    return False

#Updates the screen in the model
def updateScreen(app):
    #t1 = time.time()
    app.screen = ImageTk.PhotoImage(app.camera.renderC(app, app.textures,app.map).resize((int(app.width),int(app.width)),resample=Image.NEAREST))
    #print(f"{time.time() - t1} seconds")

#Updates the player position
def updatePosition(app):
    app.camera.pos.x = app.x
    app.camera.pos.y = app.y - 1 + 1.2
    app.camera.pos.z = app.z

    app.yvel -= 0.03 if app.dimension == "Moon" else 0.1

    airResistance = 1.0 if app.dimension == "Moon" else 0.95

    resistance = airResistance if app.map[mapIndex(app,app.x,app.y+app.yvel,app.z)] == chr(0) else 0.2

    app.xvel *= resistance
    app.yvel *= resistance
    app.zvel *= resistance

    resistance = 1 - resistance

    if app.jump and app.map[mapIndex(app,app.x,app.y-0.02,app.z)] != chr(0) and not app.inventoryView:
        app.yvel = app.jumpPower

    if app.forward and not app.inventoryView:
        app.xvel += app.walkSpeed*math.sin(app.camera.angleX)*resistance
        app.zvel += app.walkSpeed*math.cos(app.camera.angleX)*resistance

    if app.backward and not app.inventoryView:
        app.xvel += -resistance*app.walkSpeed*math.sin(app.camera.angleX)*resistance
        app.zvel += -resistance*app.walkSpeed*math.cos(app.camera.angleX)*resistance

    if app.leftward and not app.inventoryView:
        app.xvel += -resistance*app.walkSpeed*math.cos(app.camera.angleX)*resistance
        app.zvel += resistance*app.walkSpeed*math.sin(app.camera.angleX)*resistance

    if app.rightward and not app.inventoryView:
        app.xvel += resistance*app.walkSpeed*math.cos(app.camera.angleX)*resistance
        app.zvel += -resistance*app.walkSpeed*math.sin(app.camera.angleX)*resistance


    if app.map[mapIndex(app,app.x+app.xvel,app.y+0.01,app.z)] == chr(0):
        app.x += app.xvel
    else:
        pass#app.xvel = 0

    if app.map[mapIndex(app,app.x,app.y+0.01,app.z+app.zvel)] == chr(0):
        app.z += app.zvel
    else:
        pass#app.zvel = 0

    if app.map[mapIndex(app,app.x,app.y+app.yvel/(1-resistance),app.z)] == chr(0):
        app.y += app.yvel
    else:
        app.y = math.ceil(app.y+app.yvel/(1-resistance))-0.01
        app.yvel = 0

#Detects selected block
def selectBlock(app):
    pt = Point3D(math.sin(app.camera.angleX)*math.cos(app.camera.angleY),
    math.sin(app.camera.angleY),
    math.cos(app.camera.angleX)*math.cos(app.camera.angleY))
    hitX = Point3D(99,99,99)
    hitY = Point3D(99,99,99)
    hitZ = Point3D(99,99,99)
    faceX = -(app.camera.pos.x%1)
    faceY = -(app.camera.pos.y%1)
    faceZ = -(app.camera.pos.z%1)
    indxX = 0
    indxY = 0
    indxZ = 0
    indxXp = 0
    indxYp = 0
    indxZp = 0
    xDist = 99
    yDist = 99
    zDist = 99

    maxInd = app.mapWidth*app.mapHeight*app.mapLength

    if pt.x < 0:
        for i in range(5):
            hitX = pt.pointHitX(faceX)
            xDist = hitX.yDist()
            faceX -= 1
            hitX.x += app.camera.pos.x-1
            hitX.y += app.camera.pos.y+1
            hitX.z += app.camera.pos.z
            indxX = mapIndex(app,hitX.x,hitX.y,hitX.z)%maxInd
            if app.map[indxX] != chr(0):
                break
        indxXp = (hitX.x+1,hitX.y,hitX.z)
    elif pt.x > 0:
        for i in range(5):
            faceX += 1
            hitX = pt.pointHitX(faceX)
            xDist = hitX.yDist()
            hitX.x += app.camera.pos.x
            hitX.y += app.camera.pos.y+1
            hitX.z += app.camera.pos.z
            indxX = mapIndex(app,hitX.x,hitX.y,hitX.z)%maxInd
            if app.map[indxX] != chr(0):
                break
        indxXp = (hitX.x-1,hitX.y,hitX.z)

    if pt.y < 0:
        for i in range(5):
            hitY = pt.pointHitY(faceY)
            yDist = hitY.yDist()
            faceY -= 1
            hitY.x += app.camera.pos.x
            hitY.y += app.camera.pos.y
            hitY.z += app.camera.pos.z
            indxY = mapIndex(app,hitY.x,hitY.y,hitY.z)%maxInd
            if app.map[indxY] != chr(0):
                break
        indxYp = (hitY.x,hitY.y+1,hitY.z)
    elif pt.y > 0:
        for i in range(5):
            faceY += 1
            hitY = pt.pointHitY(faceY)
            yDist = hitY.yDist()
            hitY.x += app.camera.pos.x
            hitY.y += app.camera.pos.y+1
            hitY.z += app.camera.pos.z
            indxY = mapIndex(app,hitY.x,hitY.y,hitY.z)%maxInd
            if app.map[indxY] != chr(0):
                break
        indxYp = (hitY.x,hitY.y-1,hitY.z)

    if pt.z < 0:
        for i in range(5):
            hitZ = pt.pointHitZ(faceZ)
            zDist = hitZ.yDist()
            faceZ -= 1
            hitZ.x += app.camera.pos.x
            hitZ.y += app.camera.pos.y+1
            hitZ.z += app.camera.pos.z - 1
            indxZ = mapIndex(app,hitZ.x,hitZ.y,hitZ.z)%maxInd
            if app.map[indxZ] != chr(0):
                break
        indxZp = (hitZ.x,hitZ.y,hitZ.z+1)
    elif pt.z > 0:
        for i in range(5):
            faceZ += 1
            hitZ = pt.pointHitZ(faceZ)
            zDist = hitZ.yDist()
            hitZ.x += app.camera.pos.x
            hitZ.y += app.camera.pos.y+1
            hitZ.z += app.camera.pos.z
            indxZ = mapIndex(app,hitZ.x,hitZ.y,hitZ.z)%maxInd
            if app.map[indxZ] != chr(0):
                break
        indxZp = (hitZ.x,hitZ.y,hitZ.z-1)
    if xDist < yDist and xDist < zDist:
        app.breakBlock = (hitX.x,hitX.y,hitX.z)
        app.placeBlock = indxXp
    elif yDist < zDist:
        app.breakBlock = (hitY.x,hitY.y,hitY.z)
        app.placeBlock = indxYp
    else:
        app.breakBlock = (hitZ.x,hitZ.y,hitZ.z)
        app.placeBlock = indxZp

def save(app, target="w0"):
    #Credit to geeksforgeeks on how to make directory: https://www.geeksforgeeks.org/create-a-directory-in-python/
    try:
        os.mkdir(f"saves/{target}/")
    except Exception as e:
        pass
    #Credit to w3schools on how to write files: https://www.w3schools.com/python/python_file_write.asp
    posfile = open(f"saves/{target}/pos.bin", "w")
    posfile.write(f"{app.xShift},{app.yShift},{app.zShift},{app.dimension}")
    posfile.close()
    dictFile = open(f"saves/{target}/modblocks.bin", "w")
    chars = ""
    for selector in app.blockDict:
        mchars = ""
        for y in app.blockDict[selector]:
            mchars += f"-{y}={app.blockDict[selector][y]}"
        chars += f";{selector}:{mchars[1:]}"
    dictFile.write(chars[1:])
    dictFile.close()
    inventoryString = ""
    for row in app.inventory:
        for item in row:
            inventoryString += item
    inventoryFile = open(f"saves/{target}/inventory.bin", "w")
    inventoryFile.write(inventoryString)
    inventoryFile.close()

def load(app, target="w0"):
    #Credit to w3schools: https://www.w3schools.com/python/python_file_open.asp
    posfile = open(f"saves/{target}/pos.bin", "r")
    shifts = posfile.read().split(",")
    xShift, yShift, zShift = int(shifts[0]), int(shifts[1]), int(shifts[2])
    dimension = "Earth"
    if len(shifts) > 3:
        dimension = shifts[3]
    posfile.close()
    blockDict = dict()
    dictFile = open(f"saves/{target}/modblocks.bin", "r")
    dictString = dictFile.read()
    dictFile.close()
    for sector in dictString.split(";"):
        selector, ydict = tuple(sector.split(":"))
        if len(selector.split(","))<3:
            selector = f"{dimension},{selector}"
        blockDict[selector] = dict()
        for block in ydict.split("-"):
            y, id = tuple(block.split("="))
            blockDict[selector][int(y)] = int(id)
    app.blockDict = blockDict

    inventoryFile = open(f"saves/{target}/inventory.bin", "r")
    inventoryString = inventoryFile.read()
    inventoryFile.close()
    inventory = []
    for row in range(app.inventoryHeight):
        inventory.append([])
        for col in range(app.inventoryWidth):
            i = (col+app.inventoryWidth*row)*2
            inventory[row].append(inventoryString[i:i+2])
    app.inventory = inventory
    app.dimension = dimension
    reload(app, xShift=xShift, yShift=yShift, zShift=zShift)

def timerFired(app):
    updatePosition(app)
    selectBlock(app)

#Draws the screen image and crosshair
def redrawAll(app, canvas):
    if app.nameScreen:
        canvas.create_rectangle(0,0,app.width,app.height,fill="#000000")
        font = "Sans 20"
        canvas.create_text(app.width/2,app.height/2,text="Type your world name below\n"+app.nameScreenInput,font=font,anchor="center",fill="#FFFFFF")
        return

    if app.loadScreenView:
        i = -app.loadScreenScroll
        for save in app.saves:
            color = "#00FF00" if save == "Create New" else "#0000FF"
            canvas.create_rectangle(0,i,app.width,i+app.slotHeight,fill=color,outline="#FFFFFF")
            canvas.create_text(0,i,text=save,anchor="nw",fill="#FFFFFF")
            i+= app.slotHeight
        return
    if app.inventoryView:
        for i in range(app.inventoryWidth):
            for j in range(app.inventoryHeight):
                id = ord(app.inventory[j][i][0])
                amount = ord(app.inventory[j][i][1])+1
                cx = 32*(i-app.inventoryWidth/2)+app.width/2
                cy = 32*(j-app.inventoryHeight/2)+app.height/2
                font = "Sans 8"
                color = "#000000"
                if app.inventorySelect and i == app.inventorySelect[0] and j == app.inventorySelect[1]:
                    color = "#FF0000"
                canvas.create_rectangle(cx-10,cy-10,cx+10,cy+10,fill=color,width=0)
                canvas.create_image(cx,cy,image=ImageTk.PhotoImage(app.itemImages[id]))
                if id != 0:
                    canvas.create_text(cx,cy,anchor="center",text=str(amount), font=font)
        return

    #Image drawing derived from notes
    updateScreen(app)
    canvas.create_image(app.width/2,app.height/2,image=app.screen)
    canvas.create_line(app.width/2-10,app.height/2,app.width/2+10,app.height/2)
    canvas.create_line(app.width/2,app.height/2-10,app.width/2,app.height/2+10)

    for i in range(app.inventoryWidth):
        id = ord(app.inventory[0][i][0])
        amount = ord(app.inventory[0][i][1])+1
        cx = 32*(i-app.inventoryWidth/2)+app.width/2
        cy = 16
        font = "Sans 8"
        canvas.create_rectangle(cx-10,cy-10,cx+10,cy+10,fill="#FF0000" if i == app.hotbarSelect else "#000000")
        canvas.create_image(cx,cy,image=ImageTk.PhotoImage(app.itemImages[id]))
        if id != 0:
            canvas.create_text(cx,cy,anchor="center",text=str(amount), font=font)

runApp(startCall=appStarted,drawCall=redrawAll,timerCall=timerFired, mouseMovedCall=mouseMoved, mousePressCall=mousePressed, keyboardPressCall=keyPressed, keyboardReleaseCall=keyReleased)#width=400, height=400)
