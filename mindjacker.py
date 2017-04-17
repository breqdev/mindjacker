#!/usr/bin/env python

import nxt.locator
from nxt.sensor import *
from nxt.motor import *
from time import time, sleep
from threading import Thread
from pickle import dump, load
from os import listdir, remove, system
from os.path import isfile, join

class HaventGottenToThatYetError(Exception):
	pass

class Brick:
	def __init__(self, name=None):
		self.draw = Display()
		self.calibrate = Calibrator()
		self.dev = nxt.locator.find_one_brick(name=name)
		self.a = mjMotor(self.dev, 0)
		self.b = mjMotor(self.dev, 1)
		self.c = mjMotor(self.dev, 2)
		#self.sync = mjSync(self.b.dev, self.c.dev)
	
	def move(self, motors, power, degrees=None, rotations=None, seconds=None, steer=None, brake=True):
		"""Move the robot. Use only one (or none at all) out of degrees, rotations, and seconds. 
		You can set steer when using multiple motors. -100 is hard left, 0 is center, 100 is hard right."""
		power /= 100.0
		power *= 127
		power = int(round(power))
		motorObjs = []
		for motor in motors:
			if motor.upper() == "A" or motor == 0:
				motorObj = self.a
			elif motor.upper() == "B" or motor == 1:
				motorObj = self.b
			else: # C
				motorObj = self.c
			motorObjs.append(motorObj)
		
		# Is power 0? If it is, we're stopping, and that's all.
		if power == 0:
			for motorObj in motorObjs:
				if brake:
					motorObj.brake()
				else:
					motorObj.coast()
			return
		
		# How many motors?
		if len(motors) == 2:
			# We're syncing. Is steer provided?
			if steer != None:
				if steer < 0:
					motorObjs.reverse() # Can't have negative steer
			else:
				# I guess we aren't steering.
				steer = 0
			motors = SynchronizedMotors(motorObjs[0].dev, motorObjs[1].dev, abs(steer))
			# Now, how much do we turn?
			if degrees != None:
				#print("Turning motor at power "+str(power)+" and degrees "+str(degrees))
				motors.turn(power, degrees, brake)
			elif rotations != None:
				motors.turn(power, rotations*360, brake)
			elif seconds != None:
				ts = time()
				motors.run(power)
				while time() < ts + seconds:
					pass
				if brake:
					motors.brake()
				else:
					motors.idle()
			else: # unlimited
				motors.run(power)
		
		elif len(motors) == 1: # Just steal code from the motor block
			self.motor(motors[0], power, degrees, rotations, seconds, brake)
		elif len(motors) == 3:
