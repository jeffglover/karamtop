#!/usr/bin/python

#####################
##                 ##
##  KaramTop       ##
##                 ##
#####################
# Will only run when called from SuperKaramba

import karamba
import ConfigParser
import os
import sys
import zipfile
import time
import pytop #Import of the pytop.py class. Must be located in current directory

def initWidget(widget):
    global Instances, titletext, themePath, theme_dir

    #Using a unique ID for multiple instances of karamTop
    id = karamba.readConfigEntry(widget, "id")
    if id == None:
    	id = str( int( time.time() * 100 ) )
	karamba.writeConfigEntry(widget, "id", id)

    # Figure out what theme to use. flatgray is the default
    theme = karamba.readConfigEntry(widget, "karamtop theme")
    if theme == None or theme == "":
	    theme = "flatgray"

    theme_dir = "themes/"
    themePath = karamba.getThemePath(widget)
    ### Thanks to liquid weather for dealing with the skz format
    home_directory = os.popen("echo $HOME").readline()[0:-1]
    if themePath[-3:] == "skz":
	skz_file = zipfile.ZipFile(themePath, 'r')
	theme_file = skz_file.read(theme_dir + theme + "/" + theme + ".cfg")
	try:
		os.mknod(home_directory + '/.superkaramba/ktop_theme_conf')
	except(OSError):
		pass

	ktop_file = open(home_directory + '/.superkaramba/ktop_theme_conf','w')
	ktop_file.write(theme_file)
	ktop_file.close()
	theme_cfg_file = (home_directory + '/.superkaramba/ktop_theme_conf')
	skz_file.close()
    else:
    	theme_cfg_file = ( themePath + theme_dir + theme + "/" + theme + ".cfg" )

    theme_cfg = ConfigParser.ConfigParser()
    theme_cfg.readfp( open( theme_cfg_file ) )

    toptext = karamba.getThemeText(widget, "toptext")
    ##########################################################
    #### Initialize the Top class ####
    try:
	Instances[id] = None
    	Instances[id] = ( pytop.Top( widget, toptext ) )
    except NameError, (strerror):
	Instances = {}
	Instances[id] = ( pytop.Top( widget, toptext ) )
    ##########################################################

    readConfigTop(widget, theme_cfg)

    createConfigMenus(widget)

    #### Begin reading [background images] and [images] from the config file ####
    readConfigImages(widget, theme_cfg)
    ##########################################################

    #### Begin reading optional settings for titletext ####
    readConfigTitleText(widget, theme_cfg)
    ##########################################################

    #### Begin reading optional settings for toptext ####
    readConfigTopText(widget, theme_cfg)
    ##########################################################

    #### Begin reading optional settings from [formatting] ####
    readConfigFormatting(widget, theme_cfg)
    ##########################################################

    #### Begin reading optional settings from [cpuFormat] ####
    # if one option is missing. Then use defaults
    readConfigCPUFormat(widget, theme_cfg)
    ##########################################################

    #### Begin reading optional settings from [memFormat] ####
    # if one option is missing. Then use defaults
    readConfigMemFormat(widget, theme_cfg)
    ##########################################################

    readConfigThreading(widget)

    print "init: KaramTop: Developed by Moloch - [ http://www.kde-look.org/content/show.php?content=13140 ]"
    #TopRun.start() # Start the thread

def widgetUpdated(widget):
     global Instances

     id = karamba.readConfigEntry(widget, "id")
     Instances[id].start()
     karamba.redrawWidget(widget)


def menuOptionChanged(widget, key, value):
	global themePath, theme_dir, chtheme_pid, procoutformat_pid, align_pid

	chtheme_pid = None
	procoutformat_pid = None
	align_pid = None

	chtheme_cmd = ['kdialog', '--title', 'Choose theme', '--radiolist', 'Choose theme']
	align_cmd = ['kdialog', '--title', 'Set Alignment', '--radiolist', 'Set the alignment for the command text.', 'left', 'Left', 'off', 'right', 'Right', 'off', 'default','Reset to theme default', 'on']
