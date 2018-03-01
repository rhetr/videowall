## config
## needs root

# install
apt install -y Xorg mplayer

## might not need these
# apt install -y xinit x11-xserver-utils xserver-xorg-legacy

echo needs_roots_rights=yes >> /etc/X11/Xwrapper.config

## install videowall to /opt
cp -t /opt/videowall/ \
    mplay.py videowall.py load-videowall.sh
cp 60-videowall.rules /etc/udev/rules.d/

## autostart Xorg

## USERNAME and USER_HOME should be exported by node/run
# USERNAME=perry
# USER_HOME=/home/$USERNAME
echo '[[ $(tty) = "/dev/tty1" ]] && exec Xorg' >> $USER_HOME/.bashrc
