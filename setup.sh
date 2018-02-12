## config

# install
apt install -y Xorg mplayer
# might not need these
apt install -y xinit x11-xserver-utils xserver-xorg-legacy

## setup startup
# echo needs_roots_rights=yes > /etc/X11/Xwrapper.config
# autologin and start xserver


# add controller to xhost
# DISPLAY=:0 xhost +


## run
# prepare slaves