# 	padding_cmd = ['kdialog', '--title', 'Set Padding', '--inputbox', 'Set maximum length for the command text. Enter an integer number. The default value for flatgray is 13', '13']
	procoutformat_cmd = ['kdialog', '--title', 'Set Output format', '--inputbox', 'Set the column order for the output. Syntax is important here. Must include all columns.\n\nType \"default\" to reset to the default.\n\nDefault value is: %(cpu_percent)s %(command)s %(memory)s\n\nExamples: %(memory)s %(command)s %(cpu_percent)s\n%(command)s %(cpu_percent)s %(memory)s', '%(cpu_percent)s %(command)s %(memory)s']


	if key == "theme":
		listing = []
		if themePath[-3:] == "skz":
			skz_file = zipfile.ZipFile(themePath, 'r')
			ziplisting = skz_file.namelist()
			skz_file.close()
			for member in ziplisting:
				if member.find(theme_dir) > -1:
					path = member.split("/")
					if len(path) == 3 and path[2] == "":
						listing.append( path[1] )
		else:
			listing = os.listdir(themePath + theme_dir) # list the files in themes/

		for theme in listing:
			# kdialog wants 3 parameters per item.
			# tag is what the value is and item is what is display
			# not sure about status. so just putting anything there
			chtheme_cmd.append(theme) # one for tag
			chtheme_cmd.append(theme) # one for item
			chtheme_cmd.append("on") # one for status

		karamba.setMenuConfigOption(widget, "theme", 0)
		chtheme_pid = karamba.executeInteractive(widget, chtheme_cmd)

	elif key == "setProcOutformat":
		karamba.setMenuConfigOption(widget, "setProcOutformat", 0)
		procoutformat_pid = karamba.executeInteractive(widget, procoutformat_cmd)

	elif key == "showZero":
		if value == 1:
			print "Changing to config to show zeros."
			karamba.writeConfigEntry(widget, "showZero", "true")
		else:
			print "Changing to config to hide zeros."
			karamba.writeConfigEntry(widget, "showZero", "false")

		karamba.reloadTheme(widget)

	elif key == "setCmdJustification":
		karamba.setMenuConfigOption(widget, "setCmdJustification", 0)
		align_pid = karamba.executeInteractive(widget, align_cmd)

	elif key == "disableThreading":
		if value == 1:
			print "Disable threading."
			karamba.writeConfigEntry(widget, "disableThreading", "true")
		else:
			print "Enable threading."
			karamba.writeConfigEntry(widget, "disableThreading", "false")

		karamba.reloadTheme(widget)


def commandOutput(widget, pid, output):
	global chtheme_pid, procoutformat_pid, align_pid
	value = output.strip()

	if pid == chtheme_pid:
		if value != "":
			print "Changing theme to " + value
			karamba.writeConfigEntry(widget, "karamtop theme", value)
			karamba.reloadTheme(widget)

	elif pid == procoutformat_pid:
		if value != "":
			if value[:1] == "%":
				print "Changing procoutformat to " + value
				karamba.writeConfigEntry(widget, "setProcOutformat", value)
			else:
				print "Changing procoutformat to default"
				karamba.writeConfigEntry(widget, "setProcOutformat", "")

			karamba.reloadTheme(widget)

	elif pid == align_pid:
		if value != "":
			if value == "default":
				print "Changing setCmdJustification to default"
				karamba.writeConfigEntry(widget, "setCmdJustification", "")
			else:
				print "Changing setCmdJustification to " + value
				karamba.writeConfigEntry(widget, "setCmdJustification", value)

			karamba.reloadTheme(widget)

def createConfigMenus(widget):
    karamba.addMenuConfigOption(widget, "theme", "Choose theme")
    karamba.setMenuConfigOption(widget, "theme", 0)

    karamba.addMenuConfigOption(widget, "showZero", "Show processes where the CPU usage is 0")

    karamba.addMenuConfigOption(widget, "setCmdJustification", "Set the alignment for the command text")
    karamba.setMenuConfigOption(widget, "setCmdJustification", 0)

    karamba.addMenuConfigOption(widget, "setProcOutformat", "Set the column order for the output")
    karamba.setMenuConfigOption(widget, "setProcOutformat", 0)

    karamba.addMenuConfigOption(widget, "disableThreading", "Disable Threading")


#     karamba.addMenuConfigOption(widget, "CmdPadding", "Set maximum length for the command text")
#     karamba.setMenuConfigOption(widget, "CmdPadding", 0)

