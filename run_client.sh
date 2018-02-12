

MASTER=''
SRC=''
DEST=''

BCAST=10.1.15.255

rsync $TARGET Videos/

mplayer -udp-slave -udp-ip $BCAST "$DEST"

