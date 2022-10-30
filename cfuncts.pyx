#Cython syntax sources:
#https://www.cardinalpeak.com/blog/faster-python-with-cython-and-pypy-part-2

#############
## IMPORTS ##
#############

from tkinter import *
from PIL import Image, ImageTk, ImageDraw, ImageFont
from cmu_112_graphics import *
#Math library: https://stackoverflow.com/questions/10350765/overloading-python-math-functions-using-cython
from libc.math cimport sin, cos, floor, atan, sqrt

#############
## Classes ##
#############

#Info on classes in Cython: https://cython.readthedocs.io/en/latest/src/userguide/special_methods.html
cdef class Point3D:
	cdef double x, y, z

	def __cinit__(self, double x ,double y ,double z):
		self.x = x
		self.y = y
		self.z = z

	cdef void set(self, double x, double y, double z):
		self.x = x
		self.y = y
		self.z = z

	cdef void add(self, double x, double y, double z):
		self.x += x
		self.y += y
		self.z += z

	cdef void hitX(self, double faceX, Point3D out):
		cdef float ratio = faceX/self.x
		out.set(faceX,self.y*ratio,self.z*ratio)

	cdef void hitY(self, double faceY, Point3D out):
		cdef float ratio = faceY/self.y
		out.set(self.x*ratio,faceY,self.z*ratio)

	cdef void hitZ(self, double faceZ, Point3D out):
		cdef float ratio = faceZ/self.z
		out.set(self.x*ratio,self.y*ratio,faceZ)

	cdef void rotateX(self, float angleX):
		self.x, self.z = self.x*cos(angleX)+self.z*sin(angleX), self.z*cos(angleX)-self.x*sin(angleX)

	cdef void rotateY(self, float angleY):
		self.y, self.z = self.y*cos(angleY)+self.z*sin(angleY), self.z*cos(angleY)-self.y*sin(angleY)

	cdef double dist(self): #Not actual distance; used for comparing hit voxels
		return self.y*self.y #+self.x*self.x+self.z*self.z

###############
## C HELPERS ##
###############

cdef int constrain(int min, int n, int max):
	if n > max:
		return max
	elif n < min:
		return min
	return n

cdef long mapIndex(double x, double y, double z, long width, long height):
	return <long>y + height * (<long>x + width * <long>z)

def cRender(float x, float y, float z, float camX, float camY, int resX, int resY, int zoom, str world, long w, long l, long h, texture, screen, breakBlock, skybox, long renderDist, fog):
	render(x, y, z, camX, camY, resX, resY, zoom, world, w, l, h, texture, screen, breakBlock, skybox, renderDist, fog)

