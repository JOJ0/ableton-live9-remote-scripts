# J0J0's AKAI APC mini Ableton Controller hacks

I did some customizations on the Ableton Live 9 MIDI Remote Script for the [AKAI APC mini](http://www.akaipro.com/product/apc-mini)
My work is based on [phs' fork of the Ableton Live 9 MIDI remote scripts](https://github.com/phs/ableton-live9-remote-scripts), he did some customizations and code cleanup in the APCmini script. I learned a lot from his code and his words! Thanks again for that! 

## Version 0.2

### Features
 * added a "Session Overview" feature that is common with APC controllers, I adapted the code from [midiscripts.net](http://midiscripts.net/apc-mini-session-overview-midi-script-for-ableton-live-free/), you also find a video demonstrating the feature there. 
 * changed behaviour of "scene launch buttons" (buttons on right edge of controller):
  * scenes are now launched using shift + scene launch button
  * modes (stop/solo/rec/arm/mute/select/overview/stopall) are selected without shift button. Also you see what mode is currently active without holding shift (corresponding button is lit green)!

### Issues
 * currently only working with Ableton Live 9.6.1
 * StopAll could be accidently hit when launching scene 8
 * Overwiew Button (6) is always lit (actually I kind of like that, maybe not an issue?)

### Stuff to come
 * make compatible with Live 9.6.2 or even better with Abletons new v2 API (thanks to midiscripts.net for the hint!)
 * adapt phs' code for having a "Drum Rack" mode, pretty sure velocity sensitivity is not possible, but should be enough for jamming in some sliced breakbeats!

### Installation
 * If you are not familiar with git and commandlines then download this zip file [APC_mini_jojo.zip](APC_mini_jojo.zip)
  * copy the directory APC_mini_jojo to Live's "MIDI Remote Scripts" directory, if you have Suite on a Mac this usually is /Applications/Ableton Live 9 Suite/Contents/App-Resources/MIDI Remote Scripts/
  * also check official Ableton Documentation: ["How to install a third-party Remote Script?"](https://help.ableton.com/hc/en-us/articles/209072009) 
  * Select the controller in MIDI Settings as usual, it's called "APC mini jojo"
  * Certainly you can always go back and select the default controller script "APC mini" again
 * If you know how to use git, just clone my repo and have a look in the shell script to9.6.1.sh, it quick & dirty copies relevant stuff from repo to your Ableton scripts dir, if there is a new version you could update easily using the script. You have to adjust the paths to your installation first! It also cleans up \*.pyc files.

If you only want the "Session Overview" feature without my "Shift + Scene Buttons" changes, then download midiscripts.net version here: [APC MINI SESSION OVERVIEW (FREE)](http://midiscripts.net/apc-mini-session-overview-midi-script-for-ableton-live-free/)
They have versions for Live 9.6.1 and 9.6.2!
