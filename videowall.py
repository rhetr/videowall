#!/usr/bin/env python3
# videowall target_path config_path

import yaml
import subprocess
import os
import sys
import mplay

def get_matrix_size(values):
    return tuple(b + 1 for b in max(((a['pos'] for a in values))))

def make_cmd_mat(cmds, size):
    x, y = size
    cmd_mat = [[None] * y] * x
    for cmd in cmds:
        i, j = cmd['pos']
        cmd_mat[i][j] = cmd['cmd']
    return cmd_mat

def merge_node_cmd(cmd_mat, node):
    node['cmd'] = cmd_mat[node['pos'][0]][node['pos'][1]]
    return node

def rsync(ip, path):
    cmd = ('rsync', path, '{}:{}'.format(ip, path))
    print(cmd)
    # subprocess.call(cmd)

def remove_remote(ip, path):
    remote_cmd = "rm '{}'".format(path)
    cmd = ('ssh', ip, remote_cmd)
    subprocess.call(cmd)

def main(config, target=None):
    res = config['resolution']
    nodes = config['nodes']
    bcast = config['bcast']
    target = config['target'] if not target else target
    size = get_matrix_size(nodes.values())

    cmds = mplay.gen_videowall_cmds(target, size, res, bcast)
    cmd_mat = make_cmd_mat(cmds, size)
    nodes = (merge_node_cmd(cmd_mat, node) for node in nodes.values())
    active_nodes = [node for node in nodes if node['cmd']]

    for node in active_nodes:
        rsync(node['ip'], target)
        print('ssh', node['ip'], node['cmd'])
        # node['proc'] = subprocess.Popen(('ssh', node['ip'], cmd))

    master_cmd = ('mplayer', '-loop', '0', '-udp-master', '-udp-ip', bcast, target)
    print(' '.join(master_cmd))
    # subprocess.call(master_cmd)

    # # cleanup; called when mplayer is terminated
    # os.remove(target)
    for node in active_nodes:
        pass
        # node['proc'].terminate()
        # remove_remote(node['ip'], target)

if __name__ == '__main__':

    with open('config.yaml') as config_file:
        config = yaml.load(config_file)

    target = None if len(sys.argv) < 2 else sys.argv[1]
    if not os.path.isfile(target):
        print('invalid path')
        sys.exit(1)
    else:
        main(config, target)
