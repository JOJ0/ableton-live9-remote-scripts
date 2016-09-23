# J0J0's "Akai APC mini" Ableton Live Controller Hacks

I did some customizations in the Ableton Live 9 MIDI Remote Script for the [Akai APC mini](http://www.akaipro.com/product/apc-mini).
My work is based on [phs' fork of the Ableton Live 9 MIDI remote scripts](https://github.com/phs/ableton-live9-remote-scripts), he did some customizations and code cleanup in the APC mini script. I learned a lot from his code and his words! Thanks again! 

## Version 0.2

### Features
 * Added a "Session Overview" feature that is common with APC controllers, I adapted the code from [midiscripts.net](http://midiscripts.net/apc-mini-session-overview-midi-script-for-ableton-live-free/), you also find a video demonstrating the feature there (be aware of that in my version you activate the overview with just Button 6, as described below) 
 * Changed behaviour of Scene-Launch-Buttons (buttons on right edge of controller):
  * Scenes are now launched using Shift + Scene-Launch-Button
  * The Soft-Key functions instead, which select the different modes (Clip-Stop/Solo/Rec-Arm/Mute/Select/Overview/Stop-All-Clips), work without the Shift button. Now you also are able to see what mode is currently active (corresponding button is lit green), without having to press Shift! For me personally this fixes the most annoying misconception on this controller.

### Issues
 * Currently only works with Ableton Live 9.6.1
 * Stop-All-Clips could be accidently hit when launching Scene 8 (Shift + Scene 8 Button) 
 * Overwiew Button (6) is always lit (actually I kind of like that, maybe not an issue?)

### Stuff to come
 * Make compatible with Live 9.6.2 or even better with Abletons new v2 API (thanks to midiscripts.net for the hint!)
 * Adapt phs' code for having a "Drum Rack" mode, pretty sure velocity sensitivity is not possible, but should be enough for jamming out some sliced breakbeats!
 * When soloing tracks, button should be lit grin instead of red, not sure if this can be done with the LEDs on the Hardware

### Installation
 * If you are not familiar with git and commandlines then download this zip file [APC_mini_jojo.zip](APC_mini_jojo.zip)
  * Copy the directory APC_mini_jojo to Live's "MIDI Remote Scripts" directory, if you have Suite on a Mac this usually is /Applications/Ableton Live 9 Suite.app/Contents/App-Resources/MIDI Remote Scripts/
  * Also check official Ableton Documentation: ["How to install a third-party Remote Script?"](https://help.ableton.com/hc/en-us/articles/209072009) 
  * Select the controller in MIDI Settings as usual, it's called "APC mini jojo"
  * Certainly you can always return to using the default controller script by selecting "APC mini" again
 * If you know how to use git, just clone my repo and have a look in the shell script to9.6.1.sh, it quick & dirty copies relevant stuff from repo to your Ableton scripts dir, if there is a new version you could update easily using the script. You have to adjust the paths to your installation first! It also cleans up \*.pyc files, which is handy when you code and test.

If you only want the "Session Overview" feature without my "Shift + Scene-Launch-Buttons" changes, then download midiscripts.net version here: [APC MINI SESSION OVERVIEW (FREE)](http://midiscripts.net/apc-mini-session-overview-midi-script-for-ableton-live-free/).
They have versions for Live 9.6.1 and 9.6.2!
