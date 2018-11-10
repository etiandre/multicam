import pygame
import pygame.camera
from pygame.locals import *
import time

pygame.init()
pygame.camera.init()


class Capture(object):
    def __init__(self):
        self.preview_size = (1920, 1080)
        self.img_path = "img/"
        # self.preview_size = (2304, 1536)
        # create a display surface. standard pygame stuff

        # this is the same as what we saw before
        
        #self.clist = pygame.camera.list_cameras()
        self.clist = ["/dev/video3", "/dev/video0", "/dev/video1"]  
        if not self.clist:
            raise ValueError("Sorry, no cameras detected.")
        self.cams = []
        for i in self.clist:
            try:
                cam = pygame.camera.Camera(i, self.preview_size)
                cam.start()
                self.cams.append(cam)
            except SystemError:
                print("Error opening {}".format(i))
        self.display = pygame.display.set_mode((self.preview_size[1]*len(self.cams),self.preview_size[0]), 0)
        # create a surface to capture to.  for performance purposes
        # bit depth is the same as that of the display surface.
        self.snapshots = [pygame.surface.Surface(self.preview_size, 0, self.display)
                         for i in self.cams]
    def get_and_flip(self):
        # if you don't want to tie the framerate to the camera, you can check
        # if the camera has an image ready.  note that while this works
        # on most cameras, some will never return true.
        for i,cam in enumerate(self.cams):
            if cam.query_image():
                cam.get_image(self.snapshots[i])
                img = pygame.transform.rotate(self.snapshots[i], 270)
                img = pygame.transform.flip(img, True, False)
                self.display.blit(img, (self.preview_size[1]*i, 0))

        # blit it to the display surface.  simple!
        pygame.display.flip()
    def do_capture(self):
        t = time.strftime("%d%m%y-%H%M%S")
        for i in range(len(self.snapshots)):
            pygame.image.save(pygame.transform.rotate(self.snapshots[i], 270), self.img_path+"IMG-{}-{}.jpg".format(t, i))
        print("Picture taken at {}".format(t))
    def main(self):
        going = True
        while going:
            self.get_and_flip()
            events = pygame.event.get()
            for e in events:
                if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                    # close the camera safely
                    for cam in self.cams:
                        cam.stop()
                    going = False
                if e.type == KEYDOWN and e.key == K_SPACE:
                    self.do_capture()




if __name__ == "__main__":
    cap = Capture()
    cap.main()
