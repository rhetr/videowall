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

def main(target, config):
    res = config['resolution']
    nodes = config['nodes']
    size = get_matrix_size(nodes.values())

    # mplay should generate
    # [ { pos: (0,0),
    #   cmd: cmd },
    #   ... ]
    cmds = mplay.gen_videowall_cmds(target, size, res, True)

    # need ssh key
    for node in nodes.values():
        ip = node['ip']
        cmd = get_cmd_by_pos(cmds, node)
        if cmd:
            print('ssh', ip, cmd)
        # subprocess.Popen(['ssh', ip, cmd])

if __name__ == '__main__':

    videowall_dir = '/tmp/videowall'
    target_dir = os.path.join(videowall_dir, 'target')

    # can fail
    # target = os.listdir(target_dir)[0]

    target = 'cosmos.ogv'
    with open('config.yaml') as config_file:
        config = yaml.load(config_file)

    main(target, config)
