#!/usr/bin/env python2

import pygame
import pygame.camera
from pygame.locals import *
import time
import subprocess

pygame.init()
pygame.camera.init()


class Capture(object):
    def __init__(self):
        self.camera_size = (2304, 1536)
        #self.camera_size = (1920, 1080)
        self.resolution = (1920, 1080)
        self.img_path = "img/"
        self.start_cams(self.camera_size)
        # setup display
        self.display = pygame.display.set_mode(self.resolution, 0)
        # create a surface to capture to.  for performance purposes
        # bit depth is the same as that of the display surface.
        self.snapshots = [pygame.surface.Surface(self.camera_size, 0, self.display)
                         for i in self.cams]
        countdown = 0
        # calculate preview size
        self.font = pygame.font.Font(pygame.font.get_default_font(),72)
    def start_cams(self, size):
        #self.clist = pygame.camera.list_cameras()
        self.clist = [
            "/dev/v4l/by-id/usb-046d_Logitech_Webcam_C930e_B94D036E-video-index0",
            "/dev/v4l/by-id/usb-046d_Logitech_Webcam_C930e_BBAD036E-video-index0",
            "/dev/v4l/by-id/usb-046d_Logitech_Webcam_C930e_AB29F26E-video-index0"
        ]
        self.cams = []
        for i in self.clist:
            try:
                cam = pygame.camera.Camera(i, self.camera_size)
                cam.start()
                self.cams.append(cam)
            except SystemError:
                print("Error opening {}".format(i))

    def update_cams(self):
        # if you don't want to tie the framerate to the camera, you can check
        # if the camera has an image ready.  note that while this works
        # on most cameras, some will never return true.
        for i,cam in enumerate(self.cams):
            cam.get_image(self.snapshots[i])

    def draw(self):
        for i in range(len(self.snapshots)):
            img = pygame.transform.flip(pygame.transform.rotate(self.snapshots[i], 270), True, False)
            self.display.blit(pygame.transform.scale(img, self.preview_size), (self.preview_size[0]*i, 0))

    def do_capture(self):
        t = time.strftime("%d%m%y-%H%M%S")
        for i in range(len(self.snapshots)):
            pygame.image.save(pygame.transform.rotate(self.snapshots[i], 270), self.img_path+"IMG-{}-{}.jpg".format(t, i))
            # subprocess.call(["cp", "{}.jpg".format(i), self.img_path+"IMG-{}-{}.jpg".format(t, i)])
        print("Picture taken at {}".format(t))

    def draw_stitch(self):
        subprocess.call(["nona", "-m", "JPEG", "-o", "out", "params.pto"])
        self.stitch = pygame.image.load("out.jpg")
        r = pygame.Rect((0,0), self.resolution)
        c = pygame.Rect((0,0), self.stitch.get_size())
        s = c.fit(r)
        self.display.blit(pygame.transform.scale(self.stitch, s.size), (0,0))
        pygame.display.flip()
        pygame.time.wait(5000)
    def display_text(self, text, color=pygame.Color(0,0,0,255)):
        text = self.font.render("{}".format(text), True, (255, 255, 255))
        self.display.fill(color)
        self.display.blit(text, (
            self.resolution[0] // 2 - text.get_width() // 2,
            self.resolution[1] // 2 - text.get_height() // 2
        ))
        pygame.display.flip()
    def main(self):
        going = True
        whiteScreen=False
        countdown = 0
        state = "waiting"
        while going:
            self.update_cams()
            events = pygame.event.get()
            for e in events:
                if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                    # close the camera safely
                    for cam in self.cams:
                        cam.stop()
                    going = False
                elif e.type == KEYDOWN and e.key == K_SPACE and state == "waiting":
                    state="counting"
                    countdown = 3
                    pygame.time.set_timer(USEREVENT+1, 1000)
                    self.display_text(countdown)
                    print(countdown)
                elif e.type == USEREVENT+1: # counting timer event
                    if countdown > 1:
                        countdown -= 1
                        print(countdown)
                        self.display_text(countdown)
                    else: # countdown == 0
                        pygame.time.set_timer(USEREVENT+1, 0)
                        state="shooting"
                        pygame.time.set_timer(USEREVENT+2, 800)
                elif e.type==USEREVENT+2:
                    pygame.time.set_timer(USEREVENT+2,0)
                    self.do_capture()
                    state="waiting"
            if state=="shooting":
                self.display.fill(pygame.Color(255,255,255,255))
                self.display_text("clic!", pygame.Color(0,0,0,255))
                pygame.display.flip()
            elif state=="waiting":
                self.display_text("badge pr prendr 1 foto ^^^^")

if __name__ == "__main__":
    cap = Capture()
    cap.main()
