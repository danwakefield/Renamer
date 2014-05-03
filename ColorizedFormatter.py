#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

TODO
====

+ Allow setting of fg and bg colors on a level seperatly
+ Implement deep_colorize in some way. 
+ Create Testing suite

"""
__license__ = "BSD-2"
__author__ = "Daniel Wakefield"
__copyright__ = "Copyright 2014"
__version__ = "1.0"
__email__ = "dwakefieldmail-git@yahoo.co.uk"
__status__ = "prototype"

from enum import Enum
import logging

ERROR = 1
SUCCESS = 0
LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

class Color:
    _colors = { "dk_red":  52, "lt_red": 1, "red": 1,
                "dk_green": 28, "lt_green": 84,"green": 2,
                "dk_yellow": 142, "lt_yellow": 192, "yellow": 3,
                "dk_blue": 18, "lt_blue": 45, "blue": 4,
                "dk_purple": 128, "lt_purple": 183, "purple": 5,
                "dk_orange": 166, "lt_orange": 136, "orange": 172,
                "dk_grey": 238, "lt_grey": 250, "grey": 244,
                "white": 15, "black": 16
                }
    
    def __init__(self, fg_default="white", 
                bg_default="black", combo_default=None):
        self.combo_default = combo_default
        self._combos = {"_default": {"fg": fg_default, "bg": bg_default}}
        self._colors.update([(str(i), i) for i in range(1, 256)])
        self.FGColor = Enum("FGColor", [(k, "\033[38;5;" + str(v) + "m") 
                                for k,v in self._colors.iteritems()])
        self.BGColor = Enum("BGColor", [(k, "\033[48;5;" + str(v) + "m") 
                                for k,v in self._colors.iteritems()])
    
    def fg(self, s=None):
        if not (s or self._combos.has_key(s)):
            s = self._combos["_default"]["fg"]
        
        return self.FGColor[s].value
    
    def bg(self, s=None):
        if not (s or self._combos.has_key(s)):
            s = self._combos["_default"]["bg"]
        
        return self.BGColor[s].value
        
    def reset(self):
        return self.fg() + self.bg()
    
    def combo(self, s=None):
        if s and self._combos.has_key(s):
            fg = self._combos[s]["fg"]
            bg = self._combos[s]["bg"]
        else:
            fg = self._combos["_default"]["fg"]
            bg = self._combos["_default"]["bg"]
        
        return self.fg(fg) + self.bg(bg)
    
    def set_combo(self, *args):
        arg_len = len(args)
        
        if (arg_len == 3):
            self._combos[args[0]] = {"fg": args[1], "bg": args[2]}
            return SUCCESS
        
        if (arg_len == 1):
            if (type({}) == type(args[0])):
                d = args[0]
                self._combos[d["name"]] = {"fg": d["fg"],"bg": d["bg"]}
            elif ((type([]) == type(args[0])) or (type(()) == type(args[0]))):
                L = args[0] 
                self._combos[L[0]] = {"fg": L[1], "bg": L[2]}
                return SUCCESS
        
        return ERROR
        
    def set_combos(self, d):
        """ Allows setting of large numbers of combos
            
            {"default" : {"fg": "white", "bg": "black"}, 
            "default2" : {"fg": "white", "bg": "black"}}
            
            [{"fg": "white", "bg": "black", "name": "default"}]
        """
        result = SUCCESS
        
        if (type(d) == type({})):
            for k,v in d.iteritems():
                if self.set_combo(k, v["fg"], v["bg"]): result = ERROR
        elif (type(d) == type([])):
            for i in d:
                if self.set_combo(i): result = ERROR
        
        return result


class ColorizedFormatter:
    """
    Wrapper class for logging.Formatter. Adds Terminal coloring to log
    strings.
    
    Default color_handler outputs colors suitable for 256 color terminals,
    This needs to be overriden if the terminal this is being used in doesnt
    support that.
    
    To colorize a log level it has to exist in _levels first. Levels cannot
    be colorized with seperate calls to color with fg and bg, a combo color
    is needed instead.
    
    """
    _attributes = { "%(name)s": "%(name)s",
                    "%(levelno)s": "%(levelno)s",
                    "%(levelname)s": "%(levelname)s",
                    "%(pathname)s": "%(pathname)s",
                    "%(filename)s": "%(filename)s",
                    "%(module)s": "%(module)s",
                    "%(lineno)d": "%(lineno)d",
                    "%(funcName)s": "%(funcName)s",
                    "%(created)f": "%(created)f",
                    "%(asctime)s": "%(asctime)s",
                    "%(msecs)d": "%(msecs)d",
                    "%(relativeCreated)d": "%(relativeCreated)d",
                    "%(thread)d": "%(thread)d",
                    "%(threadName)s": "%(threadName)s",
                    "%(process)d": "%(process)d",
                    "%(message)s": "%(message)s",
                    }
                    
    _levels = { logging.CRITICAL: None,
                logging.FATAL: None,
                logging.ERROR: None,
                logging.WARNING: None,
                logging.WARN: None,
                logging.INFO: None,
                logging.DEBUG: None,
                logging.NOTSET: None,
                }
    
    def __init__(self, formatter=None, color_handler=None, reset=True):
        self.C = color_handler or Color()
        self.formatter = formatter or logging.Formatter()
        self._uncolored_format = formatter._fmt
        self.reset_attributes_color = reset
    
    def colorize_level(self, level, color, type_="fg"):
        if self._levels.has_key(level):
            self.reset_attributes_color = False
            
            if (type_ == "fg"):
                self._levels[level] = self.C.fg(color)
            elif (type_ == "bg"):
                self._levels[level] = self.C.bg(color)
            elif (type_ == "combo"):
                self._levels[level] = self.C.combo(color)
    
    def colorize_attribute(self, attribute, color, type_="fg"):
        if self._attributes.has_key(attribute):
            s = ""
            
            if (type_ == "fg"):
                s = self.C.fg(color) + self._attributes[attribute]
                if self.reset_attributes_color:
                    s = s + self.C.fg()
            elif (type_ == "bg"):
                s = self.C.bg(color) + self._attributes[attribute]
                if self.reset_attributes_color:
                    s = s + self.C.bg()
            elif (type_ == "combo"):
                s = self.C.combo(color) + self._attributes[attribute]
                if self.reset_attributes_color:
                    s = s + self.C.combo()
                
            self._attributes[attribute] = s
        
    def format(self, record):
        if self._levels.has_key(record.levelno):
            if self._levels[record.levelno]:
                return self._levels[record.levelno] + self.colorize(record) + self.C.reset()
        
        return self.colorize(record)
        
    def colorize(self, record):
        colored_format = self._uncolored_format
        
        for k,v  in self._attributes.iteritems():
            if k == v:
                continue
            else:
                colored_format = colored_format.replace(k, v)
            
        self.formatter._fmt = colored_format
        s = self.formatter.format(record)
        self.formatter._fmt = self._uncolored_format
        
        return s
    
    def deep_colorize(self, record):
        raise NotImplementedError("Implement this method to get coloring inside\
                of attributes.")