#	def motor(self, port, power, degrees=None, rotations=None, seconds=None, brake=True):'
			self.thread(self.motor, "A", power, degrees, rotations, seconds, brake)
			self.thread(self.motor, "B", power, degrees, rotations, seconds, brake)
			self.motor("C", power, degrees, rotations, seconds, brake)
		
	def record(self, name, seconds=None):
		"""Record movements.
		Physically move the robot with your hands to record."""
		raise HaventGottenToThatYetError, "I ain't done writing this code yet."
	
	def play(self, name):
		"""Play pre-recorded movements.
		First, record with the record() function."""
		raise HaventGottenToThatYetError, "I ain't done writing this code yet."
	
	def playSound(self, name):
		"""Play a sound file."""
		name = "/home/pi/mindjackerSounds/"+name+".mp3"
		system("mpg123 "+name)
	
	def playNote(self, note, time, nxt=True, wait=True):
		"""Play a note.
		If wait is false, don't wait for completion."""
		# Separate the note from the octave
		if len(note) == 1:
			noteStr = note.lower()
			octave = 5
		elif len(note) == 3:
			noteStr = note[0:2].lower()
			octave = int(note[2])
		elif len(note) == 2:
			if note[1] == "#":
				noteStr = note.lower()
				octave = 5
			else:
				noteStr = note[0].lower()
				octave = int(note[1])
		# I got this algorithm from www.musique.com/schem/freq.html
		if noteStr == "a":
			noteNum = 0
		elif noteStr == "a#":
			noteNum = 1
		elif noteStr == "b":
			noteNum = 2
		elif noteStr == "c":
			noteNum = 3
		elif noteStr == "c#":
			noteNum = 4
		elif noteStr == "d":
			noteNum = 5
		elif noteStr == "d#":
			noteNum = 6
		elif noteStr == "e":
			noteNum = 7
		elif noteStr == "f":
			noteNum = 8
		elif noteStr == "f#":
			noteNum = 9
		elif noteStr == "g":
			noteNum = 10
		elif noteStr == "g#":
			noteNum = 11
		octave -= 1
		a = 2**octave
		b = 1.059463**noteNum
		z = round(275*a*b)/10
		note = z
		self.dev.play_tone(note, time*1000)
		if wait:
			sleep(time)

	
	def touch(self, port):
		"""Returns the state of the touch sensor."""
		return Touch(self.dev, port-1).get_sample()
	
	def sound(self, port):
		"""Returns the level of sound from 0 to 100."""
		level = Sound(self.dev, port-1).get_sample()
		level /= 1023.0
		level *= 100
		level = int(round(level))
		return level
	
	def light(self, port):
		"""Returns the level of light from 0 to 100.
		UNTESTED!!!"""
		level = Light(self.dev, port-1).get_sample()
		level /= 1023.0
		level *= 100
		level = int(round(level))
		return level
	
	def lamp(self, port, active):
		"""Turn on or off the lamp on the light sensor
		Of selected port."""
		Light(self.dev, port-1).set_illuminated(active)
	
	# This doesn't work and returns weird values (1 or 5) regardless of color
	# def color(self, port):
		# """Returns the color read by the color sensor."""
		# colorType = Color20(self.dev, port-1).get_sample()
		# # if colorType == common.Type.COLORFULL:
			# # return "White"
		# # elif colorType == common.Type.COLORNONE:
			# # return "Black"
		# # elif colorType == common.Type.COLORRED:
			# # return "Red"
		# # elif colorType == common.Type.COLORGREEN:
			# # return "Green"
		# # elif colorType == common.Type.COLORBLUE:
			# # return "Blue"
		# return colorType
	
	def colorLamp(self, port, color):
		colorType = common.Type.COLORFULL # White
		if color.lower() == "red":
			colorType = common.Type.COLORRED
		elif color.lower() == "green":
			colorType = common.Type.COLORGREEN
		elif color.lower() == "blue":
			colorType = common.Type.COLORBLUE
		elif color.lower() == "black" or color.lower() == "off":
			colorType = common.Type.COLORNONE
		Color20(self.dev, port-1).set_light_color(colorType)
	
	def ultrasonic(self, port, convertToIn=True):
		"""Returns the distance to an object in cm.
		If convertToIn is true, the value is converted to in."""
		dist = Ultrasonic(self.dev, port-1).get_sample()
		if convertToIn:
			dist /= 2.54
			dist = int(round(dist))
		return dist
	
	ultra = ultrasonic
	
	def buttons(self):
		"""Returns the current state of the NXT buttons
		In the form of a dict.
		Use buttons()["enter"] to get the current state of the enter button, etc."""
		raise HaventGottenToThatYetError, "I ain't done writing this code yet."
	
	def encoder(self, port):
		"""Returns the value of the encoder (rotation sensor/tachometer)
		On the motor of the specified port."""
		# Which motor?
		if port.upper() == "A" or port == 0:
			myMotor = self.a
		elif port.upper() == "B" or port == 1:
			myMotor = self.b
		else: # C
			myMotor = self.c
		return myMotor.dev.get_tacho().rotation_count
	
	def thread(self, func, *args, **kwargs):
		"""Create a new thread with the specified function and arguments."""
		newThread = Thread(target=func, args=args, kwargs=kwargs)
		newThread.daemon = True
		newThread.start()
	
	def read(self, filename):
		"""Read the file and return the contents. Uses pickle when necessary."""
		pickled = False
		onlyfiles = [f for f in listdir("/home/pi/mindjackerFiles/") if isfile(join("/home/pi/mindjackerFiles/", f))]
		for f in onlyfiles:
			if filename + ".txt" == f:
				filename = "/home/pi/mindjackerFiles/"+filename+".txt"
				break
			if filename + ".pkl" == f:
				filename = "/home/pi/mindjackerFiles/"+filename+".pkl"
				pickled = True
				break
		else:
			raise IOError, "File does not exist"
		if pickled:
			with open(filename, "rb") as myFile:
				return load(myFile)
		with open(filename, "r") as myFile:
			return myFile.read()
	
	def write(self, filename, data):
		"""Write to the file. Uses pickle when necessary."""
		if data == "": # If there's no data, we're asked to remove.
			try:
				remove("/home/pi/mindjackerFiles/"+filename+".txt")
			except OSError:
				pass
			try:
				remove("/home/pi/mindjackerFiles/"+filename+".pkl")
			except OSError:
				pass
			return
		# What follows: Making sure we don't have myfile.txt and myfile.pkl at the same time.
		onlyfiles = [f for f in listdir("/home/pi/mindjackerFiles/") if isfile(join("/home/pi/mindjackerFiles/", f))]
		for f in onlyfiles:
			if filename + ".txt" == f:
				remove("/home/pi/mindjackerFiles/"+filename+".txt")
			if filename + ".pkl" == f:
				remove("/home/pi/mindjackerFiles/"+filename+".pkl")
		# Now should we use pickle?
		if type(data) in [int, str, float, bool, long, unicode]:
			self._writeText(filename, data)
		else:
			self._pickle(filename, data)
	
	def _writeText(self, filename, data):
		with open("/home/pi/mindjackerFiles/"+filename+".txt", "w") as myFile:
			myFile.write(str(data))
	
	def _pickle(self, filename, data):
		with open("/home/pi/mindjackerFiles/"+filename+".pkl", "wb") as myFile:
			dump(data, myFile)
	
	def keepAlive(self):
		"""Stop the NXT from falling asleep."""
		raise HaventGottenToThatYetError, "I ain't done writing this code yet."
	
	def motor(self, port, power, degrees=None, rotations=None, seconds=None, brake=True):
		"""Move one motor. Set only one (or none at all) of degrees, rotations, seconds."""
		power /= 100.0
		power *= 127
		power = int(round(power))
		# Which motor?
		if port.upper() == "A" or port == 0:
			myMotor = self.a
		elif port.upper() == "B" or port == 1:
			myMotor = self.b
		else: # C
			myMotor = self.c
		# If power is zero, we're being asked to stop the motor.
		if power == 0:
			if brake:
				myMotor.brake()
			else:
				myMotor.coast()
			return
		
		# What are we doing? For a duration, or unlimited?
		if degrees != None:
			myMotor.turn(power, degrees, brake)
		elif rotations != None:
			myMotor.turn(power, rotations*360, brake)
		elif seconds != None:
			ts = time()
			myMotor.run(power)
			while time() < ts + seconds:
				pass
			if brake:
				myMotor.brake()
			else:
				myMotor.coast()
		else: # No params provided, run unlimited.
			myMotor.run(power)
	
	def resetMotor(self, port=None):
		"""Reset the motor(s) internal encoders."""
		# Which motor?
		if port.upper() == "A" or port == 0:
			myMotor = self.a
		elif port.upper() == "B" or port == 1:
			myMotor = self.b
		else: # C
			myMotor = self.c
		myMotor.dev.reset_position(False)

