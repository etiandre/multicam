# coding: utf8
#!/usr/bin/env python2

import pygame
import pygame.camera
from pygame.locals import *
import time
import subprocess
from threading import Thread, Event
import serial
from os import mkdir
from os.path import isdir

pygame.mixer.pre_init(44100, 16, 2, 4096)
pygame.init()
pygame.camera.init()

HOME_DIR = "/home/photo/multicam/"
LOGS_FILE = HOME_DIR + "logs.txt"
IMG_DIR = HOME_DIR + "img/"

def LogToFile(message):
    file = open(LOGS_FILE, "a")
    file.write("Py:\t{}\r\n".format(message))
    file.close()


class Capture(object):
    def __init__(self, no_video=False):
        LogToFile("init start")
        # self.camera_size = (2304, 1536)
        self.camera_size = (1920, 1080)
        self.resolution = (1280, 1024)
        self.img_path = IMG_DIR
        self.no_video = no_video
        self.brightness = 230
        try:
            self.snd_beep = pygame.mixer.Sound(HOME_DIR+"beep.wav")
            self.snd_snap = pygame.mixer.Sound(HOME_DIR+"snap.wav")
        except Exception as e:
            print(e)
            LogToFile("Error on mixer:{}".format(str(e)))

        self.start_cams(self.camera_size)
        # setup display
        if not self.no_video:
            self.display = pygame.display.set_mode(self.resolution, 0)
        # create a surface to capture to.  for performance purposes
        # bit depth is the same as that of the display surface.
        self.snapshots = [pygame.surface.Surface(self.camera_size, 0, 32)
                          for i in self.cams]
        countdown = 0
        # calculate preview size
        self.font = pygame.font.Font(pygame.font.get_default_font(), 72)
        self.update_brightness()
        LogToFile("Init done")

    def start_cams(self, size):
        # self.clist = pygame.camera.list_cameras()
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
                subprocess.call(["v4l2-ctl", "-d", i, "-c" "exposure_auto_priority=1,exposure_auto=1"])
                self.cams.append(cam)
            except SystemError:
                print("Error opening {}".format(i))
                LogToFile("Error opening {}".format(i))
        LogToFile("Cams Started")

    def update_cams(self):
        # if you don't want to tie the framerate to the camera, you can check
        # if the camera has an image ready.  note that while this works
        # on most cameras, some will never return true.
        for i, cam in enumerate(self.cams):
            cam.get_image(self.snapshots[i])

    def draw(self):
        if self.no_video: return
        for i in range(len(self.snapshots)):
            img = pygame.transform.flip(pygame.transform.rotate(self.snapshots[i], 270), True, False)
            self.display.blit(pygame.transform.scale(img, self.preview_size), (self.preview_size[0] * i, 0))

    def do_capture(self):
        t = time.strftime("%d%m%y-%H%M%S")
        for i in range(len(self.snapshots)):
            pygame.image.save(pygame.transform.rotate(self.snapshots[i], 270),
                              self.img_path + "IMG-{}-{}-{}.jpg".format(t, self.badgereader.id, i))
            subprocess.call(["cp", self.img_path + "IMG-{}-{}-{}.jpg".format(t, self.badgereader.id, i), "{}.jpg".format(i),])
        print("Picture taken at {}".format(t))
        LogToFile("Picture taken at {}".format(t))

    def draw_stitch(self):
        if self.no_video: return
        subprocess.call(["nona", "-m", "JPEG", "-o", "out", "project.pto"])
        self.stitch = pygame.image.load("out.jpg")
        r = pygame.Rect((0, 0), self.resolution)
        c = pygame.Rect((0, 0), self.stitch.get_size())
        s = c.fit(r)
        self.display.blit(pygame.transform.scale(self.stitch, s.size), (0, 0))
        pygame.display.flip()
        pygame.time.wait(5000)

    def display_text(self, text, color=pygame.Color(0, 0, 0, 255)):
        if self.no_video: return
        text = self.font.render("{}".format(text), True, (255, 255, 255))
        self.display.fill(color)
        self.display.blit(text, (
            self.resolution[0] // 2 - text.get_width() // 2,
            self.resolution[1] // 2 - text.get_height() // 2
        ))
        pygame.display.flip()
    def update_brightness(self):
        print("Updating brightness: {}".format(self.brightness))
        for i in self.clist:
            subprocess.call(["v4l2-ctl", "-d", i, "-c" "exposure_absolute={}".format(self.brightness)])
    def main(self):
        LogToFile("Main started")
        going = True
        countdown = 0
        state = "waiting"
        self.badgereader = BadgeReader()
        self.badgereader.start()
        print("Ready")
        LogToFile("Ready")
        while going:
            self.update_cams()
            if self.badgereader.id != "" and self.badgereader.ready.is_set() and state == "waiting":
                print("putting keydown event in queue")
                e = pygame.event.Event(KEYDOWN, {"key": K_SPACE})  # add key event
                pygame.event.post(e)
                self.badgereader.ready.set()  # block badge input
            events = pygame.event.get()
            for e in events:
                # print(e)
                LogToFile(e)
                if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                    # close the camera safely
                    self.badgereader.running = False
                    for cam in self.cams:
                        cam.stop()
                    going = False
                    print("Waiting for badgereader thread...")
                    LogToFile("Waiting for badgereader thread...")
                    self.badgereader.join()
                    exit()
                elif e.type == KEYDOWN and e.key == K_SPACE and state == "waiting":
                    state = "counting"
                    countdown = 5
                    self.snd_beep.play()
                    pygame.time.set_timer(USEREVENT + 1, 1000)
                    self.display_text(countdown)
                    print(countdown)
                    LogToFile(str(countdown))
                elif e.type == KEYDOWN and e.key == K_UP:
                    self.brightness += 10
                    self.update_brightness()
                elif e.type == KEYDOWN and e.key == K_DOWN:
                    self.brightness -= 10
                    self.update_brightness()
                elif e.type == USEREVENT + 1:  # counting timer event
                    if countdown > 1:
                        countdown -= 1
                        print(countdown)
                        LogToFile(str(countdown))
                        self.display_text(countdown)
                        if countdown == 1:
                            self.snd_beep.play(loops=-1)
                        else:
                            self.snd_beep.play()
                    else:  # countdown == 0
                        pygame.time.set_timer(USEREVENT + 1, 0)
                        self.snd_beep.stop()
                        self.snd_snap.play()
                        state = "shooting"
                        pygame.time.set_timer(USEREVENT + 2, 800)
                elif e.type == USEREVENT + 2:
                    pygame.time.set_timer(USEREVENT + 2, 0)
                    self.do_capture()
                    self.draw_stitch()
                    state = "waiting"
                    self.badgereader.id = ""
                    self.badgereader.ready.clear()  # release badge input
            if state == "shooting":
                if not self.no_video:
                    self.display.fill(pygame.Color(255, 255, 255, 255))
                    self.display_text("processing...", pygame.Color(0, 0, 0, 255))
                    pygame.display.flip()
            elif state == "waiting":
                self.display_text("Badger/Espace pour une photo")
        LogToFile("Main Finished")


class BadgeReader(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.f = None
        self.running = False
        try:
            self.f = serial.Serial("/dev/ttyUSB0")
            self.running = True
        except:
            print("[!] Unable to open serial !!")
        self.id = ""
        self.ready = Event()
        self.ready.clear()

    def run(self):
        while self.running:
            if self.f.in_waiting == 0 or self.ready.is_set():
                continue
            print(self.f.read())
            self.ready.set()
            id = self.f.readline()  # blocking
            if not self.running:
                return
            id = id.strip()  # remove \r\n
            print("badgereader : read {}".format(id))
            LogToFile("badgereader : read {}".format(id))
            self.id = id


if __name__ == "__main__":
    import sys

    if not isdir(IMG_DIR):
        mkdir(IMG_DIR)
    cap = None
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "novideo":
            print("launching without video")
            LogToFile("Launching without video")
            cap = Capture(no_video=True)
            LogToFile("Capture created")
            cap.main()
        else:
            cap = Capture()
            cap.main()
    except KeyboardInterrupt:
        LogToFile("Received SIG INT")
        if cap is not None:
            cap.badgereader.running = False
            cap.going = False