#     karamba.addMenuConfigOption(widget, "titletext_value", "Change title display text")
#     karamba.setMenuConfigOption(widget, "titletext_value", 0)
#     karamba.addMenuConfigOption(widget, "titletext_color", "Change title text color")
#     karamba.setMenuConfigOption(widget, "titletext_color", 0)
#     karamba.addMenuConfigOption(widget, "titletext_shadow", "Change title text shadow")
#     karamba.setMenuConfigOption(widget, "titletext_shadow", 0)
#     karamba.addMenuConfigOption(widget, "titletext_size", "Change title text size")
#     karamba.setMenuConfigOption(widget, "titletext_size", 0)
#     karamba.addMenuConfigOption(widget, "titletext_font", "Change title text font")
#     karamba.setMenuConfigOption(widget, "titletext_font", 0)
#
#     karamba.addMenuConfigOption(widget, "toptext_color", "Change process listing color")
#     karamba.setMenuConfigOption(widget, "toptext_color", 0)
#     karamba.addMenuConfigOption(widget, "toptext_shadow", "Change process listing shadow")
#     karamba.setMenuConfigOption(widget, "toptext_shadow", 0)
#     karamba.addMenuConfigOption(widget, "toptext_size", "Change process listing font size")
#     karamba.setMenuConfigOption(widget, "toptext_size", 0)
#     karamba.addMenuConfigOption(widget, "toptext_font", "Change process listing font")
#     karamba.setMenuConfigOption(widget, "toptext_font", 0)

def readConfigTop(widget, theme_cfg):
	global theme_dir, Instances
	id = karamba.readConfigEntry(widget, "id")

	#### Begin reading the [top] section of the config file ####
	num_procs = karamba.readConfigEntry(widget, "num_procs")
	if num_procs == None or int(num_procs) < 1:
		try:
			num_procs = theme_cfg.getint( "top", "num_procs" )
			Instances[id].setNumProcs(num_procs)
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Using default."

	# The size of the widget. Required.
	try:
		w, h = theme_cfg.get( "karamba", "themesize" ).split(",", 1 )
		karamba.resizeWidget( widget, int(w), int(h) )
	except ConfigParser.NoOptionError, (strerror):
		displayError('Theme Size', 'Missing parameters for the width and height of the theme.')
		raise


def readConfigImages(widget, theme_cfg):
	#### Begin reading [background images] and [images] from the config file ####
	for image in theme_cfg.options("background images"):
		x, y, file = theme_cfg.get( "background images", image ).split(",", 2)
		karamba.createBackgroundImage(widget, int(x), int(y), file.strip())

	for image in theme_cfg.options("images"):
		x, y, file = theme_cfg.get( "images", image ).split(",", 2)
		karamba.createImage(widget, int(x), int(y), file.strip())

def readConfigTitleText(widget, theme_cfg):
	titletext = karamba.getThemeText(widget, "titletext")
	#### Read the titletext x and y position from the config file ####
	# required option
	try:
		x, y = theme_cfg.get( "karamba", "titletext_pos" ).split(",", 1 )
		karamba.moveText(widget, titletext, int(x), int(y))
	except ConfigParser.NoOptionError, (strerror):
		displayError('Title Text', 'Missing parameters for the position of the title text.')
		raise

	#### Begin reading optional settings for titletext ####
	titletext_value = karamba.readConfigEntry(widget, "titletext_value")
	if titletext_value == None:
		try:
			titletext_value = theme_cfg.get( "karamba", "titletext_value" )
			karamba.changeText(widget, titletext, titletext_value.strip())
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Using default."
	else:
		karamba.changeText(widget, titletext, titletext_value.strip())

	titletext_color = karamba.readConfigEntry(widget, "titletext_color")
	if titletext_color == None or titletext_color == "":
		try:
			r, g, b = theme_cfg.get( "karamba", "titletext_color" ).split(",", 2)
			karamba.changeTextColor(widget, titletext, int(r), int(g), int(b))
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Using default."
	else:
		r, g, b = titletext_color.split(",", 2)
		karamba.changeTextColor(widget, titletext, int(r), int(g), int(b))

	titletext_shadow = karamba.readConfigEntry(widget, "titletext_shadow")
	if titletext_shadow == None or str(titletext_shadow) == "":
		try:
			titletext_shadow = theme_cfg.getint( "karamba", "titletext_shadow" )
			karamba.changeTextShadow(widget, titletext, int(titletext_shadow))
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Using default."
	else:
		karamba.changeTextShadow(widget, titletext, int(titletext_shadow))

	titletext_size = karamba.readConfigEntry(widget, "titletext_size")
	if titletext_size == None or int(titletext_size) < 1:
		try:
			titletext_size = theme_cfg.getint( "karamba", "titletext_size" )
			karamba.changeTextSize(widget, titletext, int(titletext_size))
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Using default."
	else:
		karamba.changeTextSize(widget, titletext, int(titletext_size))

	titletext_font = karamba.readConfigEntry(widget, "titletext_font")
	if titletext_font == None or str(titletext_font) == "":
		try:
			titletext_font = theme_cfg.get( "karamba", "titletext_font" )
			karamba.changeTextFont(widget, titletext, titletext_font.strip())
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Using default."
	else:
		karamba.changeTextFont(widget, titletext, titletext_font.strip())

