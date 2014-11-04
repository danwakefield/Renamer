Renamer
=======================

Utitity to rename tv show episodes to the desired format and location.


Information
-----------

This was one of the first _major_ scripts I wrote while teaching myself python.
Its badly written I'll be the first to admit but that doesnt matter to me since
it _just works_, sort of anyway ... .

I've learnt a lot more over the years so I think its time to give this a
facelift.

### Todo ###
A lot of the things I will be adding arent really necessary but Im going to do
them anyway to teach myself something new while refactoring this.

+ First thing first is to add tests. Unit tests would be a waste of time since
  the whole code structure is to be rewritten so I've decided to go fro black
  box tests against the whole script.
+ Change the way options to the script are stored. currently you have to edit
  the script source to change something as simple as the delimter to use
  between words, if you dont want to supply it at the command line each time
  that is. I'll be deciding between .ini and .json in due course.
+ Use of a database. Using sqlite it should be easy to store additional
  information that can help the script make furture decisons about renaming.
+ Automatic episode naming from the TVDB API or IMDB page scraping. A no
  brainer really.
+ Correction of misspelled show names using fuzzy text matching against the
  database. I.e,  'suth park' would be corrected to 'south park' if the
  database already held details about the show.
+ Plugin API submission for when episodecalendar.com and letterboxd.com open
  an API.
+ Use of xattr's on file to store extra information when possible. This would
  allow many extra features such as reverting the name to the state before
  running the script.
+ Handling of associated files properly. If a show has subtitle files this
  should be renamed to match the epside name and stored according to users
  wishes. I.e 'subs' subdirectory in the shows directory.
+ Reading and writing to episode filelists. witht he option to include eisode
  overviews so you can check what the episode is about without going online.
+ Better Multi episode support. Currently This is handled in some cases by
  coincidence and breaks in others .
+ Handling unwatched and watched folders.
+ Removal of years from show names. I.e 'Parenthood.2010' to 'parenthood'
  Current behaviour doesnt fix this and can sometimes break if a year exists
  but a seaons and episode dont.
+ Better display of actions. Current output is cramped and doesnt really show
  what has been changed. Add coloring and optional diffing of changes.

