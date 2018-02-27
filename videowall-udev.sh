#!/bin/bash


if [[ $ACTION = "add" ]]; then
    echo $(date) adding >> /tmp/videowall-udev
    mkdir -p /media/videowall-target
    mount /dev/videowall-target /media/videowall-target
    echo $(date) MOUNTED EYOOOO >> /tmp/videowall-udev
    umount /media/video
    echo $(date) UNMOUNTED EYOOOO >> /tmp/videowall-udev
elif [[ $ACTION = "remove" ]]; then
    echo $(date) DEV REMOVE >> /tmp/videowall-udev
fi