def readConfigTopText(widget, theme_cfg):
	toptext = karamba.getThemeText(widget, "toptext")

	#### Read the toptext x and y position from the config file ####
	# required option
	try:
		x, y = theme_cfg.get( "karamba", "toptext_pos" ).split(",", 1 )
		karamba.moveText(widget, toptext, int(x), int(y))
	except ConfigParser.NoOptionError, (strerror):
		displayError('Top Text', 'Missing parameters for the position of the process listing text.')
		raise

	#### Begin reading optional settings for toptext ####
	toptext_color = karamba.readConfigEntry(widget, "toptext_color")
	if toptext_color == None or toptext_color == "":
		try:
			r, g, b = theme_cfg.get( "karamba", "toptext_color" ).split(",", 2 )
			karamba.changeTextColor(widget, toptext, int(r), int(g), int(b))
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Skipping option."
	else:
		r, g, b = toptext_color.split(",", 2)
		karamba.changeTextColor(widget, toptext, int(r), int(g), int(b))

	toptext_shadow = karamba.readConfigEntry(widget, "toptext_shadow")
	if toptext_shadow == None or str(toptext_shadow) == "":
		try:
			toptext_shadow = theme_cfg.get( "karamba", "toptext_shadow" )
			karamba.changeTextShadow(widget, toptext, int(toptext_shadow))
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Skipping option."
	else:
		karamba.changeTextShadow(widget, toptext, int(toptext_shadow))

	toptext_size = karamba.readConfigEntry(widget, "toptext_size")
	if toptext_size == None or int(toptext_size) < 1:
		try:
			toptext_size = theme_cfg.getint( "karamba", "toptext_size" )
			karamba.changeTextSize(widget, toptext, int(toptext_size))
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Skipping option."
	else:
		karamba.changeTextSize(widget, toptext, int(toptext_size))

	toptext_font = karamba.readConfigEntry(widget, "toptext_font")
	if toptext_font == None or str(toptext_font) == "":
		try:
			toptext_font = theme_cfg.get( "karamba", "toptext_font" )
			karamba.changeTextFont(widget, toptext, toptext_font.strip())
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Skipping option."
	else:
		karamba.changeTextFont(widget, toptext, toptext_font.strip())

def readConfigFormatting(widget, theme_cfg):
	global Instances
	id = karamba.readConfigEntry(widget, "id")
	toptext = karamba.getThemeText(widget, "toptext")
	#### Begin reading optional settings from [formatting] ####

	alignment = karamba.readConfigEntry(widget, "setCmdJustification")
	if alignment == None or alignment.strip() == "":
		try:
			alignment = theme_cfg.get( "formatting", "setCmdJustification" )
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Setting option to left."
			alignment = "left"

	cmd_padding = karamba.readConfigEntry(widget, "setCmdPadding")
	if cmd_padding == None or int(cmd_padding) < 0:
		try:
			cmd_padding = theme_cfg.getint( "formatting", "setCmdPadding" )
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Setting option to 13."
			cmd_padding = 13

	Instances[id].setCmdJustification(alignment, cmd_padding)

	ProcOutformat = karamba.readConfigEntry(widget, "setProcOutformat")
	if ProcOutformat == None or ProcOutformat.strip() == "":
		try:
			ProcOutformat = theme_cfg.get( "formatting", "setProcOutformat", True )
			Instances[id].setProcOutformat( ProcOutformat.strip() + "\n" )
		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Skipping option."
	else:
		Instances[id].setProcOutformat( ProcOutformat.strip() + "\n" )

