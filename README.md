This is an extension for Inkscape that will export the document's SVG to Javascript code to reproduce the document's
design as a [Freesewing](http://freesewing.org) design, using the the FreeSewing Javascript API. This is a convenience
tool to digitize sewing patterns. Trace or design them in Inkscape, export using this tool, then copy/paste the output
to your Freesewing design's draft() method. You will need to fix up coordinates to make them use Freesewing measurements
manually, of course.

Installation
============

- Download by clicking 'Code' on Github and then selecting 'Download ZIP'
- Extract the zip somewhere
- Make a directory called 'to-freesewing-js' in your Inkscape extensions path. You can find out where that is by looking
  (in Inkscape) under Edit/Preferences/System/User extensions.
- Copy the contents of the directory 'extension' to this directory you just made.
- Start Inkscape. Under 'Extensions', you will see a menu called 'FreeSewing', which has an entry 'Export to Freesewing
  JS...'.



User manual
===========

Marking up your SVG
-------------------

In order to be able to generate valid code for a Freesewing design, the extension needs to know things like what element
in your SVG make up what parts, what is the name of the design etc. How you let those things know is like this:

- The design name is derived from a text box with the name 'design-name' in a layer called 'metadata'. Insert this layer
  and element into your document so that the generated code can use the correct design name where it needs it. You can
  make this layer invisible if it's in your way.

- The only curves and lines that are exported, are the ones in layers with a name called 'part:' and then a name for
  your part. So you 'define' a part called 'back' by putting in a layer called 'part: back' and then putting all lines
  and curves that make up the shape of this part in that layer.

What is generated
-----------------

When you run the extension, it will let you select a design directory. Choose the root directory of your design there;
you'll need to have made the design first through the regular methods as documented in the Freesewing documentation.
When you click 'Apply', a number of files are written to that directory:

- src\index.mjs. This file is only created if it doesn't exist yet; if it exists, it's not overwritten, so it's safe to
  modify this file and run the extension export again. This file contains the definition of the design, i.e. metadata
  like its name, and what parts it's composed of. If you add parts to your design, you may have to manually edit this
  file, or delete it before running the extension, then re-applying any changes (like measurements) you made to it
  before.
- For each part (see above how those are defined): src\parts\\[part name]\[part name].mjs . Again, this file is not
  overwritten if it already exists and the same caveats apply as for index.mjs. This file draws the actual part. It does
  so in 'chunks' by calling out to other functions that actually draw the lines and curves, i.e. per path that was found
  in the svg. This way, you can manually customize anything you want, yet if you change any paths in the SVG and re-run
  the tool, this file is not overwritten and the paths are. So you can add symbols etc. safely here and still be able to
  use the visual editing power of Inkscape later on.

Output modes
------------
@todo

Example usage
=============
To illustrate how all this works, this extension comes with a sample file that contains the world's shittiest shirt
design in test_svgs\A0_full_design.svg . If you open this file in Inkscape, you'll see the layer setup, the 'metadata'
layer and the text element with id 'design-name' to set the name of the design and so on. Run the extension with this
test file and examine the output to get a feel for how things work.

Development notes
=================

- For development, you want to work straight from your git repo and not copy to the actual extensions directory. Just
  make a symlink from the extensions directory to the location of your git repo. If you're on Windows, do

    mklink /D to-freesewing-js d:\freesewing\to-freesewing-js\extension

- Open Inkscape from the command line like this:

    "c:\Program Files\Inkscape\bin\inkscapecom.com" test_svgs\simple.svg

Todo
====
- Make a second plugin that initializes the current document to be a FS template. Insert a sample layer, add a metadata
  layer, ...
- Convert markers and symbols somehow
- Add option to force-overwrite index.mjs and the part definition mjs files.
- Further split up the generated index.mjs and part definition code? Add generic 'hook' functions that allow for
  customization so that they themselves can more easily be overwritten?
- Add an option to export in a flatter directory structure. Needs some way to prevent name collisions. Or not and let
  the user figure it out.
- Add an option to export only paths, optionally from all layers. Would suit a more lightweight use case where you just
  want to draw a part and paste it into an existing design manually.
