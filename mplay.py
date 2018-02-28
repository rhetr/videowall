#!/usr/bin/env python3
# so ugly

import subprocess
import json
import sys
    
class Rect:
    def __init__(self, pos=(0, 0), size=(0,0), parent=None):
        self.setSize(size)
        self.setPos(pos)
        self.setParent(parent)
    
    def setParent(self, rect):
        self.parent = rect

    def setPos(self, pos):
        self.pos = tuple(pos)
        self.x, self.y = self.pos
        self.x1 = (self.x + self.w, self.y + self.h)
        # print('setpos',self.x+self.w, self.y+self.h)

    def setSize(self, size):
        self.size = tuple(size)
        self.w, self.h = self.size
        self.ar = self.w / self.h if self.h else None

def xpdyinfo(prop):
    return tuple( map( int,
                list( filter( None,
                        subprocess.check_output('xdpyinfo | grep {}'.format(prop), shell=True)
                        .decode().split(' '))
                    )[1].split('x')
                ))


def get_screen_rect(res = None):
    if not res:
        res = xpdyinfo('dimensions')
        ppi = xpdyinfo('resolution')
        print(size)
        # size = (1080, 1920)
        res = (1440, 900)

    return Rect(size = res)


def get_video_rect(path):
    cmd = [ 'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            path ]
    # info = json.loads(subprocess.check_output(cmd).decode())
    # video_w = info['streams'][0]['coded_width']
    # video_h = info['streams'][0]['coded_height']
    # size = (video_w, video_h)
    size = (1920, 1080)
    # size = (640,480)
    return Rect(size=size)

def get_wall_rect(display, video):
    if display.ar > video.ar:
        # vertical letterboxing; size v.h to display.h
        video_w = int( display.h / video.h * video.w )
        video_h = display.h
        
    elif display.ar < video.ar:
        # horizontal letterboxing; size v.w to display.w
        video_h = int( display.w / video.w * video.h )
        video_w = display.w
    else:
        # they're the same
        video_w = display.w
        video_h = display.h

    return Rect(size=(video_w,video_h))

def center_wall(wall, display):
    w_disp = int( (display.w - wall.w) / 2 )
    h_disp = int( (display.h - wall.h) / 2 )

    x0 = (w_disp, h_disp)
    wall.setPos(x0)
    return wall

def calc_display(screen, mon_rows, mon_cols, bezel = (0,0)):
    return Rect(size=
            (( bezel[0] + screen.w ) * mon_cols - bezel[0],
            ( bezel[1] + screen.h ) * mon_rows - bezel[1]))

def calc_win_vars(s0, s1, w0, w1):
    if s1 < w0 or w1 < s0: # wall not in screen
        win_size = None
        win_pos = None
        # return (None, None)
    else:
        if s0 < w0: # wall starts in screen
            win_pos = w0 - s0
        else: # w0 <= s0: wall starts before screen
            win_pos = 0

        if s1 < w1: # wall ends after screen
            win_size = s1 - max(w0,s0)
        else: # w1 <= s1: wall ends in screen
            win_size = w1 - max(w0,s0)

    return (win_size, win_pos)

def calc_crop_vars(screen_pos_g, win_pos_l, win_size, wall_pos_g, scale):
    crop_pos = (screen_pos_g + win_pos_l - wall_pos_g) / scale
    crop_size = win_size / scale
    return (crop_size, crop_pos)

def calc_transform(video, screen, wall, mon_index, bezel):
    scale = wall.w / video.w
    win_size = [0,0]
    win_pos = [0,0]

    crop_size = [0,0]
    crop_pos = [0,0]

    for i in range(2):
        w0, w1 = (wall.pos[i], wall.x1[i])
        s0 = (screen.size[i] + bezel[i]) * mon_index[i]
        s1 = s0 + screen.size[i]

        win_size[i], win_pos[i] = calc_win_vars(s0, s1, w0, w1)

        if win_size[i] == None:
            return None

        crop_size[i], crop_pos[i] = calc_crop_vars(s0, win_pos[i], win_size[i], wall.pos[i], scale)


    window = Rect(
            pos = map(round, win_pos),
            size = map(round, win_size))

    crop = Rect(
            pos = map(round, crop_pos),
            size = map(round, crop_size))

    return {
        'index': mon_index[::-1],
        'crop': crop,
        'window': window
    }

def gen_mplayer_cmd(bcast, crop, window, path):
    '''
    bcast : broadcast address, maybe 10.1.15.255
    crop : Rect, in original video resolution + coordinates (formatted w:h:x:y)
    crop.pos : (x, y) 
    crop.size : (w, h)
    window : Rect of mplayer window
    window.pos : x:y, pixel location of mplayer in screen coordinates
    window.size : (w, h) size of mplayer window, automatically scaled
    path : obvious
    '''
    crop_str = ':'.join(map(str, crop.size + crop.pos))

    
    cmd = "DISPLAY=:0 mplayer -udp-slave -udp-ip {} -vf crop={} -geometry {}:{} -x {} -y {} {}".format(bcast, crop_str, window.x, window.y, window.w, window.h, path)
    return cmd
    #subprocess.call(cmd, shell=True)

def gen_videowall_cmds(path, size, res = None, draw = False):
    screen_rows, screen_cols = size
    bezel = (100, 100)

    screen = get_screen_rect(res)
    video = get_video_rect(path)
    display = calc_display(screen, screen_rows, screen_cols, bezel)
    wall = get_wall_rect(display, video)
    wall = center_wall(wall, display)
    scale_x = wall.w / video.w
    scale_y = wall.h / video.h

    print('screen size = {}x{}'.format(screen.w, screen.h))
    print('video size = {}x{}'.format(video.w, video.h))
    print('display size = {}x{}'.format(display.w, display.h))
    print('wall size = {}x{}'.format(wall.w, wall.h))
    print('wall scale = {},{}'.format(scale_x, scale_y))
    print()
    
    results = (
            calc_transform(video, screen , wall, (j,i), bezel)
            for j in range(screen_cols)
            for i in range(screen_rows)
            )

    results = list(filter(None, results))

    final = []
    for res in results:
        cmd = gen_mplayer_cmd('10.1.15.255', res['crop'], res['window'], path)
        # print("{}: {}".format(res['index'], cmd))
        final.append({'pos': res['index'], 'cmd': cmd})

    if draw:
        draw_result(display, wall, screen, bezel, size, results)

    return final


def draw_result(display, wall, screen, bezel, size, results):
    screen_rows, screen_cols = size
    import tkinter
    tk_scale = 0.2
    tk_ofs = 20/tk_scale
    colors = ('green','blue','orange','yellow')

    tk = tkinter.Tk()
    canvas = tkinter.Canvas(tk, width=700,height=500)
    canvas.pack(fill=tkinter.BOTH, expand=tkinter.YES)

    # display
    canvas.create_rectangle(
            tk_ofs,
            tk_ofs,
            tk_ofs + display.w + bezel[0] * 2,
            tk_ofs + display.h + bezel[1] * 2,
            width=2)
    canvas.create_text(
            tk_ofs,
            tk_ofs,
            text="display", anchor="sw")

    # wall
    canvas.create_rectangle(
            tk_ofs + wall.pos[0] + bezel[0],
            tk_ofs + wall.pos[1] + bezel[1],
            tk_ofs + wall.x1[0] + bezel[0],
            tk_ofs + wall.x1[1] + bezel[1],
            outline='red',width=2)
    canvas.create_text(
            tk_ofs + wall.pos[0] + bezel[0],
            tk_ofs + wall.pos[1] + bezel[1],
            text="wall", anchor="sw")

    for i in range(screen_rows):
        for j in range(screen_cols):
            tk_screen_ofs = (
                    tk_ofs + j * (screen.w + bezel[0]) + bezel[0],
                    tk_ofs + i * (screen.h + bezel[1]) + bezel[1])

            canvas.create_rectangle(
                    tk_screen_ofs[0],
                    tk_screen_ofs[1],
                    tk_screen_ofs[0] + screen.w,
                    tk_screen_ofs[1] + screen.h)

            canvas.create_text(
                    tk_screen_ofs[0],
                    tk_screen_ofs[1] + screen.h,
                    text="[{},{}]".format(i,j),
                    anchor='sw')

    for res in results:
        i, j = res['index']
        tk_screen_ofs = (
                tk_ofs + j * (screen.w + bezel[0]) + bezel[0],
                tk_ofs + i * (screen.h + bezel[1]) + bezel[1])

        color = colors[(j + i * screen_rows) % len(colors)]
        canvas.create_rectangle(
                tk_screen_ofs[0] + res['window'].x,
                tk_screen_ofs[1] + res['window'].y,
                tk_screen_ofs[0] + res['window'].x + res['window'].w,
                tk_screen_ofs[1] + res['window'].y + res['window'].h,
                outline=color, width=3)

    canvas.scale("all", 0, 0, tk_scale, tk_scale)
    tk.mainloop()


if __name__ == '__main__':
    # path, rows, columns = sys.argv[1:4]
    # main(path, int(rows), int(columns)) 
    gen_videowall_cmds("cosmos.ogv", (2, 2), [1920, 1080], True)