def readConfigCPUFormat(widget, theme_cfg):
	global Instances
	id = karamba.readConfigEntry(widget, "id")
	toptext = karamba.getThemeText(widget, "toptext")
	#### Begin reading optional settings from [cpuFormat] ####
	# if one option is missing. Then use defaults
#  	cpu_padding = karamba.readConfigEntry(widget, "cpu_padding")
#  	cpu_decimal_1 = karamba.readConfigEntry(widget, "cpu_decimal_1")
# 	cpu_decimal_0 = karamba.readConfigEntry(widget, "cpu_decimal_0")
# 	hide_0 = karamba.readConfigEntry(widget, "hide_0")
# 	cpu_rem_0 = karamba.readConfigEntry(widget, "cpu_rem_0")
#
# 	if cpu_decimal_1:
# 		cpu_more_one = "%0.1f"
# 	if cpu_decimal_0:
# 		cpu_less_one = "%0.1f"

	showZero = karamba.readConfigEntry(widget, "showZero")
	if showZero == None:
		karamba.setMenuConfigOption(widget, "showZero", 0)
		karamba.writeConfigEntry(widget, "showZero", "false")
		try:
			hide_0 = theme_cfg.getboolean( "cpuFormat" , "hide_0" )
			if hide_0:
				Instances[id].cpuHideZero()

		except ConfigParser.NoOptionError, (strerror):
			print "Warning: " + str(strerror) + ". Skipping option."
	else:
		if showZero.strip() == "false":
			Instances[id].cpuHideZero()


	try:
		cpu_padding = theme_cfg.getint( "cpuFormat" , "padding" )
		cpu_decimal_1 = theme_cfg.getboolean( "cpuFormat" , "decimal_1" )
		cpu_decimal_0 = theme_cfg.getboolean( "cpuFormat" , "decimal_0" )
		cpu_rem_0 = theme_cfg.getboolean( "cpuFormat" , "remove_0" )
		cpu_more_one = theme_cfg.get( "cpuFormat" , "greater_than_one", True )
		cpu_less_one = theme_cfg.get( "cpuFormat" , "less_than_one", True )
		Instances[id].cpuFormat( cpu_padding, cpu_decimal_1, cpu_decimal_0, cpu_rem_0, cpu_more_one, cpu_less_one )
	except ConfigParser.NoOptionError, (strerror):
		print "Warning: " + str(strerror) + ". Skipping whole section."

def readConfigMemFormat(widget, theme_cfg):
	global Instances
	id = karamba.readConfigEntry(widget, "id")
	toptext = karamba.getThemeText(widget, "toptext")
	#### Begin reading optional settings from [memFormat] ####
	# if one option is missing. Then use defaults
	try:
		mem_padding = theme_cfg.get( "memFormat" , "padding" ).strip()
		kilobytes = theme_cfg.get( "cpuFormat" , "kilobytes", True )
		megabytes = theme_cfg.get( "cpuFormat" , "megabytes", True )
		gigabytes = theme_cfg.get( "cpuFormat" , "gigabytes", True )
		Instances[id].memFormat( mem_padding, kilobytes, megabytes, gigabytes)
	except ConfigParser.NoOptionError, (strerror):
		print "Warning: " + str(strerror) + ". Skipping whole section."

def readConfigThreading(widget):
	global Instances
	id = karamba.readConfigEntry(widget, "id")
	disableThreading = karamba.readConfigEntry(widget, "disableThreading")
	if disableThreading == None or disableThreading == "true":
		karamba.setMenuConfigOption(widget, "disableThreading", 1)
		karamba.writeConfigEntry(widget, "disableThreading", "true")
		disableThreading = True
	else:
		disableThreading = False

	Instances[id].setDisableThreading(disableThreading)

def displayError(title, message):
	print message
	os.execvp('kdialog', ['--title ' + str( title ), '--error', str( message )] )

def widgetClicked(widget, x, y, button):
    pass

def widgetMouseMoved(widget, x, y, button):
    #Warning:  Don't do anything too intensive here
    #You don't want to run some complex piece of code everytime the mouse moves
    pass