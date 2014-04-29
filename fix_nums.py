#!/usr/bin/env python
# vim:fdm=marker:
"""
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

"""

import getopt
import os
import sys
import re
import shutil
import logging

license = """
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
""" 

# Options #############################################
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
# The directory to write the files to
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
"MEDIAFORMATS" : [".mkv",".mp4",".avi",".flv",".mpg",".mpeg",".srt"],
# Holds the extensions of common media files to include
}
###########################################################

# Items To Strip ##########################################
STRIP = [ "hdtv", "xvid", "lol", "fqm", "320p",
		  "480p", "720p", "1080p", "webrip",
		  "web-dl", "x264", "msd", "2hd", "asap",
		  "[dd]", "h.264", "idm", "h264", "aac2.0",
		  "afg", "evolve", "immerse", "ctrlhd",
		  "pixel", "web", "dl", "fov", "excellence",
		  "excell", "proper", "killers", "tla",
		  "dvdrip", "repack", "ddlvalley.net"
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
###############

### Regexs ###################################
REGEXS = [
	re.compile("""	
	(?P<SN>.*?)			# Named Group (SN) non greedily capturing show name
	s					# Letter S representing season
	(?P<S>\d{1,2})		# Named Group (S) capturing 1/2 digits for season no
	[\W_]?				# Single Optional Non Alpha-Num char
	e					# Letter E representing Episode
	(?P<E>\d{1,2})		# Named Group (E) Capturing 1/2 digits for episode no
	[\W_]*?				# Non greedy optional Non Alpha-Num char
	(?P<EN>.*)			# Named Group (EN) greedily trying to grab episode name"""
	,re.IGNORECASE | re.VERBOSE),
	
	re.compile("""
	(?P<SN>.*?)			# NG(SN) non greedily capturing show name
	(?P<OB>\[?)			# Optional Literal [ - NG(OB) for matching bracket later
	(?P<S>\d{1,2})		# NG(S) capturing 1/2 digits for season no
	\ ?					# Optional Space
	[-x]				# Literal - or x
	\ ?					# Optional Space
	(?P<E>\d{1,2})		# NG(E) capturing 1/2 digits for episode no
	(?(OB)\])			# Matchs literal ] if [ occured earlier
	(?P<EN>.*)			# NG(EN) greedily trying to grab episode name"""
	,re.IGNORECASE | re.VERBOSE),
	
	re.compile("""
	(?P<SN>.*?)			# NG(SN) non greedily capturing show name
	season				# Character literals
	[\W_]?				# Optional non alphanum char
	(?P<S>\d{1,2})		# NG(S) capturing 1/2 digits for season no
	[\W_]?				# Optional non alphanum char
	episode				# Character literals
	[\W_]?				# Optional non alphanum char
	(?P<E>\d{1,2})		# NG(E) capturing 1/2 digits for episode no
	(?P<EN>.*)			# NG(EN) greedily trying to grab episode name"""
	,re.IGNORECASE | re.VERBOSE),
	
	re.compile("""
	(?P<SN>.*?)			# NG(SN) non greedily capturing show name
	[\W_]				# non alphanum char
	(?P<S>\d)			# NG(S) grab 1 digit for season number
	(?P<E>\d{2})		# NG(E) grab 2 digits for episode number
	[\W_]				# non alphanum char
	(?P<EN>.*)			# NG(EN) greedily trying to grab episode name"""
	,re.IGNORECASE | re.VERBOSE),
	
	re.compile("""
	ep					# Character Literals
	(?:isode)?			# Junk group for optional character literals
	[\W_]?				# Optional non alphanum char
	(?P<E>\d{1,2})		# NG(E) capturing 1/2 digits for episode no
	[\W_]				# non alphanum char
	(?P<EN>.*)			# NG(EN) greedily trying to grab episode name"""
	,re.IGNORECASE | re.VERBOSE),
]

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

STDOUT_LOGGER = logging.StreamHandler(sys.stdout)
STDOUT_LOGGER_FORMAT = logging.Formatter("%(message)s")
STDOUT_LOGGER.setFormatter(STDOUT_LOGGER_FORMAT)

LOGGER.addHandler(STDOUT_LOGGER)

#################

class FileObject: 
	""" Class for representing info about a file"""
	
	def __init__(self, start_name): 
		self.values = { "old_name"      : None,
						"start_name"    : start_name,
						"directory"     : None,
						"extension"     : None,
						"show_name"     : None,
						"episode"       : None,
						"season"        : None,
						"new_name"      : None,
						"episode_name"  : None }
		
		LOGGER.debug("Created fileobject for %s", start_name)
		self.success = True
		self._split_start_name(start_name)
		self._parse()
	

	def __is_strict(self, f_args): 
		p = re.compile("\{(\w+)\}")
		o = p.findall(OPTS["WRITEFORMAT"])
		
		for a in o:
			if f_args[a] == None or f_args[a] == "":
				return False
		
		return True
	

	def __strip(self, s):
		s = s.lower()
		LOGGER.debug("Starting __strip : '%s'", s)
		s = s.replace("_", " ")
		
		for i in STRIP:
			s = re.compile("\\b" + i + "\\b").sub("", s)
		
		LOGGER.debug("Strip : Result : '%s'", s)
		
		s = s.replace(".", " ")
		s = s.replace(", ", " ")
		s = s.replace(",", " ")
		s = s.replace("'", "")
		s = s.replace(" - ", " ")
		s = s.replace("-", " ")
		s = s.strip()
		
		LOGGER.debug("Finished __strip : '%s'", s)

		return s
	

	def __capitalize(self, s):
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
	

	def __pad(self, n, pad_count):
		s = str(n)
		while len(s) < pad_count:
			s = "0" + s
			
		return s
	

	def _parse(self):
		self._season_episode_parse()
		self._create_new_name()
	

	def _split_start_name(self, fname): 
		d, f = os.path.split(fname)
		f, e = os.path.splitext(f)

		self.values["directory"] = d
		self.values["old_name"]  = f
		self.values["extension"] = e
	

	def _season_episode_parse(self): 
		""" Performs multiple searchs to determine
			the season and episode numbers. """
		
		for p in REGEXS:
			m = re.search(p, self.values["old_name"])
			
			if m:
				season = episode = showname = episodename = None
				values = m.groupdict()
				LOGGER.debug("Parsed Values : %s", values)
				
				# Sets episode value or fails the rename if this isnt possible
				if "E" in values:
					episode = int(values["E"])
				else:
					self.success = False
				
				# Sets season or fails the rename if it isnt possible
				if "S" in values:
					if OPTS["SEASON"]:
						season = OPTS["SEASON"]
					else:
						season = int(values["S"])
				else:
					if OPTS["SEASON"]:
						season = OPTS["SEASON"]
					else:
						self.success = False
				
				
				if "SN" in values:
					if OPTS["SHOWNAME"]:
						showname = OPTS["SHOWNAME"]
					else:
						showname = values["SN"]
				else:
					if OPTS["SHOWNAME"]:
						showname = OPTS["SHOWNAME"]
					else:
						self.success = False
				
				if "EN" in values:
					episodename = values["EN"]
				else:
					episodename = ""
				
				self.values["season"] = self.__pad(season, OPTS["SPAD"])
				self.values["episode"] = self.__pad(episode, OPTS["EPAD"])
				self.values["show_name"] = self.__capitalize(self.__strip(showname.strip()))
				self.values["episode_name"] = self.__capitalize(self.__strip(episodename.strip()))
				return
		
		self.success = False
	
	
	def _create_new_name(self): 
		format_args = { "episode"		: self.values["episode"],
						"season"		: self.values["season"],
						"show_name"		: self.values["show_name"],
						"episode_name"	: self.values["episode_name"],
						"sep"			: os.sep }
		
		if OPTS["STRICT"] and not self.__is_strict(format_args):
			self.success = False
			return
		
		s = OPTS["WRITEFORMAT"].format(**format_args)
		LOGGER.debug("create_new_name : %s", s)
		s = s.strip()
		s = s.replace(" ", OPTS["DELIM"])
		LOGGER.debug("create_new_name : %s", s)
		s = re.compile("\.{2,}").sub(".", s)
		LOGGER.debug("create_new_name : %s", s)
		
		self.values["new_name"] = s + self.values["extension"]
	

	def get(self):
		if self.success == True:
			return (self.values["start_name"], self.values["new_name"])
		else:
			return (self.values["start_name"], False)
	
	
class Processor: 
	def __init__(self):
		self.files = []
		
		if OPTS["SAFERENAME"]:
			self.action = "Copy"
			self._move_func = shutil.copy
		else:
			self.action = "Move"
			self._move_func = shutil.move
		
		if OPTS["DRYRUN"]:
			self._move_func = lambda x = None, y = None: None
	

	def add_file(self, f): 
		self.files.append(f)
	

	def process(self): 
		for f in self.files:
			self._do_process(f)
	

	def _do_process(self, o): 
		old, new = o.get()
		
		if new == False:
			LOGGER.info("{0} - Cannot Be renamed".format(old))
			return 0
		
		t, h = os.path.split(new)
		
		path = os.path.join(OPTS["OUTPUTDIR"], t)
		if not os.path.isdir(path) and not OPTS["DRYRUN"]:
			os.makedirs(path)
			LOGGER.info("Created Directory Structure - {0}".format(path))
		
		new = os.path.join(path, h)
		
		if old == new:
			LOGGER.info("{0} not changed - Identical Names".format(old))
			return 0
		
		if os.path.isfile(new) and not OPTS["OVERWRITE"]:
			LOGGER.info("Cannot {0} - {1} ==> {2}\n".format(self.action, old, new) +\
					"A file already exists at this path. " +\
					"Add -D to force an overwrite")
			return 0
		
		self._relocate_file(old, new)
		
		return 1


	def _relocate_file(self, src, dst): 
		 try:
			self._move_func(src, dst)
			LOGGER.info("{0} {1} -> {2} | Success".format(self.action, src, dst.replace(OPTS["OUTPUTDIR"] + "/","")))
		 except e:
			LOGGER.info("{0} {1} -> {2} | Failed".format(self.action, src, dst)) 

def is_playable(x): 
	# This filters out files that are not media files
	_, ext = os.path.splitext(x)
	if ext in OPTS["MEDIAFORMATS"]:
		return True
	else:
		return False


def __usage(x): 
	if x == 1:
		print __doc__
	elif x == 2:
		print license
	else:
		pass


def main(argv = None): 
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
			LOGGER.setLevel(logging.DEBUG)
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
			LOGGER.setLevel(logging.DEBUG)
			if i == "q":
				break
		
	processor.process()
	

if __name__ == "__main__":
	main()


