#!/usr/bin/env python
# wax database generator
# Copyright (C) 2008 Benjamin Deering
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
   

 
#   This program converts an ASCII file with #delineated comments into a sqlite datebase
#   to be read by the python elementary wax chooser

#Items within the input file should be formatted as follows
#a new type of wax should begin with the word Wax
#the following lines should set the properties of the wax in no particular order
#Wax
#Transformed	-9	1#All temperatures are Celsius
#New	-5	0
#Brand	Swix
#Klister	No
#Color	Blue
#Name	Blue Extra
#Picture File	/swixblue.png

 
#The database will have a table for each wax brand
#Each wax brand table will have the following columns:
#Name (V05 Polar for example)
#Color (White)
#New snow max temperature (Degrees C) (-12)
#New snow min temperature (Degrees C) (-25)
#Transformed snow max temperature (-15)
#Transfored snow min temperature (-30)
#Name of icon/picture (v0005.png)
#Klister (No)
import getopt,sys,struct, sqlite3
from sets import Set
#Change max in the lines below to min for Endian trouble
#All integers will be sent in 8 bits
Waxes=[]
Brands = Set()
def help():
	print "Usage: WaxDBBuilder -i INPUTFILE -o OUTPUTFILE\n"
	print "\n\nSee README file for input file format\n"
	sys.exit(2)
#Read the fields from the file, put them into an object of class wax
#and return the object
def parsewax  ( inputfile):
	tmpwax=Wax()
	line=inputfile.readline()
	while  not (line.startswith("Wax")) and len(line)!=0:
		if line[0]!="#":
			usefulpart=line.split("#",2)
			if usefulpart[0].startswith("Brand"):
				tmpwax.brand=(usefulpart[0].split(None,1))[1].strip()
				Brands.add((usefulpart[0].split(None,1))[1].strip())
			if usefulpart[0].startswith("Picture"):
				tmpwax.picturefile=(usefulpart[0].split())[1].strip()
			if usefulpart[0].startswith("Klister"):
				tmpwax.klister=(usefulpart[0].split())[1].startswith("Y")
			if usefulpart[0].startswith("New"):
				tmpwax.newTempRange[0]=int((usefulpart[0].split())[1])
				tmpwax.newTempRange[1]=int((usefulpart[0].split())[2])
			if usefulpart[0].startswith("Transformed"):
                                tmpwax.transformedTempRange[0]=int((usefulpart[0].split())[1])
                                tmpwax.transformedTempRange[1]=int((usefulpart[0].split())[2])
			if usefulpart[0].startswith("Name"):
                                tmpwax.name=(usefulpart[0].split(None,1))[1].strip()
			if usefulpart[0].startswith("Color"):
				tmpwax.color=(usefulpart[0].split())[1].strip()

		line=inputfile.readline()
	inputfile.seek(-len(line),1)#put back the Wax keyword
	return (tmpwax)
class Wax:
	def __init__(self):
		self.brand=""
		self.name=""
		self.color=""
		self.newTempRange=[0,0]
		self.transformedTempRange=[0,0]
		self.klister=False  
		self.picturefile=""
def main():	
	#Parse commandline options
	try:
			opts, args = getopt.getopt(sys.argv[1:],"i:o:h",["input=","output=","help"])
	except  getopt.GetoptError: #if anything goes wrong print help and exit
		help()
	input=""
	output=""
	for o, a in opts:
		if o in ("-i","--input"):
			input=a
		if o in ("-o","--output"):
			output=a
		if o in ("-h","--help"):
			help()
	

	#Open the 2 files
	#input is read only
	#output is write, binary
	if input=="":
		help()
	if output=="":
		help()
	inputfile=open(input,'r')
	outputdbconn=sqlite3.connect(output)
	counter=0
	line=inputfile.readline()
	while  len(line)!=0:  
		if line[0]!="#":
			usefulpart=line.split("#",2)
			if usefulpart[0].startswith("Wax"):
				Waxes.append(parsewax(inputfile))
				counter+=1 
		line=inputfile.readline()
	print counter," Waxes read"


	outputdbcurs = outputdbconn.cursor()
	
	for brand in Brands:
		outputdbcurs.execute('''create table %s(name text, color text, picture text, newMinTemp real, newMaxTemp real, transMinTemp real, transMaxTemp real, isKlister integer)''' % brand)
                     

	
	for wax in Waxes:
		command = 'insert into %s values %s, %s, %s ' % (wax.brand, wax.name, wax.color, wax.picturefile)
		#print command		
		outputdbcurs.execute('''insert into %s values('%s', '%s', '%s', %f, %f, %f, %f, %f)''' % (wax.brand, wax.name, wax.color, wax.picturefile, wax.newTempRange[1], wax.newTempRange[0], wax.transformedTempRange[1], wax.transformedTempRange[0], wax.klister)); 
		#S wax.newTempRange[0], wax.newTempRange[1], wax.transformedTempRange[0], wax.transformedTempRange[1], wax.klister)
		#Show the user which waxes we found
		print wax.brand,"\t",wax.name
	outputdbconn.commit()
	outputdbcurs.close()  
	print "Found ",counter," waxes."
	inputfile.close()
if __name__=="__main__":
	main()
