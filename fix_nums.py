#!/usr/bin/env python
# vim:fdm=marker:
""" {{{
NAME
==================================================
	fix_nums

SYNOPSIS
==================================================
	fix_nums [opts] [files]

	Not suppling filenames means the script
	will use all detectable video files in
	the current directory.

DESCRIPTION
==================================================
	Program to decrapify and simplify filenames

	Intended for use mainly with TV epsiodes.

OPTIONS
==================================================
	-d, --delimiter [char]
		During renaming of the files spaces are
		replaced with the value passed in through
		this option. Default is a period.

	-c, --camelcase
		Camelcase will be turned on with this
		option. All discovered words will be
		capitalized when renaming the file.

	-l, --logfile [file]
		Supplies the name of the logfile to write
		too. Default is "$PWD/fixfiles.log".
		The arg "NONE" will turn off logging,
		this can also be set inside the file.

	-w, --writeformat [format]
		This arg allows you to supply the way
		in which files are renamed. See
		FORMAT OPTIONS for more detail.

	-p, --purge [word]
		This adds an item to the purge list
		any occurences of this will be replaced
		with nothing. Requires lower case.

	-D, --overwrite
		*** WARNING - DANGEROUS OPTION ***
		This option allows the program to overwrite
		other files. This can be very dangerous.

	-o, --outputdir [directory]
		This option allows you to specify where to
		place the files after renaming.

	-r, --saferename
		This option disables renaming and enables
		copying. The original files are left alone
		and copied to the specified location with
		thier new names.

	-s, --strict
		This option enables a strict renaming
		procedure. Files are not processed if
		WRITEFORMAT contains a field that
		cannot be determined.

	--epad [number]
		Allows you to alter the amount of zero
		padding that affects episodes.
		I.E. 3 would produce the number 001
		as the value for {episode}.
		Limited to max of 5.

	--spad [number]
		Allows you to alter the amount of zero
		padding that affects seasons.
		I.E. 4 would produce the number 0001
		as the value for {season}.
		Limited to max of 5.

	--showname [name]
		Pass a value in to override any value
		that is discovered for {show_name}

	--season [number]
		Pass a value in to override any value
		that is discovered for {season}
		
	-x, --dryrun
		Performs a dryrun of any selected operations.

	-h, --help
		Display this help message

	--license
		Display the licese for this program


FORMAT OPTIONS
==================================================

	This section describes the formatting options
	that can be supplied to modify the created
	filenames.
	

	{show_name}
		This is the guessed show name.

	{episode_name}
		The Guessed name for the episode.

	{season}
		This is the number representing the
		current season of the show.

	{episode}
		This is the number representing the
		current episode of the show.

	{sep}
		This option allows create of folders to 
		contain the new files.
		I.E. "folder{sep}{episode_name}"
		would place the file at
		"folder/Great.Episode.mp4"

	Both {show_name} and {season} can
	be passed in using the command line.
	These values will take precedence 
	over any that are discovered.
	
	Using the strict option also means that 
	files will not be processed if the 
	writeformat contains a field that cannot
	be determined.

""" # }}}


import getopt
import os
import sys
import re
import shutil

license = """ {{{
LICENSE
==================================================
Copyright (c) 2012, Daniel Wakefield
<daniel_wakefield (at) lavabit.com> 
All rights reserved.

Redistribution and use in source and binary
forms, with or without modification, are
permitted provided that the following
conditions are met: 
* Redistributions of source
code must retain the above copyright notice,
this list of conditions and the following
disclaimer. 
* Redistributions in binary form
must reproduce the above copyright notice, this
list of conditions and the following disclaimer
in the documentation and/or other materials
provided with the distribution. 
* Neither the name of the <organization> nor
the names of its contributors may be used
to endorse or promote products derived from
this software without specific prior written
permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT
HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
<COPYRIGHT HOLDER> BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
""" #}}}

