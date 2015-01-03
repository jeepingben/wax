# -*- coding: utf-8 -*-

# Wax Chooser -- A utility for finding the ski wax best for the given conditions
#
# Copyright (C) 2011 Benjamin Deering <waxChooserMaintainer@swissmail.org>
# http://jeepingben.homelinux.net/wax/
#
# This file is part of Wax-chooser.
#
# Wax-chooser is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Wax-chooser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
import sys, os, signal
import elementary, evas, ecore
import ConfigParser
import sqlite3
from const import *
	
class waxGUI(object):

	def __init__ (self):
		self.brands = []
		self.enabledBrands = {}
		self.usingCelsius = 0
		self.usingSensor = 0
		self.sensorTemperature = 1
		self.LoadDB()
		self.configfile = os.path.expanduser ('~/.wax-chooser.cfg')
		self.config = ConfigParser.SafeConfigParser ()
		self.LoadConfig (self.configfile)
		self.widgets = self.build_gui ()
		self.sensorTimer = ecore.timer_add( 1, self.updateSensorLabel )
		self.image_path = './'
		self.widgets['mainwin'].show ()
		self.snow_cond = 0
		self.humidity = 1
		self.bestAveTemp = 9999
		signal.signal(signal.SIGINT, self.interrupted)

		elementary.init()                            
                                               
		elementary.run()                                            
		elementary.shutdown()           
	
	def interrupted (self, signal, frame):
		self.sensorTimer.delete()
		self.SaveConfig (self.configfile)
		elementary.exit ()
	def build_gui (self):

		def destroy (obj, *args, **kargs):
			
			self.sensorTimer.delete()
			self.SaveConfig (self.configfile)
			elementary.exit ()

		gui_items = dict ()

		# Start elementary
		elementary.init ()

		# Create main window
		gui_items['mainwin'] = elementary.Window ("Wax-Chooser", elementary.ELM_WIN_BASIC)
		gui_items['mainwin'].title_set ("Wax-Chooser")
		gui_items['mainwin'].callback_destroy_add (destroy)

		# Create background
		bg = elementary.Background (gui_items['mainwin'])
		bg.size_hint_weight_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		bg.size_hint_min_set (200,300)
		gui_items['mainwin'].resize_object_add (bg)
		bg.show ()

		# Create main box (vertical by default)
		gui_items['mainbox'] = elementary.Box (gui_items['mainwin'])
		gui_items['mainbox'].size_hint_weight_set (evas.EVAS_HINT_EXPAND, 1.0)
		gui_items['mainbox'].size_hint_align_set (-1.0, evas.EVAS_HINT_FILL)
		gui_items['mainwin'].resize_object_add (gui_items['mainbox'])
		gui_items['mainbox'].show ()

		# Create title label
		gui_items['title'] = elementary.Label (gui_items['mainwin'])
		gui_items['title'].text_set ("Current Conditions")
		gui_items['mainbox'].pack_start (gui_items['title'])
		gui_items['title'].size_hint_weight_set (1.0, evas.EVAS_HINT_FILL)
		gui_items['title'].size_hint_align_set (0.5, -1.0)
		gui_items['title'].show ()

		# Create scroller to hold condition descripion items
		self.sc2 = elementary.Scroller(gui_items['mainwin'])
		self.sc2.bounce_set(0, 0)
		self.sc2.size_hint_weight_set(evas.EVAS_HINT_EXPAND, 1.0)
		self.sc2.size_hint_align_set(-1.0, evas.EVAS_HINT_FILL)
		gui_items['mainbox'].pack_end(self.sc2)
		self.sc2.show()
		gui_items['mainwin'].resize_object_add (self.sc2)
		
		# Create condtion description box (vertical by default)
		box2 = elementary.Box (gui_items['mainwin'])
		box2.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 1.0)
		box2.size_hint_align_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		self.sc2.content_set (box2)
		box2.show ()
		

		gui_items['rows'] = []
		
		# Create four boxes: temperature, humidity, snow type, and buttons, set as horizonal
		tbox = elementary.Box (gui_items['mainwin'])
		#tbox.horizontal_set (1)
		#box1.homogenous_set (1)
		tbox.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		tbox.size_hint_align_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		box2.pack_end (tbox)
		tbox.show ()
		
		# Create temperature widget label
		
		tl = elementary.Label (gui_items['mainwin'])
		tl.text_set ('Temperature')
		tbox.pack_start( tl )
		tl.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		tl.size_hint_align_set (0.4, 0.5)
		tl.show ()
						
		# Create temperature slider
		gui_items['temperatureSlider'] = elementary.Slider (gui_items['mainwin'])
		gui_items['temperatureSlider'].size_hint_weight_set (1, 0)
		gui_items['temperatureSlider'].size_hint_align_set (-1, 0)
		if self.usingCelsius:
			gui_items['temperatureSlider'].min_max_set (-30.0, 10.0)
			gui_items['temperatureSlider'].value = 0
		else:
			gui_items['temperatureSlider'].min_max_set (-15.0, 45.0)
			gui_items['temperatureSlider'].value = 32
		gui_items['temperatureSlider'].unit_format_set( '%1.1f degrees' )
		tbox.pack_end (gui_items['temperatureSlider'])
		gui_items['temperatureSlider'].show ()
		
		
		tsbox = elementary.Box (gui_items['mainwin'])
		tsbox.horizontal_set (1)
		tsbox.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		tsbox.size_hint_align_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		box2.pack_end (tsbox)
		tsbox.show ()

		# Create Use Sensor button
		gui_items['sensorButton'] = elementary.Button (gui_items['mainwin'])
		gui_items['sensorButton']._callback_add ('clicked', self.setTemperatureFromSensor)
		ic = elementary.Icon(gui_items['sensorButton'])
		ic.file_set(os.path.join(IMAGE_DIR, "thermometer.png"))
		gui_items['sensorButton'].icon_set( ic)
		gui_items['sensorButton'].text_set( "Searching for sensor" )
		gui_items['sensorButton'].size_hint_weight_set (evas.EVAS_HINT_EXPAND, 1.0)
		gui_items['sensorButton'].size_hint_align_set (evas.EVAS_HINT_FILL, 1.0)
		
		tsbox.pack_end (gui_items['sensorButton'])
		if self.usingSensor:
			gui_items['sensorButton'].show ()
		
		######## Humidity ############		
		hbox = elementary.Box (gui_items['mainwin'])
		#box1.homogenous_set (1)
		hbox.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		hbox.size_hint_align_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		box2.pack_end (hbox)
		hbox.show ()
		gui_items['mainwin'].resize_object_add (hbox)
		
		#create humidity widget label
		hl = elementary.Label (gui_items['mainwin'])
		hl.text_set ('Humidity')
		hl.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 1.0)
		hl.size_hint_align_set (0.45, 0.5)
		hbox.pack_start (hl)		
		hl.show ()
		
		hbox2 = elementary.Box (gui_items['mainwin'])
		hbox2.horizontal_set (1)
		#box1.homogenous_set (1)
		hbox2.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		hbox2.size_hint_align_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		hbox.pack_end (hbox2)
		gui_items['mainwin'].resize_object_add (hbox2)
		hbox2.show ()	
		
		#Create humidity toolbar
		rhtoolbar = elementary.Toolbar(gui_items['mainwin'])
		rhtoolbar.menu_parent_set(gui_items['mainwin'])
		rhtoolbar.homogenous_set(0)		
		rhtoolbar.icon_size_set( 64 )		
	#	print str( rhtoolbar.icon_size )
		rhtoolbar.icon_size = ( 96 )		
	#	print str( rhtoolbar.icon_size )
		
		rhtoolbar.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)                                                            
		rhtoolbar.size_hint_align_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		rhtoolbar.item_append(os.path.join(IMAGE_DIR, 'medrh.png'), "Normal", self.setHumidity,humidity=NORMAL_HUMIDITY)
		rhtoolbar.item_append(os.path.join(IMAGE_DIR, 'highrh.png'), "High", self.setHumidity,humidity=HIGH_HUMIDITY)
		rhtoolbar.first_item_get().selected_set(True)
		hbox2.pack_end( rhtoolbar )
		rhtoolbar.show()
		
		
		######## Snow Condition ############		
		sbox = elementary.Box (gui_items['mainwin'])
		#box1.homogenous_set (1)
		sbox.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		sbox.size_hint_align_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		box2.pack_end (sbox)
		sbox.show ()
		
		
		#create snow cond widget label
		sl = elementary.Label (gui_items['mainwin'])
		sl.text_set ('Snow Condition')
		sl.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		sl.size_hint_align_set (0.45, 0.5)
		sbox.pack_start (sl)		
		sl.show ()
		
		sbox2 = elementary.Box (gui_items['mainwin'])
		sbox2.horizontal_set (1)
		#box1.homogenous_set (1)
		sbox2.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		sbox2.size_hint_align_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		sbox.pack_end (sbox2)
		sbox2.show ()	
		
		#Create Snow condition toolbar
		sctoolbar = elementary.Toolbar(gui_items['mainwin'])
		sctoolbar.menu_parent_set(gui_items['mainwin'])
		sctoolbar.homogenous_set(0)
		sctoolbar.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)                                                            
		sctoolbar.size_hint_align_set (evas.EVAS_HINT_FILL, 1.0)
		sctoolbar.item_append(os.path.join(IMAGE_DIR, 'newsnow.png'), "New", self.setSnowCond,snowcond=NEW_SNOW)
		sctoolbar.item_append(os.path.join(IMAGE_DIR, 'transformedsnow.png'), "Transformed", self.setSnowCond,snowcond=OLD_SNOW)
		sctoolbar.item_append(os.path.join(IMAGE_DIR, 'corn.png'), "Corn", self.setSnowCond,snowcond=CORN_SNOW)
		sctoolbar.item_append(os.path.join(IMAGE_DIR, 'ice.png'), "Ice", self.setSnowCond,snowcond=ICY_SNOW)
		sctoolbar.first_item_get().selected_set(True)		
		sbox2.pack_end( sctoolbar )
		sctoolbar.show()
			
		# Create bottom button row (prev, next city & refresh)
		box3 = elementary.Box (gui_items['mainwin'])
		box3.horizontal_set (1)
		box3.homogenous_set (1)
		box3.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		box3.size_hint_align_set (evas.EVAS_HINT_FILL, 1.0)
		gui_items['mainbox'].pack_end (box3)
		box3.show ()

		# Find Wax button
		bt = elementary.Button (gui_items['mainwin'])
		bt.text_set ('Find Wax')
		bt._callback_add ('clicked', self.find_wax)
		bt.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 1.0)
		bt.size_hint_align_set (evas.EVAS_HINT_FILL, 1.0)
		# Add a prev icon to the button
		box3.pack_end (bt)
		bt.show ()

		# Settings button
		bt = elementary.Button (gui_items['mainwin'])
		bt.text_set ('Settings')
		bt._callback_add ('clicked', self.settingsDialog)
		bt.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 1.0)
		bt.size_hint_align_set (evas.EVAS_HINT_FILL, 1.0)
		# Add a next icon to the button
		box3.pack_end (bt)
		bt.show ()

		
		#####
		# Create wax display box (vertical by default)
		gui_items['waxbox'] = elementary.Box (gui_items['mainwin'])
		gui_items['waxbox'].size_hint_weight_set (evas.EVAS_HINT_FILL, 1.0)
		gui_items['waxbox'].size_hint_align_set (evas.EVAS_HINT_FILL, -1.0)
		gui_items['waxLabel'] = elementary.Label(gui_items['mainwin'])
		gui_items['waxLabel'].text_set("Wax")
		gui_items['waxbox'].pack_start(gui_items['waxLabel'])
		gui_items['waxLabel'].show()
		# Create box to hold the wax picture
	
		sc = elementary.Scroller(gui_items['waxbox'])
		sc.bounce_set(0, 0)
		sc.size_hint_weight_set(evas.EVAS_HINT_EXPAND, 0.5)
		sc.size_hint_align_set(evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		
		
		ib = elementary.Box(gui_items['mainwin'])
		ib.size_hint_weight_set(evas.EVAS_HINT_EXPAND, 0.5)
		ib.size_hint_align_set(evas.EVAS_HINT_FILL, 0.5)
		gui_items['waxicon'] = elementary.Icon(gui_items['mainwin'])
		gui_items['waxicon'].size_hint_weight_set(1.0, 0.5)
		gui_items['waxicon'].scale_set(0.2, 0.2)
		gui_items['waxicon'].size_hint_align_set(0.5, 0.0)
		ib.pack_end(gui_items['waxicon'])
		gui_items['mainwin'].resize_object_add (ib)
		
		gui_items['waxicon'].show()
		
		gui_items['waxtext'] = elementary.Entry( gui_items['mainwin'] )
		gui_items['waxtext'].size_hint_weight_set(evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		gui_items['waxtext'].size_hint_align_set(-1.0, 0.0)
		gui_items['waxtext'].scale_set(1)
		ib.pack_end(gui_items['waxtext'])
		gui_items['waxtext'].show()
		sc.content_set(ib)
		gui_items['waxbox'].pack_end(sc)
		gui_items['mainwin'].resize_object_add (sc)
		ib.show()
		sc.show()
		
		# Create bottom button row (warmer back colder)
		box3 = elementary.Box (gui_items['mainwin'])
		box3.horizontal_set (1)
		box3.homogenous_set (1)
		box3.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		box3.size_hint_align_set (evas.EVAS_HINT_FILL, 1.0)
		gui_items['waxbox'].pack_end (box3)
		box3.show ()
		gui_items['mainwin'].resize_object_add (box3)
		
		# Create the warmer button
		bt = elementary.Button (gui_items['mainwin'])
		bt.text_set ('Warmer')
		bt._callback_add ('clicked', self.warmerWax)
		bt.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 0.0)
		bt.size_hint_align_set (evas.EVAS_HINT_FILL, 0.0)
		box3.pack_end (bt)
		bt.show ()

		# Create the back button
		bt = elementary.Button (gui_items['mainwin'])
		bt.text_set ('Back')
		bt._callback_add ('clicked', self.closeWax)
		bt.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 0.0)
		bt.size_hint_align_set (evas.EVAS_HINT_FILL, 0.0)
		box3.pack_end (bt)
		bt.show ()
		
		# Create the Colder button
		bt = elementary.Button (gui_items['mainwin'])
		bt.text_set ('Colder')
		bt._callback_add ('clicked', self.colderWax)
		bt.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 0.0)
		bt.size_hint_align_set (evas.EVAS_HINT_FILL, 0.0)
		box3.pack_end (bt)
		bt.show ()
		
		gui_items['mainwin'].resize_object_add (gui_items['waxbox'])
		gui_items['waxbox'].hide ()
		
		#####
		# Create about box (vertical by default)
		gui_items['aboutbox'] = elementary.Box (gui_items['mainwin'])
		gui_items['aboutbox'].size_hint_weight_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		gui_items['aboutbox'].size_hint_align_set (-1.0, -1.0)
		al = elementary.Label(gui_items['mainwin'])
		al.size_hint_weight_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		al.size_hint_align_set (0.5, -1.0)
		al.text_set("About waxChooser")
		gui_items['aboutbox'].pack_start(al)
		al.show()
		sc2 = elementary.Scroller(gui_items['mainwin'])
		sc2.bounce_set(0, 0)
		sc2.size_hint_weight_set(evas.EVAS_HINT_EXPAND, 1.0)
		sc2.size_hint_align_set(evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		gui_items['aboutbox'].pack_end(sc2)
		gui_items['mainwin'].resize_object_add (sc2)
		sc2.show()

		ib =    elementary.Box(gui_items['aboutbox'])
		ic = elementary.Icon(gui_items['aboutbox'])
		ic.size_hint_weight_set(evas.EVAS_HINT_FILL,1.0)
		ic.scale_set(0, 0) 
		ic.size_hint_align_set(0.5, 0.5)
		gui_items['mainwin'].resize_object_add(ic)
		ic.file_set(os.path.join(IMAGE_DIR, "author.png"))
		ib.size_hint_weight_set(evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		ib.size_hint_align_set(evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		ib.pack_end(ic)
		sc2.content_set(ib)

		ic.show()
		gui_items['mainwin'].resize_object_add (ic)
		
		# Create text box with 'about' info
		at = elementary.Entry( gui_items['mainbox'] )
		at.size_hint_weight_set(1.0, 0.0)
		at.size_hint_align_set(evas.EVAS_HINT_FILL, 0.0)
		at.scale_set(1)
		info = self.infoadd("waxChooser " + APP_VERSION)
		info += self.infoadd("Copyright (c) 2011 Benjamin Deering")
		info += self.infoadd("<waxChooserMaintainer@swissmail.org>" )
		at.text_set( info )	
		gui_items['aboutbox'].pack_end(at)
		at.show()
		
		# Create bottom button row (back, about)
		box3 = elementary.Box (gui_items['mainwin'])
		box3.horizontal_set (1)
		box3.homogenous_set (1)
		box3.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		box3.size_hint_align_set (-1.0, 0.0)
		gui_items['aboutbox'].pack_end (box3)
		box3.show ()
		# Create the back button
		bt = elementary.Button (gui_items['mainwin'])
		bt.text_set ('Back')
		bt._callback_add ('clicked', self.hideAbout)
		bt.size_hint_weight_set (evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_FILL)
		bt.size_hint_align_set (evas.EVAS_HINT_FILL, -1.0)
		box3.pack_end (bt)
		bt.show ()
		
		gui_items['mainwin'].resize_object_add (gui_items['aboutbox'])
		
		#####
		# Create settings box (vertical by default)
		gui_items['settingsbox'] = elementary.Box (gui_items['mainwin'])
		gui_items['settingsbox'].size_hint_weight_set (evas.EVAS_HINT_EXPAND, 1.0)
		gui_items['settingsbox'].size_hint_align_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		settingsLabel = elementary.Label(gui_items['mainwin'])
		settingsLabel.text_set('Settings')
		settingsLabel.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 0.0)
		settingsLabel.size_hint_align_set (0.5, -1.0)
		gui_items['settingsbox'].pack_start( settingsLabel)
		settingsLabel.show()	
		
		# Create scroller to hold settings toggles items
		sc2 = elementary.Scroller(gui_items['mainwin'])
		sc2.bounce_set(0, 0)
		sc2.size_hint_weight_set(evas.EVAS_HINT_EXPAND, 1.0)
		sc2.size_hint_align_set(evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		gui_items['settingsbox'].pack_end(sc2)
		gui_items['mainwin'].resize_object_add (sc2)
		sc2.show()
		
		tb = 	elementary.Box(gui_items['settingsbox'])
		
		
		ut = elementary.Check (gui_items['mainwin'])
		ut.text_set('Units')
		ut.style_set("toggle")
		ut.text_part_set( 'off', 'Fahrenheit' )
		ut.text_part_set( 'on', 'Celsius' )
		ut.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 0.0)
		ut.size_hint_align_set (evas.EVAS_HINT_FILL, 0.0)
		tb.pack_end( ut )
		ut.state_set(self.usingCelsius)
		ut._callback_add('changed',self.setUnits)
		ut.show()
		
		for brand in self.brands:
			ut = elementary.Check (gui_items['mainwin'])
			ut.style_set("toggle")
			ut.text_set(brand)
			ut.text_part_set( 'on', 'enabled' )
			ut.text_part_set( 'off', 'disabled' )   
			ut.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 0.0)
			ut.size_hint_align_set (evas.EVAS_HINT_FILL, 0.0)
			ut.state_set(eval(self.enabledBrands[brand]))
			tb.pack_end( ut )
			ut._callback_add('changed',self.enableBrands,brand=brand)
			ut.show()

		ut = elementary.Check (gui_items['mainwin'])
		ut.text_set('Use MLX90614')
		ut.style_set("toggle")
		ut.text_part_set( 'on', 'Yes' )
		ut.text_part_set( 'off', 'No' )  
		ut.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 0.0)
		ut.size_hint_align_set (evas.EVAS_HINT_FILL, 0.0)
		tb.pack_end( ut )
		ut.state_set(self.usingSensor)
		ut._callback_add('changed',self.setSensor)
		ut.show()
		tb.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 0.0)
		tb.size_hint_align_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)		
		tb.show()	
		#gui_items['settingsbox'].pack_end( tb )	
		sc2.content_set(tb)
		# Create bottom button row (back, about)
		box3 = elementary.Box (gui_items['mainwin'])
		box3.horizontal_set (1)
		box3.homogenous_set (1)
		box3.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 0.0)
		box3.size_hint_align_set (evas.EVAS_HINT_FILL, 0.0)
		gui_items['settingsbox'].pack_end (box3)
		box3.show ()
			
		# Create the back button
		bt = elementary.Button (gui_items['mainwin'])
		bt.text_set ('Back')
		bt._callback_add ('clicked', self.closeSettings)
		bt.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 0.0)
		bt.size_hint_align_set (evas.EVAS_HINT_FILL, 0.0)
		box3.pack_end (bt)
		bt.show ()
		
		# Create the about button
		bt = elementary.Button (gui_items['mainwin'])
		bt.text_set ('About')
		bt._callback_add ('clicked', self.showAbout)
		bt.size_hint_weight_set (evas.EVAS_HINT_EXPAND, 0.0)
		bt.size_hint_align_set (evas.EVAS_HINT_FILL, 0.0)
		box3.pack_end (bt)
		bt.show ()
		
		
		#self.widgets['settingsbox'].pack_start(settingsTitle)	
		gui_items['mainwin'].resize_object_add (gui_items['settingsbox'])
		gui_items['settingsbox'].hide ()
		
		
		return gui_items
	def changeWax( self, *args, **kargs ):
		 direction = kargs.get('direction')
		 isKlisterVal = 0		 
		 if self.snow_cond == CORN_SNOW or self.snow_cond == ICY_SNOW:
		 	isKlisterVal = 1
		 
		 minTempStr = 'newMinTemp'
		 maxTempStr = 'newMaxTemp'
		 minTempIdx = 3
		 maxTempIdx = 4
		 if( self.snow_cond == OLD_SNOW ):
		 	 minTempStr = 'transMinTemp'
			 maxTempStr = 'transMaxTemp'
			 minTempIdx = 5
			 maxTempIdx = 6
		 bestResult = None
		 bestdiff = 9999
		 bestBrand = None
		 for brand in self.brands:
		 	if self.enabledBrands[brand] != 'True':
		 		#debugprint "Brand" + brand + "disabled"
		 		continue
		 	if direction == 'Warmer':
		 		queryString ='''select * from %s where %f < (%s + %s) / 2 AND isKlister == %d order by (%s + %s) / 2.0 ''' % (brand, self.bestAveTemp, maxTempStr, minTempStr, isKlisterVal, maxTempStr, minTempStr) 		
			else:
				queryString ='''select * from %s where %f > (%s + %s) / 2 AND isKlister == %d order by (%s + %s) / 2.0 DESC''' % (brand, self.bestAveTemp, maxTempStr, minTempStr, isKlisterVal, maxTempStr, minTempStr) 		
	
			#debugprint queryString			
			self.waxdbcur.execute( queryString )
			result = self.waxdbcur.fetchone()
			if result is not None:
				temperaturediff = abs(( result[maxTempIdx] + result[minTempIdx] ) / 2.0 - self.bestAveTemp)
				if bestResult is None or temperaturediff < bestdiff: 		
					bestResult = result				
					bestdiff = temperaturediff
					bestBrand = brand
		 if bestResult is None:
		 	if direction == "Warmer":
		 		self.bestAveTemp = 9999
		 	else:
		 		self.bestAveTemp = -9999
		 else:
		 	self.bestAveTemp = (bestResult[maxTempIdx] + bestResult[minTempIdx]) / 2
		 self.displayWax( brand = bestBrand, bestResult=bestResult, minTempIdx = minTempIdx, maxTempIdx = maxTempIdx )
		 
	def find_wax( self, *args, **kargs ):
		 currTemp = self.widgets['temperatureSlider'].value		 
		 if not self.usingCelsius :
		 	currTemp = (5.0/9.0) * (currTemp - 32.0)
		 isKlisterVal = 0		 
		 if self.snow_cond == CORN_SNOW or self.snow_cond == ICY_SNOW:
		 	isKlisterVal = 1
		 
		 minTempStr = 'newMinTemp'
		 maxTempStr = 'newMaxTemp'
		 minTempIdx = 3
		 maxTempIdx = 4
		 if( self.snow_cond == 1 ):
		 	 minTempStr = 'transMinTemp'
			 maxTempStr = 'transMaxTemp'
			 minTempIdx = 5
			 maxTempIdx = 6
		 bestResult = None
		 bestdiff = 9999
		 bestBrand = None
		 for brand in self.brands:
		 	if self.enabledBrands[brand] != 'True':
		 		#debugprint "Brand" + brand + "disabled"
		 		continue
		 	queryString ='''select * from %s where %f >= %s AND %f <= %s AND isKlister == %d order by abs( %f - (%s + %s) / 2 )''' % (brand, currTemp, minTempStr, currTemp, maxTempStr, isKlisterVal, currTemp, maxTempStr, minTempStr) 		
			#debugprint queryString			
			self.waxdbcur.execute( queryString )
			result = self.waxdbcur.fetchone()
			if result is not None:
				temperaturediff = abs( currTemp - ( result[maxTempIdx] - result[minTempIdx] ))
				if bestResult is None or temperaturediff < bestdiff: 		
					bestResult = result
					bestBrand = brand				
 					bestdiff = temperaturediff
		 			self.bestAveTemp = (bestResult[maxTempIdx] + bestResult[minTempIdx]) / 2
		 
		 if self.humidity == HIGH_HUMIDITY:
		 	self.changeWax( direction='Warmer')
		 else:
		 	self.displayWax( brand = bestBrand, bestResult=bestResult, minTempIdx = minTempIdx, maxTempIdx = maxTempIdx )
		 
	def enableBrands(self, obj, *args, **kargs):
		 brand = kargs.get('brand')
		 self.enabledBrands[brand] = str(obj.state_get())
	def setUnits(self, obj, *args, **kargs):
		 self.usingCelsius = obj.state_get()
		 if self.usingCelsius:
			self.widgets['temperatureSlider'].min_max_set (-30.0, 10.0)
			self.widgets['temperatureSlider'].value = 0
	  	 else:
			self.widgets['temperatureSlider'].min_max_set (-15.0, 45.0)
			self.widgets['temperatureSlider'].value = 32
	def setSensor(self, obj, *args, **kargs):
		 self.usingSensor = obj.state_get()
		 if( self.usingSensor ):
			self.widgets['sensorButton'].show ()
		 else:
			self.widgets['sensorButton'].hide ()
	def getSensorTemperatureString(self, obj, *args, **kargs):
		 temperature = self.getSensorTemperature(self)
		 unit = "C"
		 if not self.usingCelsius:
		 	temperature = self.CtoF(temperature)
			unit = "F"	 
		 labelString = str( temperature ) + unit
		 return labelString
		 
	def setTemperatureFromSensor(self, obj, *args, **kargs):
		 
		 if self.usingCelsius:
		 	self.widgets['temperatureSlider'].value = self.getSensorTemperature(self) 
		 else:
		 	self.widgets['temperatureSlider'].value = self.CtoF( self.getSensorTemperature(self) )
	def getSensorTemperature(self, obj, *args, **kargs):
		 tempfile = open( '/sys/bus/i2c/devices/0-005a/object1','r' )
		 tempx100 = int(tempfile.read())
		 tempfile.close()
		 return tempx100 / 100.0
	def colderWax (self, *args, **kargs):
		 self.changeWax( direction='Colder')
	def warmerWax (self, *args, **kargs):
		 self.changeWax( direction='Warmer')
	def setHumidity( self, *args, **kargs ):
		 self.humidity = kargs.get('humidity')
	def setSnowCond( self, *args, **kargs ):
		 self.snow_cond = kargs.get('snowcond')
	def infoadd(self, text):                               
		 return elementary.Entry.utf8_to_markup(text)+'<br>'
	def displayWax( self, *args, **kargs ): 
		bestResult = kargs['bestResult']
		minTempIdx = kargs['minTempIdx']
		maxTempIdx = kargs['maxTempIdx']
		brand = kargs['brand']
		if bestResult is not None:
			isKlisterVal = 0		 
		 	if self.snow_cond == 2 or self.snow_cond == 3:
		 		isKlisterVal = 1
			self.widgets['waxicon'].file_set(os.path.join(IMAGE_DIR, bestResult[2]))
			self.widgets['waxLabel'].text_set(bestResult[0])
			info = self.infoadd(brand +" "+ bestResult[0])
			temperature = []
			temperature.append(bestResult[3])
			temperature.append(bestResult[4])
			temperature.append(bestResult[5])
			temperature.append(bestResult[6])
			UnitChar = 'C'
			if not self.usingCelsius:
				temperature = self.CtoFarray( temperature )
				UnitChar = 'F'
			if isKlisterVal != 1:
				info += self.infoadd("New snow Range: "+str(temperature[0])+UnitChar+" - "+str(temperature[1])+UnitChar)
				info += self.infoadd("Old snow Range: "+str(temperature[2])+UnitChar+" - "+str(temperature[3])+UnitChar)
			else:
				info += self.infoadd("Temperature Range: "+str(temperature[0])+UnitChar+" - "+str(temperature[1])+UnitChar)
			self.widgets['waxtext'].text_set( info )		 
		else:
			self.widgets['waxicon'].file_set(os.path.join(IMAGE_DIR, "waxless.png"))
			self.widgets['waxLabel'].text_set("No Match found")
			info = self.infoadd("try:")
			info += self.infoadd("Including more brands")
			info += self.infoadd("Buying more wax" )
			info += self.infoadd("Skiing Waxless" )
			info += self.infoadd("Staying indoors" )
			self.widgets['waxtext'].text_set( info )		
			 	
		self.widgets['mainbox'].hide ()
		self.widgets['waxbox'].show ()		
	def settingsDialog (self, *args, **kargs):
		self.widgets['mainbox'].hide ()
		self.widgets['settingsbox'].show ()
	def showAbout(self, *args, **kargs):
		self.widgets['aboutbox'].show()
		self.widgets['settingsbox'].hide ()
	def hideAbout(self, *args, **kargs):
		self.widgets['aboutbox'].hide()
		self.widgets['settingsbox'].show()	
	def closeSettings (self, *args, **kargs):
		self.widgets['settingsbox'].hide ()
		self.widgets['mainbox'].show ()
	def closeWax (self, *args, **kargs):
		self.widgets['waxbox'].hide ()
		self.widgets['mainbox'].show ()
	def updateSensorLabel(self, *args, **kargs):
		if self.usingSensor:
			self.widgets['sensorButton'].text_set( "Use Sensor Reading: " + self.getSensorTemperatureString(self) )	
		return True
	def LoadConfig (self, cfpath):
		"""
		Load configuration file, create a default if it doesn't exist.
		"""
		self.config.read (cfpath)
		if not self.config.has_section ('Main'):
			self.config.add_section ('Main')
		if not self.config.has_option( 'Main', 'units' ):
			self.config.set ('Main', 'units', 'celsius')
		if not self.config.has_option( 'Main', 'Sensor' ):
			self.config.set ('Main', 'Sensor', 'no')
		#debugprint self.config.get ('Main', 'units', 0)
		self.usingCelsius = self.config.get ('Main', 'units', 0) == 'celsius'
		self.usingSensor = self.config.get ('Main', 'Sensor', 0) == 'yes'
		if not self.config.has_section ('Brands'):
			for brand in self.brands:
				self.enabledBrands[brand] = 'True'
				#debugprint "creating default bands"
		else:
			for brand in self.brands:
				if self.config.has_option( 'Brands', brand ):
					self.enabledBrands[brand] = self.config.get( 'Brands', brand, 0 )
					#debugprint "read value:" + str( self.enabledBrands[brand] )		
				else:
					self.enabledBrands[brand] = 'True'
		self.SaveConfig (cfpath)
	def LoadDB ( self ):
		self.waxdbconn=sqlite3.connect(os.path.join(DATA_DIR, 'waxdb.db'))
		self.waxdbconn.text_factory = sqlite3.OptimizedUnicode
		self.waxdbcur=self.waxdbconn.cursor()
		
		# get the list of brands for populating gui
		self.waxdbcur.execute( '''SELECT name FROM sqlite_master WHERE type='table' ORDER BY name''' )
		brandtups = self.waxdbcur.fetchall()
		self.brands = [tup[0] for tup in brandtups]
		
	def SaveConfig (self, cfpath):
		'''
		Save config file.
		'''
		if self.usingCelsius:
			self.config.set ('Main', 'units', 'celsius')
		else:
			self.config.set ('Main', 'units', 'fahreinheit')
		if self.usingSensor:
			self.config.set ('Main', 'Sensor', 'yes')
		else:
			self.config.set ('Main', 'Sensor', 'no')
		if not self.config.has_section ('Brands'):
			self.config.add_section ('Brands')
		for brand in self.brands:
			self.config.set('Brands', brand, self.enabledBrands[brand])
		with open(cfpath, 'wb') as configfile:
			self.config.write (configfile)
			configfile.close ()

	def SearchFile (self, filename, fallback=None):
		'''
		Given a search path, find file
		'''
		file_found = 0
		paths = self.image_path.split (os.pathsep)
		for path in paths:
			if os.path.exists (os.path.join (path, filename)):
				file_found = 1
				break
		if file_found:
			return os.path.abspath (os.path.join (path, filename))
		elif fallback:
			return self.SearchFile (fallback)
		return None

	def LoadHistory (self):
		'''
		Get the saved history (from the config file) for the current
		location and load it into the fdata list.
		'''
		viewnum = self.config.getint('Main', 'lastview')
		brand = self.brands[viewnum]
		self.fdata = []
		if not self.config.has_section (location):
			return
		daycount = self.config.getint (location, 'entry_count')
		for i in range (0, daycount):
			date = self.config.get (location, 'date' + str (i))
			high = self.config.get (location, 'high' + str (i))
			low = self.config.get (location, 'low' + str (i))
			icon = self.config.get (location, 'icon' + str (i))
			self.fdata.append ({'date': date, 'high': high, 'low': low, 'icon': icon})
	def CtoFarray (self, temperatures):
		rettemperatures=[]
		for temperature in temperatures:
		    rettemperatures.append(self.CtoF(temperature))
		return rettemperatures
	def CtoF (self, temperature):
		return (temperature * (9.0/5.0)) + 32.0
                               
 
if __name__ == "__main__":  
	app = waxGUI()                                       
	sys.exit(main(app)) 
