#!/usr/bin/env python3
# so ugly

import subprocess
import json
import sys
import pprint

colors = ('green','blue','orange','yellow')

div = 16.0
    
class Rect:
    def __init__(self, pos=(0, 0), size=(0,0), parent=None):
        self.setPos(pos)
        self.setSize(size)
        self.setParent(parent)
    
    def setParent(self, rect):
        self.parent = rect

    def setPos(self, pos):
        self.pos = pos
        self.x = pos[0]
        self.y = pos[1]

    def setSize(self, size):
        self.size = size
        self.w = size[0]
        self.h = size[1]
        self.ar = self.w / self.h

def get_screen_rect():
    screen_geom = subprocess.check_output("xwininfo -root | grep geometry", shell=True).decode('utf-8').split(' ')[-1].split('x')

    screen_w = int(screen_geom[0])
    screen_h = int(screen_geom[1].split('+')[0])
    size = (screen_w, screen_h)
    size = (1080, 1920)
    size = tuple(s/div for s in size)
    return Rect(size=size)


def get_video_rect(path):
    info = json.loads(subprocess.check_output('ffprobe -v quiet -print_format json -show_streams {}'.format(path), shell=True).decode('utf-8'))
    video_w = info['streams'][0]['coded_width']
    video_h = info['streams'][0]['coded_height']
    size = (video_w, video_h)
    size = (1920/div, 1080/div)
    return Rect(size=size)

def calc_wall_size(display, video):
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

    wall = Rect(size=(video_w,video_h))
    return wall

def calc_display(screen, mon_rows, mon_cols, bezel = (0,0)):
    return Rect(size=
            (( bezel[0] + screen.w ) * mon_cols - bezel[0],
            ( bezel[1] + screen.h ) * mon_rows - bezel[1]))

def calc_vars(screen_size, mon_num, bezel_size, wall):
    s0 = (screen_size + bezel_size) * mon_num
    s1 = s0 + screen_size
    
    w0, w1 = wall
    crop_pos = s0 - w0 

    # print("{}->{}, {}->{}".format(s0,s1,w0,w1))
    if s1 < w0 or w1 < s0: # wall not in screen
        return (None, None, None)

    # lower bound
    if s0 < w0: # wall starts in screen
        win_pos = w0 - s0
    else: # w0 <= s0: wall starts before screen
        win_pos = 0

    # upper bound
    if s1 < w1: # wall ends after screen
        crop_size = s1 - max(w0,s0)
    else: # w1 <= s1: wall ends in screen
        crop_size = w1 - max(w0,s0)

    return (crop_pos, crop_size, win_pos)

def calc_transform(screen, wall, mon, bezel):
    mon_y, mon_x = mon
    # window_pos is local to screen
    # crop is local to video (wall for now)

    crop_xpos, crop_w, window_pos_x = calc_vars(
            screen.w, mon_x, bezel[0],
             (wall.x0[0],wall.x1[0]))
    crop_ypos, crop_h, window_pos_y = calc_vars(
            screen.h, mon_y, bezel[1],
             (wall.x0[1],wall.x1[1]))

    window = Rect(
            pos=(window_pos_x, window_pos_y),
            size=(crop_w, crop_h))
    crop = Rect(
            pos=(crop_xpos, crop_ypos),
            size=(crop_w,crop_h))
    return {
        'crop': crop,
        'window': window,
    }

def center_wall(wall, display):
    w_disp = int( (display.w - wall.w) / 2 )
    h_disp = int( (display.h - wall.h) / 2 )
    wall.x0 = (w_disp, h_disp)
    wall.x1 = (display.w - w_disp, display.h - h_disp)
    return wall

def start_mplayer(bcast, crop, window, path):
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
    crop_str = ':'.join(crop.size + crop.pos)
    
    cmd = "DISPLAY=:0 mplayer -udp-slave -udp-ip {} -vf {} -geometry {} -x {} -y {} {}".format(bcast, crop_str, window.pos, window.w, window.h, path)
    subprocess.call(cmd, shell=True)

def main(path, screen_rows, screen_cols):
    bezel = (5, 10)

    screen = get_screen_rect()
    video = get_video_rect(path)
    print('screen size = {}x{}'.format(screen.w, screen.h))
    print('video size = {}x{}'.format(video.w, video.h))
    display = calc_display(screen, screen_rows, screen_cols, bezel)
    wall = calc_wall_size(display, video)
    wall = center_wall(wall, display)
    print('display size = {}x{}'.format(display.w, display.h))
    print('wall size = {}x{}'.format(wall.w, wall.h))
    scale_x = wall.w / video.w
    scale_y = wall.h / video.h
    print('wall scale = {},{}'.format(scale_x, scale_y))
    print()
    
    ofs = 20

    import tkinter
    tk = tkinter.Tk()
    h = tkinter.Scrollbar(tk, orient=tkinter.HORIZONTAL)
    v = tkinter.Scrollbar(tk, orient=tkinter.VERTICAL)
    canvas = tkinter.Canvas(tk, width=700,height=500)
    canvas.pack()

    canvas.create_rectangle(
            ofs,
            ofs,
            ofs + display.w + bezel[0] * 2,
            ofs + display.h + bezel[1] * 2, 
            width=2)
    canvas.create_text(
            ofs,
            ofs,
            text="display", anchor="sw")

    canvas.create_rectangle(
            ofs + wall.x0[0] + bezel[0],
            ofs + wall.x0[1] + bezel[1],
            ofs + wall.x1[0] + bezel[0],
            ofs + wall.x1[1] + bezel[1],
            outline='red',width=2)
    canvas.create_text(
            ofs + wall.x0[0] + bezel[0],
            ofs + wall.x0[1] + bezel[1],
            text="wall", anchor="sw")


    for i in range(screen_rows):
        for j in range(screen_cols):
            # draw screens
            screen_ofs = (
                    ofs + j * (screen.w + bezel[0]) + bezel[0],
                    ofs + i * (screen.h + bezel[1]) + bezel[1])

            canvas.create_rectangle(
                    screen_ofs[0],
                    screen_ofs[1],
                    screen_ofs[0] + screen.w,
                    screen_ofs[1] + screen.h)

            canvas.create_text(
                    screen_ofs[0],
                    screen_ofs[1] + screen.h,
                    text="[{},{}]".format(i,j),
                    anchor='sw')

            # print('[{},{}]:'.format(i,j))
            res = calc_transform(
                    screen, 
                    wall, 
                    (i,j),
                    bezel)

            s = pprint.pformat(res, indent=4)
            
            color = colors[(j + i * screen_rows) % len(colors)]

            if res['window'].w == None \
                or res['window'].h == None:    
                continue
            canvas.create_rectangle(
                    screen_ofs[0] + res['window'].x,
                    screen_ofs[1] + res['window'].y,
                    screen_ofs[0] + res['window'].x + res['crop'].w,
                    screen_ofs[1] + res['window'].y + res['crop'].h,
                    outline=color, width=3)

            # canvas.create_text(
            #         screen_ofs[0] + res['window_pos'][0],
            #         screen_ofs[1] + res['window_pos'][1],
            #         text="[{},{}]".format(j,i))
    tk.mainloop()

if __name__ == '__main__':
    # path, rows, columns = sys.argv[1:4]
    # main(path, int(rows), int(columns))
    main("cosmos.ogv", 2, 4)
