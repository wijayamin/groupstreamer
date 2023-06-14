#!/usr/bin/env python3

import asyncio, os, regex_spm, subprocess, multiprocessing, time
from cameractrls.cameractrls import CameraCtrls
from udp_server import start_udp_servers


class UVC:
    def __init__(self, device):
        self.device = device
        self.camera = None
        self.ctrls = {}
        self.read_control()

    def read_control(self):
        fd = os.open(self.device, os.O_RDWR, 0)
        self.camera = CameraCtrls(self.device, fd)
        for page in self.camera.get_ctrl_pages():
            for cat in page.categories:
                for c in cat.ctrls:
                    if c.type in ['integer', 'boolean']:
                        self.ctrls.update({
                            c.text_id:{
                                'type': c.type,
                                'value': c.value,
                                'default': c.default,
                                'min': c.min,
                                'max': c.max,
                                'step': c.step,
                            }
                        })
                    elif c.type == 'menu':
                        self.ctrls.update({
                            c.text_id:{
                                'type': c.type,
                                'value': c.value,
                                'default': c.default,
                                'values': [m.text_id for m in c.menu]
                            }
                        })
                    elif c.type == 'info':
                        self.ctrls.update({
                            c.text_id:{
                                'type': c.type,
                                'value': c.value
                            }
                        })

    def zoom_tele(self, speed=0):
        self.read_control()
        zoom = self.ctrls['zoom_absolute'] if 'zoom_absolute' in self.ctrls else None
        speed_increments=[5, 20, 35, 50, 65, 80, 95, 100]
        if zoom:
            new_zoom = min(zoom['value']+speed_increments[speed], zoom['max'])
            self.camera.setup_ctrls({'zoom_absolute': new_zoom})

    def zoom_wide(self, speed=0):
        self.read_control()
        zoom = self.ctrls['zoom_absolute'] if 'zoom_absolute' in self.ctrls else None
        speed_decrements=[5, 20, 35, 50, 65, 80, 95, 100]
        if zoom:
            new_zoom = max(zoom['value']-speed_decrements[speed], zoom['min'])
            self.camera.setup_ctrls({'zoom_absolute': new_zoom})

    def pan_tilt_stop(self):
        self.read_control()
        if 'pan_speed' in self.ctrls:
            self.camera.setup_ctrls({'pan_speed': 0})
        if 'tilt_speed' in self.ctrls:
            self.camera.setup_ctrls({'tilt_speed': 0})

    def pan_left(self):
        self.read_control()
        if 'pan_speed' in self.ctrls:
            self.camera.setup_ctrls({'pan_speed': -1})

    def pan_right(self):
        self.read_control()
        if 'pan_speed' in self.ctrls:
            self.camera.setup_ctrls({'pan_speed': 1})

    def tilt_stop(self):
        self.read_control()
        if 'pan_speed' in self.ctrls:
            self.camera.setup_ctrls({'tilt_speed': 0})

    def tilt_up(self):
        self.read_control()
        if 'pan_speed' in self.ctrls:
            self.camera.setup_ctrls({'tilt_speed': -1})

    def tilt_down(self):
        self.read_control()
        if 'pan_speed' in self.ctrls:
            self.camera.setup_ctrls({'tilt_speed': 1})

    def pan_tilt_home(self):
        self.read_control()
        if 'logitech_pantilt_reset' in self.ctrls:
            self.camera.setup_ctrls({'logitech_pantilt_reset': 'both'})
            

class VISCA:
    def __init__(self):
        self.message = []
        self.uvc = UVC('/dev/video1')
        self.process = None

    def parse(self, data):
        message = data.hex(' ')
        self.message = message.split()
        match regex_spm.fullmatch_in(message):
            case r'01 00 00 .. .. .. .. .. 81 01 04 07 2. ff': self.zoom_tele()
            case r'01 00 00 .. .. .. .. .. 81 01 04 07 3. ff': self.zoom_wide()
            case r'01 00 00 .. .. .. .. .. 81 01 04 07 00 ff': self.zoom_stop()
            case r'01 00 00 .. .. .. .. .. 81 01 06 01 .. .. 03 03 ff': self.pan_tilt_stop()
            case r'01 00 00 .. .. .. .. .. 81 01 06 01 .. .. 01 03 ff': self.pan_left()
            case r'01 00 00 .. .. .. .. .. 81 01 06 01 .. .. 02 03 ff': self.pan_right()
            case r'01 00 00 .. .. .. .. .. 81 01 06 01 .. .. 03 01 ff': self.tilt_up()
            case r'01 00 00 .. .. .. .. .. 81 01 06 01 .. .. 03 02 ff': self.tilt_down()
            case r'01 00 00 .. .. .. .. .. 81 01 06 04 ff': self.tilt_down()
            
    def zoom_tele(self):
        speed = int(self.message[12][1])
        def zoom(self, speed):
            while True:
                # print(speed)
                self.uvc.zoom_tele(speed)
                time.sleep(0.8)
        self.process = multiprocessing.Process(target=zoom, args=(self, speed,))
        self.process.start()
            
    def zoom_wide(self):
        speed = int(self.message[12][1])
        def zoom(self, speed):
            while True:
                # print(speed)
                self.uvc.zoom_wide(speed)
                time.sleep(0.8)
        self.process = multiprocessing.Process(target=zoom, args=(self, speed,))
        self.process.start()

    def zoom_stop(self):
        self.process.terminate()
        self.process.join()

    def pan_tilt_stop(self):
        self.uvc.pan_tilt_stop()

    def pan_left(self):
        self.uvc.pan_left()

    def pan_right(self):
        self.uvc.pan_right()

    def tilt_up(self):
        self.uvc.tilt_up()

    def tilt_down(self):
        self.uvc.tilt_down()

    def pan_tilt_reset(self):
        self.uvc.pan_tilt_home()

visca = VISCA()
# Define the callback function to handle received data
def handle_data(data, addr, send_response):
    visca.parse(data)
    print(data.hex(' '))
    send_response(data, addr)

async def run_servers():
    await start_udp_servers(handle_data)

command = "ustreamer -d /dev/video1 -r 1920x1080 -m MJPEG -f 30 -c HW --image-default --slowdown -s 0.0.0.0"
process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# Run the UDP servers
asyncio.run(run_servers())