#### Options #####################{{{#############
OPTS = {
"DELIM" : ".",
# Used to seperate parts of a file name instead of spaces
"CAMALCASE" : True,
# All Parts of a filename are capitalized 
"LOGFILE" : None,
# Location of log file 
"EPAD" : 2,
# Minimum length of episode field with zero padding
"SPAD" : 1,
# Minimum length of season field with zero padding
"WRITEFORMAT" : "{show_name}{sep}{season}{sep}{show_name} S{season}E{episode} {episode_name}",
# Valid writeout field are
# {show_name} | {season} | {episode} | {episode_name}
# {sep} - this is the os.sep char to allow creation
# of folders during the rename process
"OVERWRITE" : False,
# Allows program to overwrite files during the renaming process
# Enabling this option is very dangerous and can lead to large
# losses of data
"SAFERENAME" : False,
# Does not rename the files copys with the modified name instead
"OUTPUTDIR" : "/home/admx/video/keep",
# The directory to write the files too
"STRICT" : False,
# Disallows renaming if any field cannot be determined
"SHOWNAME" : None,
# Holder var for Command line passing of a show name
"SEASON" : None,
# Holder var for Command line passing of a season
"DRYRUN" : False,
# 
"LOG" : True,
#
"MEDIAFORMATS" : [".mkv",".mp4",".avi",".flv",".mpg",".mpeg"],
# Holds the extensions of common media files to include
}
################################}}}###############

## Items To Strip ############{{{#################
STRIP = [ "hdtv", "xvid", "-lol", "-fqm", "320p",
		  "480p", "720p", "1080p", "webrip",
		  "web-dl", "x264", "-msd", "-2hd", "-asap",
		  "[dd]", "h.264", "-idm", "h264", "aac2.0",
		  "-afg", "-evolve", "immerse", "ctrlhd",
		  "pixel", "web", "dl", "fov", "excellence",
		  "excell", "proper", "killers"
]
# These are just some common terms to strip from
# filenames.
# You can specify more at runtime by using the
# option -p or --purge.
# This option can be added multiple times on the
# command line.
# Items can be added to this list to remain a 
# permanant purge
# Arguements are in lower case
###############################}}}###############

### Regexs ###################{{{#################
REGEXS = [
	"[Ss](?P<S>\d{1,2})[\W_]?[Ee](?P<E>\d{1,2})" ,        
	# s01e01 | s1e1                        
	"\[?(?P<S>\d{1,2})\ ?[-x]\ ?(?P<E>\d{1,2})\]?" ,      
	# 01x01 | 1x01 | 1x1 | 01x1 | 01-01 | 1-01 | 1-1 | 01-1
	# [01x01] | [1x01] | etc
	"[Ss]eason[\W_]?(?P<S>\d{1,2})[\W_]?[Ee]pisode[\W_]?(?P<E>\d{1,2})",
	# Although this is an accurate regex it is not a very common
	# pattern :. try matching later on
	"[\W_](?P<S>\d)(?P<E>\d{2})[\W_]",            
	# 101  - This is not the most reliable method          
]
# TODO
#
# These would probably be faster as compiled 
# re patterns
##############################}}}#################


