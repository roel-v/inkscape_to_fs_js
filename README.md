This is an extension for Inkscape that will export all Bezier curves to Javascript code to reproduce those curves using
the [Freesewing](http://freesewing.org) API. This is a convenience tool digitize sewing patterns. Trace them in
Inkscape, export using this tool, then copy/paste the output to your Freesewing design's draft() method. You will need
to fix up coordinates to make them use Freesewing measurements manually, of course.

Installation
------------

- Download by clicking 'Code' on Github and then selecting 'Download ZIP'
- Extract the zip somewhere
- Make a directory called 'to-freesewing-js' in your Inkscape extensions path. You can find out where that is by looking
  (in Inkscape) under Edit/Preferences/System/User extensions.
- Copy the contents of the directory 'extension' to this directory you just made.
- Start Inkscape. If you go to File/Save or File/Save as, there will be a new entry under the filetypes you can choose
  there called 'FreeSewing Path description (\*.js)'. Select that to export the Javascript code.

Development notes
-----------------

- For development, you want to work straight from your git repo and not copy to the actual extensions directory. Just
  make a symlink from the extensions directory to the location of your git repo. If you're on Windows, do

    mklink /D to-freesewing-js d:\freesewing\to-freesewing-js\extension

- Open Inkscape from the command line like this:

    "c:\Program Files\Inkscape\bin\inkscapecom.com" test_svgs\simple.svg
