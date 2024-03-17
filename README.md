This is an extension for Inkscape that will export the document's SVG to Javascript code to reproduce the document's
design as a [FreeSewing](http://freesewing.org) design, using the the FreeSewing Javascript API. This is a convenience
tool to digitize sewing patterns. Trace or design them in Inkscape, export using this extensions, then copy/paste the output
to your FreeSewing design's draft() method or have this extension generate the complete design code structure for you.
You will need to fix up coordinates to make them use FreeSewing measurements manually, of course; this is not and likely
never will be a complete replacement for programming a FreeSewing design. Most notably, support for including
measurements in your Inkscape design is very limited.

Installation
============

- Download by clicking 'Code' on Github and then selecting 'Download ZIP'
- Extract the zip somewhere
- Make a directory called 'to-freesewing-js' in your Inkscape extensions path. You can find out where that is by looking
  (in Inkscape) under Edit/Preferences/System/User extensions.
- Copy the contents of the directory 'extension' in what you just unzipped to the directory you just made.
- You will need to restart Inkscape (if you still have it open) before the new extension is picked up.
- Start Inkscape. Under 'Extensions', you will see a menu called 'FreeSewing', which has an entry 'Export to FreeSewing
  JS...'.

User manual
===========

Marking up your SVG
-------------------

In order to be able to generate valid code for a FreeSewing design, the extension needs to know things like what element
in your SVG make up what parts, what is the name of the design etc. How you let it those things know is as follows:

- The design name is derived from a text object with the label 'design-name' in a layer called 'metadata'. Insert this
  layer and element into your document so that the generated code can use the correct design name where it needs it. You
  can make this layer invisible if it's in your way.

- The only curves and lines that are exported, are the ones in layers with a name that starts with 'part:' and then a
  name for your part. So you 'define' a part called 'back' by putting in a layer called 'part: back' and then putting
  all lines and curves that make up the shape of this part in that layer.

- The part names are derived from whatever is after the 'part:' in the layer's Label, as described above; the individual
  path names however are derived from their ID. You may want to change the ID to be the same as the Label for your
  paths, as this will make it easier to find back in the code what paths you're looking at and to make the link between
  what you see in your SVG in Inkscape and what you see in FreeSewing. However, these ID's have to be unique, and you
  will have to manage their names manually. So you can't have a layer with ID 'front' and then also have a path inside
  that layer with that same ID 'front'. You'll likely want to name only your path 'front', as that is what will show up
  in your generated code. You still may want to give your layer a descriptive ID though, say 'layer\_front', just for
  consistency and finding your way around easily.

  This naming is not important from a technical point of view, it will work regardsless of the
  path being called 'path1' or 'front'. But it is best practice to have good data hygiene and use accurate and
  descriptive ID's for your paths, as these will translate into accurate and descriptive variable names in your
  FreeSewing code. Other people and your future self will thank you.

- Path styling is ignored. So what color, line style etc. you use for your paths is irrelevant for the generated code.

What is generated
-----------------

When you run the extension from the 'Extensions' menu under 'FreeSewing', you'll see a dialog that has a dropdown box
where you can choose 'Export what'. What you select here, depends on how the extension works. If you select 'All, as a
complete design', it will generate a complete design, including the design definition, part definition etc. Use this
when you're traced a paper design or designed a complete design and want to convert it completely to a FreeSewing
design. If you select "Selection, path to clipboard", the extension will take the object that are selected in Inkscape
and copy only the code required to draw those paths in FreeSewing to your clipboard. Use this when you want to quickly
iterate on a single part design and already have all code that ties things together in a FreeSewing development
environment.

The following is only relevant if you choose 'All, as a complete design'.

The extension will let you select a design directory in the 'Design directory' text box. Choose the root directory of
your design there, meaning the one that contains the 'src' and 'i18n' directories. If those don't exist yet they'll be
created for you, but this way you can also use a design that was already made through the regular methods as documented
in the FreeSewing documentation (i.e. the 'yarn new design' process). When you click 'Apply', a number of files are
written to that directory:

- src\index.mjs. This file is only created if it doesn't exist yet; if it exists, it's not overwritten, so it's safe to
  modify this file and run the extension export again. This file contains the definition of the design, i.e. metadata
  like its name, and what parts it's composed of. If you add parts to your design, you may have to manually edit this
  file, or delete it before running the extension, then re-applying any changes (like measurements) you made to it
  before.
- For each part (see above how those are defined): src\parts\\[part name]\\[part name].mjs . Again, this file is not
  overwritten if it already exists and the same caveats apply as for index.mjs. This file draws the actual part. It does
  so in 'chunks' by calling out to other functions that actually draw the lines and curves, i.e. per path that was found
  in the svg. This way, you can manually customize anything you want in the design or part configuration, yet if you
  change any paths in the SVG and re-run the extension, this file is not overwritten and the paths are. So you can add
  annotations etc. safely here and still be able to use the visual editing power of Inkscape later on for the actual
  part paths.
- For each path of each part: src\parts\\[part name]\\paths\\[path name].mjs . These will be overwritten if they already
  exist. This has the actual code to draw paths.

Note that if you write to an existing design's directory, index.mjs and maybe parts\\[part name].mjs will likely already
exist; the references (paths and variable names) in them may change depending on what's in your SVG. Best practice if
you use an existing design is to have it version controlled and committed before you run the extension, then after you
run it check which files are new and which ones have changed, and examine any changes so you understand what's going on.

To re-iterate, by physically splitting the path defintions from the design and part definitions, you can modify the
design and part without it being overwritten when the extension is re-run. This code structure has additional levels compared
to the standard 'all parts are found in the same src folder' structure that is set up by the FreeSewing 'new design'
tools. This allows the converter to update code as needed when you run the plugin again. The index.mjs file that is
generated by the extension already takes this alternative structure into account. If you run the extension for an
existing design, you may need to update paths to make things work. It helps to first run the extension into an empty
directory, then into your existing design's directory, and then compare the generated index.mjs files.

Output modes
------------
@todo

Example usage
=============
To illustrate how all this works, this extension comes with a sample file that contains the world's shittiest shirt
design in example\_svgs\examplar\_shirt.svg . If you open this file in Inkscape, you'll see the layer setup, the 'metadata'
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
- Add the .class('fabric') stuff somehow from path properties.
- Clean up newline generation in generated point/path code; right now where there are newlines at the start/end of
  blocks isn't perfectly consistent. Also come up with a way to specify how indentation is generated, and make that
  consistent throughout the templates.
