#!/usr/bin/env python3
# so ugly
# need to account for bezels
# bezel_x0
# bezel_y0
# bezel_y1
import subprocess
import json
import sys
import pprint

class Size:
    def __init__(self, w, h):
        self.w = int(w)
        self.h = int(h)
        self.ar = self.w/self.h
        

def get_screen_size():
    screen_geom = subprocess.check_output("xwininfo -root | grep geometry", shell=True).decode('utf-8').split(' ')[-1].split('x')

    screen_x = int(screen_geom[0])
    screen_y = int(screen_geom[1].split('+')[0])
    return Size(1440,900)
    #return Size(screen_x, screen_y)


def get_video_size(path):
    info = json.loads(subprocess.check_output('ffprobe -v quiet -print_format json -show_streams {}'.format(path), shell=True).decode('utf-8'))
    video_x = info['streams'][0]['coded_width']
    video_y = info['streams'][0]['coded_height']
    # return Size(716, 300)
    return Size(video_x, video_y)

# 
# bcast = '10.1.15.255'
# crop = '358:150:358:0'
# geometry = '0:297'
# scale = (1440, 603)

# size video
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
    wall = Size(video_w, video_h)
    wall.scale_x = wall.w / video.w
    wall.scale_y = wall.h / video.h
    return wall

def calc_display(screen, mon_rows, mon_cols):
    return Size(screen.w * mon_rows, screen.h * mon_cols)


def calc_screen_args(screen, wall, mon_x, mon_y, scale):
    # geometry is local to screen
    # crop is local to video (wall for now)
    # (uh ignore scale for now)
    screen_x0 = (screen.w * mon_x, screen.h * mon_y)
    screen_x1 = (screen.w * (mon_x+1), screen.h * (mon_y+1))
    geometry_x = 0
    geometry_y = 0

    
    crop_xpos = screen_x0[0] - wall.x0[0] 
    if screen_x0[0] < wall.x0[0]:  
        geometry_x = wall.x0[0]
        crop_w = screen_x1[0] - wall.x0[0]
        crop_xpos = 0
    elif screen_x1[0] > wall.x1[0]:
        crop_w = wall.x1[0] - screen_x0[0]
    else:
        crop_w = screen_x1[0] - screen_x0[0]

    crop_ypos = screen_x0[0] - wall.x0[0] 
    if screen_x0[1] < wall.x0[1]:
        geometry_y = wall.x0[1]
        crop_h = screen_x1[1] - wall.x0[1]
        crop_ypos = 0
    elif screen_x1[1] > wall.x1[1]:
        crop_h = wall.x1[1] - screen_x0[1]
    else: # screen_x1[1] < wall.x1[1]
        crop_h = screen_x1[1] - screen_x0[1]

    # scale is actually just straight up the width and height
    mplay_scale = (crop_w, crop_h)
    # crop_args = list(map(lambda x: int(x/scale), [crop_w,crop_h,crop_xpos,crop_ypos]))
    # crop = ':'.join(map(str, crop_args))
    crop = (
            crop_w,
            crop_h,
            crop_xpos,
            crop_ypos
            )
    return {
        'crop': crop,
        'geometry': (geometry_x, geometry_y),
        'scale': mplay_scale
    }

def center_wall(wall, display):
    w_disp = int( (display.w - wall.w) / 2 )
    h_disp = int( (display.h - wall.h) / 2 )
    wall.x0 = (w_disp, h_disp)
    wall.x1 = (display.w - w_disp, display.h - h_disp)
    return wall

def start_mplayer(bcast, crop, geometery, xscale, yscale, path):
    cmd = "DISPLAY=:0 mplayer -udp-slave -udp-ip {} -vf {} -geometry {} -x {} -y {} {}".format(bcast, crop, geometry, xscale, yscale, path)
    subprocess.call(cmd, shell=True)

def main(path, screen_rows, screen_cols):
    import tkinter
    tk = tkinter.Tk()
    h = tkinter.Scrollbar(tk, orient=tkinter.HORIZONTAL)
    v = tkinter.Scrollbar(tk, orient=tkinter.VERTICAL)
    canvas = tkinter.Canvas(tk, width=500,height=500)
    canvas.pack()

    screen = get_screen_size()
    video = get_video_size(path)
    print('screen size = {}x{}'.format(screen.w, screen.h))
    print('video size = {}x{}'.format(video.w, video.h))
    display = calc_display(screen, screen_rows, screen_cols)
    wall = calc_wall_size(display, video)
    wall = center_wall(wall, display)
    print('display size = {}x{}'.format(display.w, display.h))
    print('wall size = {}x{}; scale = {}x{}'.format(wall.w, wall.h, wall.scale_x, wall.scale_y))
    
    ofs = 20
    div = 10
    print('wall: ({},{}) to ({},{})'.format(wall.x0[0]+ofs,wall.x0[1]+ofs,wall.x1[0],wall.x1[1]))

    canvas.create_rectangle(0+ofs,ofs,display.w/div+ofs,display.h/div+ofs, width=2)
    canvas.create_rectangle(wall.x0[0]/div+ofs,wall.x0[1]/div+ofs,wall.x1[0]/div+ofs, wall.x1[1]/div+ofs, outline='red',width=2)

    # for j in range(screen_rows):
    #     for i in range(screen_cols):
    #         pprint.pprint('{},{}: {}'.format(i,j,calc_screen_args(screen, wall, i, j, wall.scale_x)))

    for j in range(screen_rows):
        for i in range(screen_cols):
            screen_ofs = (screen.w*j/div, screen.h*i/div)
            canvas.create_rectangle(
                    ofs+screen_ofs[0],
                    ofs+screen_ofs[1],
                    ofs+screen.w*(j+1)/div,
                    ofs+screen.h*(i+1)/div,
                    )
            res = calc_screen_args(screen, wall, j, i, wall.scale_x)
            if any((param < 0 for param in res['crop'])) \
                    or not good_bounds(res['geometry'], (screen.w, screen.h)):
                print('{},{}: no image'.format(j,i))
                continue

            s = pprint.pformat(res, indent=4)
            print('{},{}: {}'.format(j,i,s))

            canvas.create_rectangle(
                    ofs+screen_ofs[0]+res['geometry'][0]/div,
                    ofs+screen_ofs[1]+res['geometry'][1]/div,
                    ofs+screen_ofs[0]+res['geometry'][0]/div+10,
                    ofs+screen_ofs[1]+res['geometry'][1]/div+10
                    )
    tk.mainloop()

def good_bounds(geom, screen):
    for i in range(2):
        if geom[i] > screen[i]:
            return False
    return True

if __name__ == '__main__':
    # path, rows, columns = sys.argv[1:4]
    # main(path, int(rows), int(columns))
    main("cosmos.ogv", 3,5)
