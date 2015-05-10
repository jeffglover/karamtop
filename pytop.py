#!/usr/bin/env python2
#
# pyTop - Emulates the functionality of top. Desgined for scripting
# Copyright (C) Jeff Glover
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# http://www.gnu.org/licenses/gpl.txt

# Keep in mind this is not every field of /proc. Just stuff I find useful.

import os
import time
import thread
import operator
# Check for superkaramba
try:
	import karamba
	useKaramba = True
except:
	useKaramba = False

class Top:
	def __init__ (self, widget=None, toptext=None):
		print "init: pytop.Top"
		self.widget = widget
		self.num_procs = 5
		self.toptext = toptext
		self.disableThreading = True;
		self.procfs = "/proc"
		self.mainstat = self.procfs + "/stat"
		self.procStatfs = self.procfs + "/%s/stat" # %s reserved for procid in loop
		self.procStatusfs = self.procfs + "/%s/status"
		self.utimepos = 13 # position in _procStatfs of utime (starting at 0)
		self.stimepos = 14 # position in _procStatfs of stime (starting at 0)
		self.rssKey = 'VmRSS:' # Where to find real memory usage in _procStatusfs

		self.cpu_total_old = 1
		self.cpu_load_old = 1
		self.cpu_total_new = 1
		self.cpu_load_new = 1
		self.totaltime = 0
		self.pcpu = 0 # total cpu percentage

		self.rss_mb = 1024.0 # What to divide the rss size by (to get MB)
		self.rss_gb = self.rss_mb * self.rss_mb

		# should be set the same or output could look funny
		self.cmd_ljust = 0 # Spacing to make cmd text left justfied, 0 for none
		self.cmd_rjust = 0 # Spacing to make cmd text right justfied, 0 for none
		self.cmd_cutoff = 255 # Where to cut off cmd text

		self.sort_cpu = 0
		self.sort_rss = 1 #not yet implemented
		self.sort_cmd = 2 #not yet implemented
		self.sort_none = 3

		self.updateOutStr = True

		# A very short delay after reading each /proc file in a loop here greatly reduces
		# cpu usage. Down to the level that top uses. It seems to be just as accurate.
		# At least according to top. Under load accuracy is lost as these sleeps allows
		# other processes to work in between
		self.granularity = 0.0001

		self.proclist = [] # nested list that holds proc values
		self.lasttime = {} # dictionary that stores the last time value of each process
		self.sort = self.sort_cpu
		self.procOutStr = ""
		self.procthread = None
		self.procOutformat = "%(cpu_percent)s %(command)s %(memory)s\n"
		self.cpu_padding = 5
		self.cpu_less_one = "%.1f%%"
		self.cpu_more_one = "%.1f%%"
		self.cpu_decimal_1 = True
		self.cpu_decimal_0 = True
		self.cpu_rem_0 = False
		self.hide_0 = False
		self.mem_padding = 6
		self.memK = "%.0fK"
		self.memM = "%.1fM"
		self.memG = "%.1fG"

		try:
			test = operator.itemgetter(0)
			self.has24 = True
			print "pyTop: has Python 2.4"
			test = None
		except:
			self.has24 = False
			print "pyTop: does not have Python 2.4"

		self.threadrun = False

	def run(self):
		self.totalCPU()
		self.procStats()

		time.sleep(self.granularity)

		if self.updateOutStr:
			self.procPrintToString()
			if useKaramba:
				try:
					karamba.changeText(self.widget, self.toptext, self.getprocOutStr())
				except ValueError:
					print "pyTop: ValueError: lost karamba object"

	def start(self):
		if not self.disableThreading:
			thread.start_new_thread ( self.run, ( ) )
			print "threading..."
		else:
			print "not threading..."
			self.run()

	def totalCPU(self): # find the total cpu usage
		statarry = open(self.mainstat,'r').readline().split()
		# total cputime including idle
		self.cpu_total_new = float(statarry[1]) + float(statarry[2]) + float(statarry[3]) + float(statarry[4])

		# total cpu load (not including idle)
		self.cpu_load_new = float(statarry[1]) + float(statarry[2]) + float(statarry[3])

		# compute cpu percentage
		#try:
			#self.pcpu = (self.cpu_load_new - self.cpu_load_old) / (self.cpu_total_new - self.cpu_total_old) * 100.0
		#except ZeroDivisionError:
			#self.pcpu = 0.0

		# do some stuff to prepare for the next iteration
		self.totaltime = self.cpu_total_new - self.cpu_total_old
		self.cpu_total_old = self.cpu_total_new
		self.cpu_load_old = self.cpu_load_new

	def procStats(self): # /proc information for each process
		self.proclist = [] # clear the proc list
		procdirs = os.listdir(self.procfs) # list the dirs in /proc
		for procdir in procdirs:
			if procdir.isdigit(): # make sure it is a process and not something else
				try:
					procStatarray = open(self.procStatfs % procdir,'r').readline().split()
					procStatus = open(self.procStatusfs % procdir, 'r').read()

					time.sleep(self.granularity) # A very short delay here greatly reduces cpu usage. Down to the level of top. It seems to be just as accurate. At least according to top. Except during heavy IO.
				except IOError:
					continue

				i = procStatus.find(self.rssKey) # look for the RSS location
				procStatus = procStatus[i:].split(None, 3)  # whitespace
				if len(procStatus) < 3:
					# if something is fucked just set it to 0
					rssmem = 0  # invalid format?
				else:
					# 9999 KB, we are just extracting the number
					rssmem = int(round(float(procStatus[1])))

				# add up user time and system time
				ptime = float( procStatarray[self.utimepos] ) + float( procStatarray[self.stimepos] )

				# add in the executable name, strip out the ( ) around it
				command = procStatarray[1].strip("()")

				try:
					# computes the cpu percentage of the process
					# if it is the first run or the process has
					# died since the last run, it will fail
					try:
						pcpu = ( ptime - self.lasttime[int(procdir)] ) / self.totaltime * 100.0
					except ZeroDivisionError:
						pcpu = 0.0

					if pcpu < 1:
						if self.cpu_decimal_0: pcpu = round( pcpu, 1 )
						else: pcpu = int( round( pcpu, 0 ) )
					else:
						if self.cpu_decimal_1: pcpu = round( pcpu, 1 )
						else: pcpu = int( round( pcpu, 0 ) )

				except KeyError:
					# if it fails, just set it to 0
					pcpu = 0.0

				self.lasttime[int(procdir)] = ptime

				self.proclist.append( ( int(procdir), pcpu, command, rssmem ) )

	def procPrintToString(self):
		# takes arguments sort_*, and the number of processes to display
		#
		# for printing, but if you are writing your own interface
		# then you can use the sortby function and deal with the data
		# how you please

		out_string = ""
		count = 1
		self.sortBy(self.sort)

		# Take list of keys and print by the order

		for procdir, pcpu, command, rssmem in self.proclist:
			# break if pcpu is 0. Since it is sorted by cpu, once it reaches 0
			# none of the others matter as they will be 0, but only do this
			# if we are sorting by cpu
			if (pcpu == 0.0) and (self.hide_0):
				break

			if self.cmd_ljust > 0:
				command = command[:self.cmd_cutoff].ljust(self.cmd_ljust)
			elif self.cmd_rjust > 0:
				command = command[:self.cmd_cutoff].rjust(self.cmd_rjust)
			else:
				command = command[:self.cmd_cutoff]

			# CPU%
			if pcpu < 1 and pcpu > 0:
				cpu_percent = self.cpu_less_one % ( pcpu )
				if self.cpu_rem_0: cpu_percent = cpu_percent.lstrip("0")
			elif pcpu >= 100:
				#no one process should show more than 99. This can happen during heavy IO which causes inaccurate readings
				cpu_percent = self.cpu_more_one % ( 99 )
			elif pcpu == 0:
				cpu_percent = "0%"
			else:
				cpu_percent = self.cpu_more_one % ( pcpu )

			cpu_percent = cpu_percent[:self.cpu_padding].rjust(self.cpu_padding)

			# if rssmem is > 1 MB print n.0m
			# otherwise print it in 'k' with no decimal precision
			if rssmem < 1:
				rssmem = "0"
			elif rssmem < 1000:
				rssmem = self.memK % ( rssmem )
			elif rssmem < 999999:
				rssmem = self.memM % ( rssmem / self.rss_mb )
			else:
				rssmem = self.memG % ( rssmem / self.rss_gb )

			rssmem = rssmem[:self.mem_padding].rjust(self.mem_padding)

			out_string += self.procOutformat % { 'command': command, 'cpu_percent': cpu_percent, 'memory': rssmem }

			time.sleep(self.granularity)

			if self.num_procs > 0:
				count += 1
				if count > self.num_procs: # break if we reached the limit to display
					break

		self.procOutStr = out_string

	def getprocOutStr(self):
		return self.procOutStr

	def setCmdJustification(self, side, amount):
		self.cmd_cutoff = amount
		if side.lower() == "right":
			self.cmd_rjust = amount
			self.cmd_ljust = 0
		elif side.lower() == "left":
			self.cmd_ljust = amount
			self.cmd_rjust = 0
		else:
			print "Invalid Justification: '" + side + "'. Accepted values are right or left. Defaulting to left."
			self.cmd_ljust = amount
			self.cmd_rjust = 0

	def setUpdateOutStr(self, value):
		self.updateOutStr = value

	def setProcOutformat(self, value):
		self.procOutformat = value

	def setNumProcs(self, value):
		self.num_procs = int(value)

	def setDisableThreading(self, value):
		self.disableThreading = value;
		print "pyTop: Disable threading: %s" % (value);

	def cpuFormat(self, cpu_padding=5, cpu_decimal_1=True, cpu_decimal_0=True, cpu_rem_0=False, cpu_more_one="%.1f%%", cpu_less_one="%.1f%%"):
		#This is the amount of padding to consider with the cpu percentage string. Right justified
		self.cpu_padding = cpu_padding #default: 5

    		#Whether to show the decimal if cpu percentage is greater than 1
    		self.cpu_decimal_1 = cpu_decimal_1 #default: True

    		#Whether to show the decimal if cpu percentage is less than 1
    		self.cpu_decimal_0 = cpu_decimal_0 #default: True

		#Whether to remove the leading zero when a percent is < 0
    		self.cpu_rem_0 = cpu_rem_0 #default: False

    		#Format of CPU percentage. You can modify the format when it's more than one and less then one
    		#If _cpu_decimal_* is false then...
    		self.cpu_more_one = cpu_more_one #default: "%.1f%%"
    		self.cpu_less_one = cpu_less_one #default: "%.1f%%"

	def cpuHideZero(self):
		#Whether to hide processes with a cpu percent of 0
		self.hide_0 = True #default: False

	def memFormat(self, mem_padding=6, memK="%.0fK", memM="%.1fM", memG="%.1fG"):
		self.mem_padding = mem_padding
		self.memK = memK
		self.memM = memM
		self.memG = memG

	def sortBy(self, sorttype):
		# takes arguments sort_* from above
		# sorts based upon sorttype
		if not self.hide_0: self.proclist.sort() # first, sort by the first field, procid

		if   sorttype == self.sort_cpu:
			if self.has24:
				self.proclist.sort(key=operator.itemgetter(1), reverse=True) # works with python 2.4
			else:
				self.proclist.sort( lambda a, b: cmp(b[1], a[1]) )

		elif sorttype == self.sort_cmd:
			if self.has24:
				self.proclist.sort(key=operator.itemgetter(2), reverse=True) # works with python 2.4
			else:
				self.proclist.sort( lambda a, b: cmp(string.lower(a[2]), string.lower(b[2])) )
#

		elif sorttype == self.sort_rss:
			if self.has24:
				self.proclist.sort(key=operator.itemgetter(3), reverse=True) # works with python 2.4
			else:
				self.proclist.sort( lambda a, b: cmp(b[3], a[3]) )


def __example():
	lock = thread.allocate_lock() # Allocate the lock
	TopRun = Top() # Init it
	TopRun.setNumProcs(5)
	TopRun.setUpdateOutStr(True) #Tells pytop to place the output in TopRun._procOutStr
	TopRun.setCmdJustification( "left", 20 )
	TopRun.cpuHideZero() # Hide 0% processes
	TopRun.cpuFormat( 5, True, True, False, "%.1f%%", "%.1f%%" )

	while True: # loop until the end of time, or press ctrl-c
		TopRun.start() # Yay, threading!
		lock.acquire()
		#print "TotalCPU: %d%%" % (TopRun.pcpu) # print TotalCPU xx%
		print TopRun.getprocOutStr()
		lock.release()
		#print ""
		time.sleep(2) # Wait a couple seconds

if __name__ == '__main__':
    __example()

