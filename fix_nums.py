#!/usr/bin/env python
# ex: set foldmethod=marker
""" {{{
NAME
==================================================
    fix_nums

SYNOPSIS
==================================================
    fix_nums [opts]

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

    -i, --indexfile
        If arg is supplied turns on creation of
        and index file for the show. If more
        than one show name is discovered this
        option does procede. Index file is
        written out in Markdown format.

    -w, --writeformat [format]
        This arg allows you to supply the way
        in which files are renamed. See 
        FORMAT OPTIONS for more detail.

    -D, --overwrite
        DANGEROUS OPTION - WARNING
        This option allows the program to overwrite
        other files. This can be very dangerous.

    -o, --outputdir [directory]
        This option allows you to specify where to 
        place the files after renaming.

    -s, --saferename
        This option disables renaming and enables
        copying. The original files are left alone
        and copied to the specified location with
        thier new names.

    -S, --strict
        This option enables a strict renaming 
        procedure. Files are not processed if
        WRITEFORMAT contains a field that
        cannot be determined.

    --epad [number]
        Allows you to alter the amount of zero 
        padding that affects episodes.
        I.E. 3 would produce the number 003
        as the value for {episode}

    --spad [number]
        Allows you to alter the amount of zero 
        padding that affects seasons.
        I.E. 3 would produce the number 003
        as the value for {season}

    --showname [name]
        Pass a value in to override any value
        that is discovered for {show_name}

    --season [number]
        Pass a value in to override any value
        that is discovered for {season}
        
    -h, --help
        Display this help message


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
""" # }}}

import getopt
import os
import sys
import re

#### Options #####################{{{#############
OPTS = {
"DELIM" : ".",
# Used to seperate parts of a file name instead of spaces
"CAMALCASE" : True,
# All Parts of a filename are capitalized 
"LOGFILE" : None,
# Location of log file 
"SUBFILES" : False,
# Mimics Naming onto known subtitle files and stores in Subs dir
"INDEXFILE" : True,
# Creates an md file in a simple layout for file descriptions 
"EPAD" : 2,
# Required length of episode field after zero padding
"SPAD" : 1,
# Required length of season field after zero padding
"WRITEFORMAT" : "{show_name}{sep}{season}{sep}{show_name}S{season}E{episode}{episode_name}",
# Valid writeout field are
# {quality} | {show_name} | {season} | {episode} | {episode_name}
# {sep} - this is the os.sep char to allow creation
# of folders during the rename process
"OVERWRITE" : False,
# Allows program to overwrite files during the renaming process
# Enabling this option is very dangerous and can lead to large
# losses of data
"SAFERENAME" : False,
# Does not rename the files copys to a subdirectory
# with the modified name instead
"OUTPUTDIR" : os.getcwd(),
}
################################}}}###############

### Case Examples ##############{{{###############
# 
# Must be able to place 
# Show Name, Season, Episode, Episode Title, Quality
# in a user defined way
#
# Must match Season and Episode in the formats
# S01E01 | s01e01 | s01e1 | s1e1 | 1x01 | 1x1 | 101 
#
# Matching quality is much simpler as there are only 
# a few qualitys that are released
# 320p | 480p | 720p | 1080p
#
# Renaming should also strip out useless information
# such as
# release names - striped by miXed cASe letters 
# HDTV
# WEB-DL
# XviD
#
# Matching Show name will be more difficult as it
# will be hard to differentiate.
# Show name is usally the first part of the filename
# but the is not always the case some release groups
# place a web-address before the showname
# 
# One way of discovering show names will be comparing
# the guessed names across multiple files
#
# Episode name is nearly always the last part of the
# filename after the Season/Episode identifier
# it can also follow the show name with a hyphen
# delimiter
# 
#################################}}}##############

### Regexs ###################{{{#################
REGEXS = [ {  1 : "[sS](?P<S>\d{1,2})[eE](?P<E>\d{1,2})" ,        
              # S01E01 | s01e01 | S1E1 | s1e1                        
              2 : "(?P<S>\d{1,2})\ ?[-x]\ ?(?P<E>\d{1,2})" ,      
              # 01x01 | 1x01 | 1x1 | 01x1 | 01-01 | 1-01 | 1-1 | 01-1
              3 : "[ \[]?(?P<S>\d)(?P<E>\d{2})[ \]]?",            
              # 101  - This is not the most reliable method          
           }, # Season - Episode regexes index 0

]
##############################}}}#################