class FileObject: #{{{
	""" Class for representing info about a file

		Functions
		---------
		get - returns tuple(start_name, new_name)

	"""
	
	def __init__(self, start_name): #{{{
		self.values = { "old_name"      : None,
						"start_name"    : start_name,
						"directory"     : None,
						"extension"     : None,
						"show_name"     : None,
						"episode"       : None,
						"season"        : None,
						"new_name"      : None,
						"episode_name"  : None }

		self.success = True
		self._split_start_name(start_name)
		self._parse()

	# __init__ }}}

	def __is_strict(self, f_args): #{{{
		p = re.compile("\{(\w+)\}")
		o = p.findall(OPTS["WRITEFORMAT"])

		for a in o:
			if f_args[a] == None or f_args[a] == "":
				return False

		return True
	# __is_strict }}}

	def __strip(self, s): # {{{
		s = s.lower()
		for i in STRIP:
			s = s.replace(i, "")
		
		s = s.replace(".", " ")
		s = s.replace(", ", " ")
		s = s.replace(",", " ")
		s = s.replace("_", " ")
		s = s.replace("'", "")
		s = s.replace(" - ", " ")
		s = s.replace("-", " ")
		s = s.strip()

		return s

	# __strip }}}

	def __capitalize(self, s): # {{{
		if OPTS["CAMALCASE"]:
			l = s.split(" ")
			new_l = []
			d = OPTS["DELIM"]
			for word in l:
				word = word.capitalize()
				new_l.append(word)
				new_l.append(d)
				
			new_l.pop()
			return "".join(new_l)
		else:
			return s.replace(" ", OPTS["DELIM"])

	# __capitalize }}}

	def __pad(self, n, pad_count): # {{{
		s = str(n)
		while len(s) < pad_count:
			s = "0" + s
			
		return s

	# __pad }}}

	def _parse(self): # {{{
		self._season_episode_parse()
		self._show_name_parse()
		self._episode_name_parse()
		self._create_new_name()

	# _parse }}}

	def _split_start_name(self, fname): #{{{
		d, f = os.path.split(fname)
		f, e = os.path.splitext(f)

		self.values["directory"] = d
		self.values["old_name"]  = f
		self.values["extension"] = e

	# _split_start_name }}}

	def _season_episode_parse(self): #{{{
		""" Performs multiple searchs to determine
			the season and episode numbers. 
		"""
		
		for p in REGEXS:
			m = re.search(p, self.values["old_name"])

			if m != None:
				season = int(m.group("S"))  
				episode = int(m.group("E"))
				self.values["season"] = self.__pad(season , OPTS["SPAD"])
				self.values["episode"] = self.__pad(episode, OPTS["EPAD"])
				s = re.split(p, self.values["old_name"])

				if len(s) == 4:
					self.values["show_name"] = s[0].strip()
					self.values["episode_name"] = s[3].strip()
				else:
					self.success = False
					
				return 0

		self.success = False
		
	# _season_episode_parse }}}

	def _episode_name_parse(self): # {{{
		en = self.values["episode_name"]
		if en == "" or en == None:
			return 0
		
		s = self.__strip(en)
		self.values["episode_name"] = self.__capitalize(s)

	# _episode_name_parse }}}

	def _show_name_parse(self): # {{{
		if OPTS["SHOWNAME"] != None:
			self.values["show_name"] = OPTS["SHOWNAME"]
			return 0

		sn = self.values["show_name"]
		if sn == "" or sn == None:
			return 0

		s = self.__strip(sn)
		
		self.values["show_name"] = self.__capitalize(s)

	# _show_name_parse }}}

	def _create_new_name(self): #{{{
		format_args = { "episode"       : self.values["episode"],
						"season"        : self.values["season"],
						"show_name"     : self.values["show_name"],
						"episode_name"  : self.values["episode_name"],
						"sep"           : os.sep }

		if OPTS["STRICT"] and not self.__is_strict(format_args):
			self.success = False
			return 0

		s = OPTS["WRITEFORMAT"].format(**format_args)
		s = s.strip()
		s = s.replace(" ", OPTS["DELIM"])

		self.values["new_name"] = s + self.values["extension"]
	# _create_new_name }}}

	def get(self):#{{{
		if self.success == True:
			return (self.values["start_name"], self.values["new_name"])
		else:
			return (self.values["start_name"], False)

	# get }}}

	def _debug_log(self): #{{{
		for k, v in self.values.iteritems():
			print str(k) + " == " + repr(v)

	#}}}


# FileObject }}}
		
class Processor: # {{{

	def __init__(self): # {{{
		self.files = []

		if OPTS["SAFERENAME"]:
			self.action = "Copy"
			self._move_func = shutil.copy
		else:
			self.action = "Move"
			self._move_func = shutil.move

		if OPTS["DRYRUN"]:
			self._move_func = lambda x = None, y = None: None

		self.log_level = OPTS["LOG"]

	# __init__ }}}

	def LOG(self, message): #{{{
		if self.log_level:
			LOG(message)

	# LOG }}}

	def add_file(self, f): #{{{
		self.files.append(f)

	# add_file }}}

	def process(self): #{{{
		for f in self.files:
			self._do_process(f)
			self.LOG("")

	# process }}}

	def _do_process(self, o): #{{{
		old, new = o.get()

		if new == False:
			self.LOG("{0} - Cannot Be renamed".format(old))
			return 0

		t, h = os.path.split(new)

		path = os.path.join(OPTS["OUTPUTDIR"], t)
		if not os.path.isdir(path) and not OPTS["DRYRUN"]:
			os.makedirs(path)
			self.LOG("Created Directory Structure - {0}".format(path))

		new = os.path.join(path, h)

		if old == new:
			self.LOG("{0} not changed - Identical Names".format(old))
			return 0

		if os.path.isfile(new) and not OPTS["OVERWRITE"]:
			self.LOG("Cannot {0} - {1} ==> {2}\n".format(self.action, old, new) +\
					"A file already exists at this path. " +\
					"Add -D to force an overwrite")
			return 0

		self._relocate_file(old, new)
		
		return 1

	# _do_process }}}

	def _relocate_file(self, src, dst): #{{{
		 try:
			 self._move_func(src, dst)
			 self.LOG("{0} {1} -> {2} | Success".format(self.action, src, dst.replace(OPTS["OUTPUTDIR"] + "/","")))
		 except e:
			 self.LOG("{0} {1} -> {2} | Failed".format(self.action, src, dst))
			 
	#_relocate_file}}}

