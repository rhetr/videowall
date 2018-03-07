#!/usr/bin/env python3
# videowall target_path config_path

import yaml
import subprocess
import os
import sys
import mplay

def get_matrix_size(values):
    return tuple(b + 1 for b in max(((a['pos'] for a in values))))

def get_cmd_by_pos(cmds, node):
    for cmd in cmds:
        if cmd['pos'] == tuple(node['pos']):
            return cmd['cmd']

def main(config, target=None):
    res = config['resolution']
    nodes = config['nodes']
    bcast = config['bcast']
    if not target:
        target = config['target']
    size = get_matrix_size(nodes.values())

    cmds = list(mplay.gen_videowall_cmds(target, size, res, bcast))

    for node in nodes.values():
        ip = node['ip']
        cmd = get_cmd_by_pos(cmds, node)
        if cmd:
            print('ssh', ip, cmd)
            # need ssh key
            # subprocess.Popen(['ssh', ip, cmd])
    # master command
    master_cmd = ('mplayer', '-loop', '0', '-udp-master', '-udp-ip', bcast, target)
    print(' '.join(master_cmd))

if __name__ == '__main__':

    # videowall_dir = '/tmp/videowall'
    # target_dir = os.path.join(videowall_dir, 'target')
    # # can fail
    # target = os.listdir(target_dir)[0]

    with open('config.yaml') as config_file:
        config = yaml.load(config_file)

    main(config)