class FileObject: #{{{
    """ Class for representing info about a file

        Functions
        ---------
        get_filenames - returns tuple(start_name, new_name)

    """
    
    def __init__(self, start_name): #{{{
        self.values = { "old_name"      : None,
                        "start_name"    : start_name,
                        "directory"     : None,
                        "extension"     : None,
                        "show_name"     : None,
                        "episode"       : None,
                        "season"        : None,
                        "quality"       : None,
                        "episode_name"  : None }

        self._split_start_name(start_name)
        self._season_episode_parse()

    # __init__ }}}

    def _split_start_name(self, fname): #{{{
        d, f = os.path.split(fname)
        f, e = os.path.splitext(f)

        self.values["directory"] = d

        for i in ["_", ".", "-", ","]:
            f = f.replace(i, " ")

        self.values["old_name"]  = f
        self.values["extension"] = e

    # _split_start_name }}}

    def _season_episode_parse(self): #{{{
        """ Performs multiple searchs to determine
            the season and episode numbers. 
        """
        
        for p in REGEXS[0].itervalues():
            m = re.search(p, self.values["old_name"])

            # The earlier the match the better the probabilty
            # of the match being correct therefore we exit
            # the check after the first match
            if m != None:
                self.values["season"] = m.group("S")
                self.values["episode"] = m.group("E")
                s = re.split(p, self.values["old_name"])

                if len(s) == 4:
                    self.values["show_name"] = s[0]
                    self.values["episode_name"] = s[3]
                else:
                    print s
                    # This should raise an error that can be handled
                    assert 0, "Filename contains extra Season-Episode identifiers"
                    

                break
        

    # _season_episode_parse }}}

    def get_filenames(self): #{{{
        """  
            Formats new_name according to
            OPTS[WRITEFORMAT] 
            
            Returns ( old_name, new_name )
        """

        old_name = self.values["directory"] + os.sep +\
                   self.values["old_name"] + self.values["extension"]

        format_args = { "episode"      : self.episode_num,
                        "season"       : self.season_num,
                        "show_name"    : self.show_name,
                        "episode_name" : self.episode_name,
                        "quality"      : self.quality,
                        "sep"          : os.sep }
        

        if OPTS["STRICT"] and not self._is_strict(format_args):
            return False
        
        new_name = OPTS["WRITEFORMAT"].format(**format_args)
        new_name.replace(" ", OPTS["DELIM"])
        new_name += self.extension

        return (old_name, new_name)

    # get_filenames }}}

    def _is_strict(self, f_args): #{{{
        p = re.compile("\{(\w+)\}")
        o = p.findall(OPTS["WRITEFORMAT"])

        for a in o:
            if f_args[a] == None:
                return False

        return True
                                          
    # _is_strict }}}

# FileObject }}}
        

def __usage():
    print __doc__

def main(argv = None): #{{{
    short_args = "d:cl:siw:o:rhDS"
    long_args = ["camelcase",     # c - CAMELCASE   flag
                 "subfiles",      # s - SUBFILES    flag
                 "indexfile",     # i - INDEXFILE   flag
                 "overwrite",     # D - OVERWRITE   flag
                 "saferename",    # r - SAFERENAME  flag
                 "strict",        # S - STRICT      flag
                 "logfile=",      # l - LOGFILE     arg
                 "writeformat=",  # w - WRITEFORMAT arg
                 "outputdir=",    # o - OUTPUTDIR   arg
                 "delimiter=",    # d - DELIM       arg
                 "epad=",         # EPAD            arg
                 "spad=",         # SPAD            arg
                 "season=",       # SEASON          arg
                 "showname=",     # SHOWNAME        arg
                 "help",
                ]

    if argv == None:
        argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, short_args, long_args)
    except getopt.GetoptError, e:
        __usage()
        print str(e)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            __usage()
            sys.exit(1)
        elif opt in ["-d", "--delimiter"]:
            OPTS["DELIM"] = arg
        elif opt in ["-c", "--camelcase"]:
            OPTS["CAMELCASE"] = True
        elif opt in ["-l", "--logfile"]:
            OPTS["LOGFILE"] = arg
        elif opt in ["-s", "--subfiles"]:
            OPTS["SUBFILES"] = True
        elif opt in ["-i", "--indexfile"]:
            OPTS["INDEXFILE"] = True
        elif opt in ["-w", "--writeformat"]:
            OPTS["WRITEFORMAT"] = arg
        elif opt in ["-D", "--overwrite"]:
            OPTS["OVERWRITE"] = True
        elif opt in ["-r", "--saferename"]:
            OPTS["SAFERENAME"] = True
        elif opt in ["-o", "--outputdir"]:
            OPTS["OUTPUTDIR"] = arg
        elif opt in ["-S", "--strict"]:
            OPTS["STRICT"] = True
        elif opt == "--season":
            OPTS["SEASON"] = arg
        elif opt == "--showname":
            OPTS["SHOWNAME"] = arg
        elif opt == "--epad":
            OPTS["EPAD"] = arg
        elif opt == "--spad":
            OPTS["SPAD"] = arg
        else:
            assert 0, "Unhandled Option - {0}".format(opt)

    # main }}}


if __name__ == "__main__":
    main()


