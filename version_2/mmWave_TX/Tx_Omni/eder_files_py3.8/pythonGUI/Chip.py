#from Common import *
import ast
from collections import OrderedDict


class Chip(object):

	def __init__(self, configFile):
		self.groups = []
		self.readConfig(configFile)

	def show(self):
		for group in self.groups:
			group.show()

	def readConfig(self, configFile):
		#Create register and add to the groups list of registers
		with open(configFile) as config:
			currentLine = 0
			for line in config:
				currentLine += 1
				if line.startswith("%"):
					continue
				name = line.split("\n")[0]
				group = Group(name)
				#print(group.getName())
				for line in config:
					currentLine += 1
					if line.startswith("%"):
						continue
					if line.startswith("#"):
						#All registers are now added to the group, add the group to the chip
						self.addGroup(group)
						break
					configLine = line.split(":")
					registerName = configLine[0]
					registerVars = ast.literal_eval(configLine[1].lstrip(' '))
					register = Register(registerName, registerVars[0],registerVars[1],registerVars[2])
					#print(len(configLine))
					try:
						#Read the control 2dArray and add controls
						registerControls = ast.literal_eval(configLine[2].lstrip(' '))
						for i in range(len(registerControls)):
							#print(registerControls[i][2])
							control = Control(registerControls[i][0],registerControls[i][1],registerControls[i][2])
							#print("created control")
							register.addControl(control)
					except:
						#If something is wrong with the file, print and dont add controls
						print ("Error in config file on line", currentLine, ", control not added to register", registerName)
					group.addRegister(register, registerName)
		self.addGroup(group)
		config.close()
		"""for group in self.groups:
			print(group.getName())
			for register in group.getRegisters():
				print(register.getName(),format(register.getPhysAddr(),'#02x'), register.getSize(),format(register.getReset(),'#02x'))
		"""



	def addGroup(self, group):
		self.groups.append(group)


	def getGroups(self):
		return self.groups

	def getGroup(self, groupName):
		for group in self.groups:
			if group.getName() == groupName:
				return group
class Group:
	"""Contains a list of registers."""
	
	def __init__(self, name):
		self.name = name
		self.registers = OrderedDict()

	def show(self):
		print('GROUP:',self.getName())
		for register in self.getRegisters():
			register.show()

	def setName(self, name):
		self.name = name

	def getName(self):
		return self.name

	def addRegister(self, register, registerName):
		self.registers[registerName] = register

	def setRegisters(self, registers):
		self.registers = registers

	def getRegisters(self):
		return self.registers

	def getRegister(self, registerName):
		return self.registers[registerName]


class Register:
	""" Has a list of controls, a size, a physical address, and a hardware reset"""
	def __init__(self, name, physAddr,size, reset):
		self.name = name
		self.size = size
		self.physAddr = physAddr
		self.reset = reset
		self.controls = {}

	def show(self):
		print('REGISTER:',self.getName(), self.getPhysAddr(), self.getEndBit(), self.getReset())
		for key in self.getControls():
			control = self.controls[key]
			control.show()

	def getControls(self):
		return self.controls

	def getControl(self,key):
		return self.controls[key]

	def addControl(self,control):
		self.controls[control.getName()] = control

	def getName(self):
		return self.name

	def getPhysAddr(self):
		return self.physAddr

	def getSize(self):
		return self.size

	def getReset(self):
		return self.reset

	def calculateValue(self):
		binary = 0
		for key in self.controls:
			control = self.controls[key]
			binary += control.variable<<control.startBit
		return binary




class Control:
	"""Has a name and a number of bits that the control is to change. Might need to split up to subclasses"""
	def __init__(self, name, startBit, endBit):
		self.name = name
		self.startBit = startBit
		self.endBit = endBit
		self.variable = 0

	def show(self):
		print('CONTROL:',self.getName(), self.getStartBit(), self.endBit())

	def getName(self):
		return self.name

	def getStartBit(self):
		return self.startBit

	def getEndBit(self):
		return self.endBit

	def getValue(self):
		return self.variable
	
	def setValue(self, value):
		self.variable = value

	def getVar(self):
            return self.variable