cdef render(float xp, float yp, float zp, float camXp, float camYp, int resXp, int resYp, float zoomp, str worldp, long wp, long lp, long hp, textures, screen, breakBlock, skybox, renderDistp, fogp):
	#Variables are pre-defined before loop to waste less time in declaration
	cdef Point3D pt = Point3D(1,1,1)
	cdef Point3D hitX = Point3D(99,99,99)
	cdef Point3D hitY = Point3D(99,99,99)
	cdef Point3D hitZ = Point3D(99,99,99)
	cdef Point3D hit = hitX
	cdef int r = 0
	cdef int g = 0
	cdef int b = 0
	cdef double x = xp
	cdef double y = yp
	cdef double z = zp
	cdef float camX = camXp
	cdef float camY = camYp
	cdef int resX = resXp
	cdef int resY = resYp
	cdef double zoom = zoomp
	cdef double skyX = 0.0
	cdef double skyY = 0.0
	cdef int fog = 1 if fogp == True else 0

	#Width and Length of the skybox
	cdef double skyWidth = skybox.width
	cdef double skyHeight = skybox.height
	sky = skybox.load()


	#Width length and height of map
	cdef long width = wp
	cdef long height = hp
	cdef long length = lp
	cdef long mapSize = width*height*length
	cdef long indxBreak = mapIndex(breakBlock[0], breakBlock[1], breakBlock[2], width, height)%mapSize

	#The world, which is a string, is pre-converted to bytes to avoid conversion during loop
	#Method suggested by: https://stackoverflow.com/questions/42334321/dealing-with-strings-in-cython
	cdef bytes world = worldp.encode()

	cdef char air = 0
	cdef int maxRenderDist = renderDistp

	cdef double faceX = 0.0
	cdef double faceY = 0.0
	cdef double faceZ = 0.0
	cdef double xdist = 999.9
	cdef double ydist = 999.9
	cdef double zdist = 999.9

	cdef int indxX = 0
	cdef int indxY = 0
	cdef int indxZ = 0

	for i in range(resX):
		for j in range(resY):
			xdist = 999.9
			ydist = 999.9
			zdist = 999.9

			#Generates ray for voxel detection
			pt.set(i/resX*2-1,1-j/resY*2,1)
			pt.rotateY(camY)
			pt.rotateX(camX)

			#Angles used for detecting skybox pixel
			skyX = (atan(pt.x/pt.z) + 1.5708)/6.2832
			skyY = (1.5708 - atan(pt.y/sqrt(pt.z*pt.z+pt.x*pt.x)))/3.1416
			if pt.z < 0:
				skyX += 0.5

			#Sets hit points to arbitrary far away point to avoid false detection
			hitX.set(99,99,99)
			hitY.set(99,99,99)
			hitZ.set(99,99,99)

			faceX = -(x%1)
			faceY = -(y%1)
			faceZ = -(z%1)

			#Detects hit voxels
			if pt.x < 0.0:
				for k in range(maxRenderDist):
					pt.hitX(faceX,hitX)
					xdist = hitX.dist()
					hitX.add(x, y, z)
					faceX -= 1
					indxX = mapIndex(hitX.x-1,hitX.y+1,hitX.z,width,height)%mapSize
					if world[indxX] != air:
						break
			elif pt.x > 0.0:
				for k in range(maxRenderDist):
					faceX += 1
					pt.hitX(faceX,hitX)
					xdist = hitX.dist()
					hitX.add(x, y, z)
					indxX = mapIndex(hitX.x,hitX.y+1,hitX.z,width,height)%mapSize
					if world[indxX] != air:
						break

			if pt.y < 0.0:
				for k in range(maxRenderDist):
					pt.hitY(faceY,hitY)
					ydist = hitY.dist()
					hitY.add(x, y, z)
					faceY -= 1
					indxY = mapIndex(hitY.x,hitY.y,hitY.z,width,height)%mapSize
					if world[indxY] != air:
						break
			elif pt.y > 0.0:
				for k in range(maxRenderDist):
					faceY += 1
					pt.hitY(faceY,hitY)
					ydist = hitY.dist()
					hitY.add(x, y, z)
					indxY = mapIndex(hitY.x,hitY.y+1,hitY.z,width,height)%mapSize
					if world[indxY] != air:
						break

			if pt.z < 0.0:
				for k in range(maxRenderDist):
					pt.hitZ(faceZ,hitZ)
					zdist = hitZ.dist()
					hitZ.add(x, y, z)
					faceZ -= 1
					indxZ = mapIndex(hitZ.x,hitZ.y+1,hitZ.z-1,width,height)%mapSize
					if world[indxZ] != air:
						break
			elif pt.z > 0.0:
				for k in range(maxRenderDist):
					faceZ += 1
					pt.hitZ(faceZ,hitZ)
					zdist = hitZ.dist()
					hitZ.add(x, y, z)
					indxZ = mapIndex(hitZ.x,hitZ.y+1,hitZ.z,width,height)%mapSize
					if world[indxZ] != air:
						break

			#Image pixel access: https://www.geeksforgeeks.org/python-pil-getpixel-method/
			#Comparison of detected voxels; closest wins
			if xdist < ydist and xdist < zdist:
				#hit = hitX
				if world[indxX] == 0:
					screen[i,j] = sky[floor(skyX%1*skyWidth),floor(skyY%1*skyHeight)]
					continue
				r, g, b = textures[world[indxX]][(hitX.z)%1*16,(hitX.y)%1*16]
				if (indxX == indxBreak):
					r = r//2+128
					g = g//2+128
					b = b//2+128
				screen[i,j] = (r,g,b)
			elif ydist < zdist:
				#hit = hitY
				if world[indxY] == 0:
					screen[i,j] = sky[floor(skyX%1*skyWidth),floor(skyY%1*skyHeight)]
					continue
				r, g, b = textures[world[indxY]][(hitY.x)%1*16,(hitY.z)%1*16]
				if (indxY == indxBreak):
					r = r//2+128
					g = g//2+128
					b = b//2+128
				screen[i,j] = (r,g,b)
			else:
				#hit = hitZ
				if world[indxZ] == 0:
					screen[i,j] = sky[floor(skyX%1*skyWidth),floor(skyY%1*skyHeight)]
					continue
				r, g, b = textures[world[indxZ]][(hitZ.x)%1*16,(hitZ.y)%1*16]
				if (indxZ == indxBreak):
					r = r//2+128
					g = g//2+128
					b = b//2+128
				screen[i,j] = (r,g,b)
