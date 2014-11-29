#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial, struct, time
from os import system

"""
We need some serial logic to prevent concurrent writes to serial device.
"""
class SerialLogic(object):
	def __init__(self, device, baudrate):
		# force setting serial speed before using device
		system("stty -F %s %d" % (device, baudrate))
		time.sleep(1)

		self.serialCon = serial.Serial(device, baudrate)
		self.inUse = False

	def __del__(self):
		self.serialCon.close()

	def write(self, data):
		# wait until serial device is free
		#while self.inUse: time.sleep(0.000000001)
		#self.inUse = True
		self.serialCon.write(data)
		#self.inUse = False

	def close(self):
		self.serialCon.close()

"""
Control (part of) a single LED strip.
"""
class Dioder(object):
	def __init__(self, serialLogic, limits=(0, 88)):
		super(Dioder, self).__init__()
		try:
			self.dioder = serialLogic
			self.limits = limits
			# this actually takes some time
			time.sleep(1)
		except (serial.serialutil.SerialException, OSError):
			print "Please connect Dioder to %s." % device
			print "Running in dry mode.."
			self.dioder = Dry()

	def __del__(self):
		self.dioder.close()

	def checksum(self, body):
		result = ord(body[0])
		for i in range(0, len(body)):
			if i > 0:
				result = result ^ ord(body[i])
		return struct.pack("B", result)

	def setColor(self, i, color1, color2, color3):
		#print "writing %s to LED #%s" % ((color1, color2, color3), i)
		# write header
		self.dioder.write("\xBA\xBE")

		body = chr(i)

		for v in [color1, color2, color3]:
				body += chr(int(v))
		self.dioder.write(body)

		# write checksum
		self.dioder.write(self.checksum(body))

	def setColorPerc(self, i, color1, color2, color3):
		self.setColor(i, color1*255, color2*255, color3*255)

	def setStripColorPerc(self, color1, color2, color3):
		self.setStripColor(color1*255, color2*255, color3*255)

	def setStripColor(self, color1, color2, color3):
		for i in range(self.limits[0], self.limits[1]+1):
			self.setColor(i, color1, color2, color3)

	def show(self):
		# strip shows color when index out of bounds
		# FIXME: we need an index that's out of bounds, but we do not know one,
		# because we might be handling only part of the strip :S
		self.setColor(88, 0, 0, 0)

"""
Print everything that would have been sent to serial device for debugging
purposes.
"""
class Dry(object):
	def write(self, cmd):
		print cmd

	def close(self):
		pass

"""
For testing purposes only.
"""
def main():
	print "setting color"
	dioder = Dioder("/dev/ttyACM0", 57600, 0)
	dioder.setStripColor(255, 255, 255)

	dioder2 = Dioder("/dev/ttyACM0", 57600, 1)
	dioder2.setStripColor(255, 255, 255)


if __name__ == '__main__':
	main()
