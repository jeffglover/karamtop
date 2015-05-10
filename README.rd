# karamtop
Superkaramba theme that emulates the functionality of top
Copyright (C) Jeff Glover

Designed to work with TDE - T Desktop Enhancements from www.kde-look.org

Usage: Just add karamtop.theme using SuperKaramba. From the config menu.
You can configure the theme, whether to show processes where the CPU usage
is 0, or the order of the output. Open the current theme file from the
themes directory to fine tune the configuration.

About:
A threaded python script that parses /proc.
Shows an X number of runnig processes with CPU, Memory usage and program name,
sorted by CPU. The default number of processes to show is 8. More than that
and the text will run out of space, so you will have to redo the graphic,
or change the font. Idea based on the gkrelltop a plugin for GKrellM.
pytop.py is the class file. It can be used within any kind of script.

Requirements:
SuperKaramba v0.36, Python v2.3.4

Version numbers are what I had on my Gentoo system as of 3/16/05. Newer
versions should work, I don't know about older versions.

Download gkrelltop: http://web.wt.net/~billw/gkrellm/Plugins.html

Licensing
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
http://www.gnu.org/licenses/gpl.txt

all graphics liscensed GPL by original authors
ksysguard.png is from KDE's Crystal theme
The rest are copied from the TDE Superkaramba theme