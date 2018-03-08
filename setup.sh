## config
## needs root

# install
apt install -y Xorg mplayer

echo needs_roots_rights=yes >> /etc/X11/Xwrapper.config

## install videowall to /opt
cp -t /opt/videowall/ \
    mplay.py videowall.py load-videowall.sh
cp 60-videowall.rules /etc/udev/rules.d/

## autostart Xorg
# $USER_HOME needs to be in env. should be exported by node/run
# may need to address rotation
echo '[[ $(tty) = "/dev/tty1" ]] && exec Xorg' >> $USER_HOME/.bashrc