class Display:
	def __init__(self):
		pass
	
	def text(self, text, x, y):
		"""Draw text on the screen."""
		raise HaventGottenToThatYetError, "I ain't done writing this code yet."
	
	def line(self, x1, y1, x2, y2):
		"""Draw a line on the screen."""
		raise HaventGottenToThatYetError, "I ain't done writing this code yet."
	
	def circle(self, x, y, radius):
		"""Draw a circle on the screen."""
		raise HaventGottenToThatYetError, "I ain't done writing this code yet."
	
	def image(self, filename):
		"""Draw an image on the screen."""
		raise HaventGottenToThatYetError, "I ain't done writing this code yet."

class Calibrator:
	def __init__(self):
		pass
	
	def sound(self, end):
		"""Calibrate the sound sensor.
		end: False for minimum, True for maximum."""
		raise HaventGottenToThatYetError, "I ain't done writing this code yet."
	
	def light(self):
		"""Calibrate the light sensor. 
		end: False for minimum, True for maximum."""
		raise HaventGottenToThatYetError, "I ain't done writing this code yet."

class mjMotor:
	def __init__(self, brick, port):
		self.dev = Motor(brick, port)
	
	def degrees(self):
		'''Get the current rotation'''
		return self.dev.get_tacho()
	
	def run(self, power):
		'''Run the motor indefinitely'''
		power /= 128.0
		power *= 100
		self.dev.run(int(round(power)))
	
	def brake(self):
		'''Stop the motor quickly'''
		self.dev.brake()
	
	def coast(self):
		'''Motor coasts to a stop'''
		self.dev.idle()
	
	def turn(self, power, degrees, brake=True):
		'''Turn a certain number of degrees'''
		power /= 128.0
		power *= 100
		self.dev.turn(int(round(power)), degrees, brake)
