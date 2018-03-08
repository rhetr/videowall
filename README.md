# videowall
## what it do, when it did
calculates crop/scale/window position parameters given a matrix of screens and an input video, then plays it.

## assumptions
- screens are the same size and resolution
- screens are arranged in a 2d matrix
- usb drive has a single video file on it that is playable by mplayer

## dependencies
- mplayer
- rsync
### master dependencies (includes above)
- python3
- ffmpeg/ffprobe
- xdpyinfo

## run loop
### on usb attach
1. udev:
	1. mounts to /mnt
	2. copy video to /tmp
	3. umount 
	4. run videowall
2. videowall:
	1. reads config.yaml to determine screen layout and resolution
	2. rsyncs video to slaves
	3. generates slave commands and calls them via ssh
	4. loop video on master
	 
### on usb detach
1. udev stops mplayer
2. videowall:
	1. remove video on master
	2. terminate slave processes (to be sure)
	3. remove video on slaves
