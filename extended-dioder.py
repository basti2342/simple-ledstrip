#!/usr/bin/env python
# -*- coding: utf-8 -*-

import colorsys, time, random, signal
from dioder import Dioder, SerialLogic
from threading import Thread

class ExtendedDioder(Dioder, Thread):
	def __init__(self, *args, **kwargs):
		super(ExtendedDioder, self).__init__(*args, **kwargs)
		self.running = True
		self.mode = None
		self.modeBreak = False
		self.savedMode = signal.SIGRTMIN + 1

	def shouldBreak(self):
		returnVal = not self.running or self.modeBreak
		self.modeBreak = False
		return returnVal

	def setMode(self, signalNum):
		if self.mode: self.modeBreak = True
		signals = {
					34: "dark",
					35: "lightUp",
					36: "rainbow",
					37: "wipeRed",
					38: "wipeGreen",
					39: "wipeBlue",
					40: "colorWipeCenter",
					41: "colorWipeCenterReverse",
					42: "colorWipeCenterBounce",
					43: "strobo",
					44: "ambientColorFade",
					45: "orange",
					46: "white"
				}
		if signalNum == 50:
			signalNum = self.savedMode
			self.savedMode += 1
			if self.savedMode > (signal.SIGRTMIN + len(signals) - 1):
				self.savedMode = signal.SIGRTMIN

		self.mode = getattr(self, signals[signalNum])
		print "Running ", signals[signalNum]

	def run(self):
		while self.running:
			if self.mode:
				self.mode()
			else:
				self.dark()

	def dark(self):
		self.showColor(0, 0, 0)

	def white(self):
		self.showColor(255, 255, 255)

	def orange(self):
		self.showColor(173, 76, 0)

	def showColor(self, color0, color1, color2):
		while not self.shouldBreak():
			self.setStripColor(color0, color1, color2)
			self.show()
			time.sleep(0.5)

	def lightUp(self):
		for color in range(256):
			if self.shouldBreak(): return
			self.setStripColor(color, color, color)
			self.show()
		self.white()

	def rainbow(self, waitMs=20):
		for j in range(256):
			for i in range(self.limits[1]):
				if self.shouldBreak(): return
				color = self.wheel((i+j) & 255)
				self.setColor(i, *color)

			self.show()
			time.sleep(waitMs*0.001)

	def wheel(diod, wheelPos):
		if wheelPos < 85:
			return (wheelPos * 3, 255 - wheelPos * 3, 0)
		elif wheelPos < 170:
			wheelPos -= 85;
			return (255 - wheelPos * 3, 0, wheelPos * 3)
		else:
			wheelPos -= 170
			return (0, wheelPos * 3, 255 - wheelPos * 3)

	def wipeRed(self):
		self.colorWipe((255, 0, 0))

	def wipeGreen(self):
		self.colorWipe((0, 255, 0))

	def wipeBlue(self):
		self.colorWipe((0, 0, 255))

	def colorWipe(self, color, waitMs=50):
		for i in range(self.limits[1]):
			if self.shouldBreak(): return
			self.setColor(i, *color)
			self.show()
			time.sleep(waitMs*0.001)

	def colorWipeCenter(self, color=(255, 255, 255), waitMs=50):
		center = int(round(self.limits[1]/2))
		i = center
		j = center

		while i != 0 and j != self.limits[1]:
			if self.shouldBreak(): return
			self.setColor(i, *color)
			self.setColor(j, *color)
			self.show()
			time.sleep(waitMs*0.001)
			i -= 1
			j += 1

	def colorWipeCenterReverse(self, color=(0, 255, 0), waitMs=50):
		center = int(round(self.limits[1]/2))
		i = 0
		j = self.limits[1] - 1

		while i < center and j > center:
			if self.shouldBreak(): return
			self.setColor(i, *color)
			self.setColor(j, *color)
			self.show()
			time.sleep(waitMs*0.001)
			i += 1
			j -= 1

	def colorWipeCenterBounce(self, color=(0, 255, 0), waitMs=50):
		self.colorWipeCenter(color, waitMs)
		self.colorWipeCenterReverse((0, 0, 0), waitMs)

	def strobo(self, color=(255, 255, 255)):
		for c in [color] + [(0, 0, 0)]:
			if self.shouldBreak(): return
			self.setStripColor(*c)
			self.show()

	def ambientColorFade(self, color1=(254, 100, 0), color2=(255, 120, 1), waitMs=50):
		color = [random.randint(color1[x], color2[x]) for x in range(3)]
		self.setStripColor(color[0], color[1], color[2])
		self.show()

		while True:
			gauss = {}
			mean = random.choice(range(self.limits[1]+1))

			for i in range(5000):
				try:
					rand = int(round(random.gauss(mean, 0.2))) #2

					if rand >= self.limits[0] and rand <= self.limits[1]:
						gauss[rand] += 1
				except KeyError:
					gauss[rand] = 1

			for i, count in gauss.items():
				if self.shouldBreak(): return
				try:
					hsv = list(colorsys.rgb_to_hsv(color[0]/255.0, color[1]/255.0, color[2]/255.0))
				except ZeroDivisionError:
					pass

				hsvNew = hsv
				hsvNew[2] += (count*0.000008) * random.choice((1, -1))#signed
				if hsvNew[2] < 0: hsvNew = hsv
				if hsvNew[2] < -1: hsvNew[2] += 1
				newRgb = colorsys.hsv_to_rgb(*hsvNew)
				newRgb = [x*255 for x in newRgb]
				try:
					self.setColor(i, *newRgb)
					color = newRgb
				except ValueError:
					pass

				self.show()
				time.sleep(0.00001)

			time.sleep(waitMs*(0.0001*random.randint(0, 5)))


serialLogic = SerialLogic("/dev/ttyACM0", 57600)
diod0 = ExtendedDioder(serialLogic) #0 0,38
#diod1 = ExtendedDioder(serialLogic, (0, 49)) #1
diod0.start()
#diod1.start()

def wrapMode(signalNum, stackframe):
	diod0.setMode(signalNum)
	#diod1.setMode(signalNum)

for i in range(signal.SIGRTMIN, signal.SIGRTMAX+1):
	signal.signal(i, wrapMode)

while True:
	signal.pause()

