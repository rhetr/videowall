#!/bin/bash

DEV=/dev/videowall-src
SRC_DIR=/media/videowall-src
VIDEOWALL_DIR=/tmp/videowall
TARGET_DIR=$VIDEOWALL_DIR/target


if [[ $ACTION = "add" ]]; then
    mkdir -p $SRC_DIR
    mkdir -p $TARGET_DIR

    echo $(date) mounting >> $VIDEOWALL_DIR/log
    mount $DEV $SRC_DIR
    SRC=$(ls $SRC_DIR)
    if [[ "$SRC" = "" ]]; then
	echo 'nothing to play'
	exit 1
    fi 
    BASENAME=$(basename "$SRC")
    TARGET="$TARGET_DIR/$BASENAME" 

    # copy file to tmp dir
    echo $(date) rsyncing >> $VIDEOWALL_DIR/log
    rsync -a "$SRC" "$TARGET"

    # unmount drive BUT KEEP THE DRIVE IN
    echo $(date) ummounting >> $VIDEOWALL_DIR/log
    umount $DEV

    # run it

elif [[ $ACTION = "remove" ]]; then
    echo $(date) DEV REMOVE >> $VIDEOWALL_DIR/log
fi