# Processor }}}



def LOG(message):# {{{
	if OPTS["LOGFILE"] == None:
		f = sys.stdout
	else:
		if type(OPTS["LOGFILE"]) == type(sys.stdout):
			f = OPTS["LOGFILE"]
		else:
			try:
				f = open(OPTS["LOGFILE"], "a")
			except:
				OPTS["LOGFILE"] == None
				f = sys.stdout

	f.write(message + "\n")
	if not type(f) == type(sys.stdout):
		f.close()


# LOG }}}

def is_playable(x): #{{{
	# This filters out files that are not media files
	_, ext = os.path.splitext(x)
	if ext in OPTS["MEDIAFORMATS"]:
		return True
	else:
		return False
#}}}

def __usage(x): #{{{
	if x == 1:
		print __doc__
	elif x == 2:
		print license
	else:
		pass
#}}}

def main(argv = None): #{{{
	short_args = "d:cl:w:o:rhDStp:xv"
	long_args = ["camelcase",     # c - CAMELCASE   flag
				 "overwrite",     # D - OVERWRITE   flag
				 "saferename",    # r - SAFERENAME  flag
				 "strict",        # s - STRICT      flag
				 "dryrun",        # x - DRYRUN      flag
				 "verbose",       # v - verbose     flag
				 "logfile=",      # l - LOGFILE     arg
				 "writeformat=",  # w - WRITEFORMAT arg
				 "outputdir=",    # o - OUTPUTDIR   arg
				 "delimiter=",    # d - DELIM       arg
				 "purge=",        # p - STRIP       arg
				 "epad=",         # EPAD            arg
				 "spad=",         # SPAD            arg
				 "season=",       # SEASON          arg
				 "showname=",     # SHOWNAME        arg
				 "help",
				 "license",
				]

	if argv == None:
		argv = sys.argv[1:]

	try:
		opts, args = getopt.getopt(argv, short_args, long_args)
	except getopt.GetoptError, e:
		__usage()
		print str(e)
		sys.exit(2)

	TEST = False
	for opt, arg in opts:
		if opt in ["-h", "--help"]:
			__usage(1)
			sys.exit(1)
		elif opt in ["-d", "--delimiter"]:
			OPTS["DELIM"] = arg
		elif opt in ["-c", "--camelcase"]:
			OPTS["CAMELCASE"] = True
		elif opt in ["-l", "--logfile"]:
			OPTS["LOGFILE"] = arg
		elif opt in ["-w", "--writeformat"]:
			OPTS["WRITEFORMAT"] = arg
		elif opt in ["-D", "--overwrite"]:
			OPTS["OVERWRITE"] = True
		elif opt in ["-r", "--saferename"]:
			OPTS["SAFERENAME"] = True
		elif opt in ["-o", "--outputdir"]:
			OPTS["OUTPUTDIR"] = arg
		elif opt in ["-s", "--strict"]:
			OPTS["STRICT"] = True
		elif opt in ["-p", "--purge"]:
			STRIP.append(arg)
		elif opt in ["-x", "--dryrun"]:
			OPTS["DRYRUN"] = True
		elif opt in ["-v", "--verbose"]:
			OPTS["LOG"] = True
		elif opt == "--season":
			OPTS["SEASON"] = arg
		elif opt == "--showname":
			OPTS["SHOWNAME"] = arg
		elif opt == "--epad":
			OPTS["EPAD"] = min(int(arg), 5)
		elif opt == "--spad":
			OPTS["SPAD"] = min(int(arg), 5)
		elif opt == "-t":
			TEST = True
		elif opt == "--license":
			__usage(2)
			sys.exit(1)
		else:
			assert 0, "Unhandled Option - {0}".format(opt)


	if not args:
		fl = os.listdir(".")
	else:
		fl = args

	processor = Processor()
	for f in fl:
		if is_playable(f):
			in_f = FileObject(f)
			processor.add_file(in_f)

	if TEST:
		for f in processor.files:
			i = raw_input(".")
			f._debug_log()
			if i == "q":
				break
		
	processor.process()
	# main }}}

if __name__ == "__main__":
	main()


