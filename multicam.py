import pygame
import pygame.camera
from pygame.locals import *

pygame.init()
pygame.camera.init()


class Capture(object):
    def __init__(self):
        self.size = (1920, 1080)
        # create a display surface. standard pygame stuff

        # this is the same as what we saw before
        self.clist = pygame.camera.list_cameras()
        if not self.clist:
            raise ValueError("Sorry, no cameras detected.")
        self.cams = []
        for i in self.clist:
            try:
                cam = pygame.camera.Camera(i, self.size)
                cam.start()
                self.cams.append(cam)
            except SystemError:
                print("Error opening {}".format(i))
        self.display = pygame.display.set_mode((self.size[0],self.size[1]*len(self.cams)), 0)
        # create a surface to capture to.  for performance purposes
        # bit depth is the same as that of the display surface.
        self.snapshots = [pygame.surface.Surface(self.size, 0, self.display)
                         for i in self.cams]

    def get_and_flip(self):
        # if you don't want to tie the framerate to the camera, you can check
        # if the camera has an image ready.  note that while this works
        # on most cameras, some will never return true.
        for i,cam in enumerate(self.cams):
            if cam.query_image():
                self.snapshots[i] = cam.get_image(self.snapshots[i])
                self.display.blit(self.snapshots[i], (0, self.size[1]*i))

        # blit it to the display surface.  simple!
        pygame.display.flip()

    def main(self):
        going = True
        while going:
            events = pygame.event.get()
            for e in events:
                if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                    # close the camera safely
                    for cam in self.cams:
                        cam.stop()
                    going = False

            self.get_and_flip()


if __name__ == "__main__":
    cap = Capture()
    cap.main()
