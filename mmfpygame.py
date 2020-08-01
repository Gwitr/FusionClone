import time
import pygame
import mmfbase

class FakeDisplay():

    def __init__(self, d):
        self.display = d
        self.images = []
    
    def blit(self, img, pos):
        self.images.append((img, pos))

class Game(mmfbase.Game):

    def init(self):
        if pygame.display.get_init():
            raise RuntimeError("Only one instance of mmfpygame.Game allowed at one time.")
        
        self._display = pygame.display.set_mode((800, 600))
        self._events = []
        self._clock = pygame.time.Clock()
        self.display = FakeDisplay(self._display)

    def exit(self):
        pygame.display.quit()
        pygame.mixer.quit()
        pygame.quit()

    def pre_update(self):
        self._clock.tick(60)
        self._display.fill(0)
        
        self._events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.display.quit()
                pygame.mixer.quit()
                pygame.quit()
                raise mmfbase.Exit
            else:
                self._events.append(event)

    def post_update(self):
        for i in self.display.images:
            self._display.blit(i[0], (i[1][0] - self.camerax, i[1][1] - self.cameray))

        self.display.images = []
        pygame.display.flip()

    def image_load(self, path):
        return pygame.image.load(self.fileloader.get_file(path))

    def image_scale(self, img, x, y):
        return pygame.transform.scale(img, (img.get_width() * x, img.get_width() * y))

    def sfx_load(self, path):
        return pygame.mixer.Sound(path)

    def mus_play(self, path):
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

    def get_axis(self, axis):
        if type(axis) != int:
            raise TypeError
        
        if mmfbase.AxisNames.player(axis) != 1:
            return 0
        
        axis_norm = mmfbase.AxisNames.as_p1(axis)
        keys = pygame.key.get_pressed()

        # print(mmfbase.AxisNames.to_string(axis), mmfbase.AxisNames.to_string(axis_norm))

        if axis_norm == mmfbase.AxisNames.P1_VERTICAL:
            positive = int(keys[pygame.K_w] or keys[pygame.K_UP])
            negative = int(keys[pygame.K_s] or keys[pygame.K_DOWN])
            return positive - negative

        if axis_norm == mmfbase.AxisNames.P1_HORIZONTAL:
            positive = int(keys[pygame.K_d] or keys[pygame.K_RIGHT])
            negative = int(keys[pygame.K_a] or keys[pygame.K_LEFT])
            return positive - negative

        return 0

    def get_time(self):
        return self._clock.get_time() / 1000


@mmfbase.register("Input")
class Input(mmfbase.Object):

    ATTRIBUTE_NAMES = mmfbase.Object.ATTRUBUTE_NAMES
    EVENTS = mmfbase.Object.EVENTS + [("Key pressed", str), ("Key released", str)]
    ACTIONS = mmfbase.Object.ACTIONS

    def init(self):
        self.last_pressed = pygame.key.get_pressed()
        self.pressed      = pygame.key.get_pressed()
        self.SPECIAL_KEY_MAP = {
            "ESC": pygame.K_ESCAPE,
            "RETURN": pygame.K_RETURN
        }

    def tick(self):
        self.last_pressed = self.pressed
        self.pressed = pygame.key.get_pressed()
    
    def check_event(self, name, arg):
        if name == "Key pressed":
            key_id = self.SPECIAL_KEY_MAP.get(arg, arg)
            if (not self.last_pressed[key_id]) and self.pressed[key_id]:
                return [self]
            return None

        elif name == "Key released":
            key_id = self.SPECIAL_KEY_MAP.get(arg, arg)
            if self.last_pressed[key_id] and (not self.pressed[key_id]):
                return [self]
            return None

    def handle_action(self, name, value):
        ...


@mmfbase.register("Game")
class GameObject(mmfbase.Object):

    ATTRIBUTE_NAMES = mmfbase.Object.ATTRUBUTE_NAMES
    EVENTS = mmfbase.Object.EVENTS + [("Timer expired", str), ("Frame start",)]
    ACTIONS = mmfbase.Object.ACTIONS + [
        ("Set timer #0", float),
        ("Set timer #1", float),
        ("Set timer #2", float),
        ("Set timer #3", float),
        ("Set timer #4", float),
        ("Set timer #5", float),
        ("Set timer #6", float),
        ("Set timer #7", float),
        ("Set timer #8", float),
        ("Set timer #9", float),
        ("Close game window",),
        ("Create object", dict),
        ("Camera: Move", list),
        ("Camera: Follow object", str)
    ]
    
    def init(self):
        self.timers = {}
        self.frame_start_sent = False
        self.cam_following = None

    def tick(self):
        if self.cam_following is not None:
            self.game.camerax = self.cam_following.pos[0] - 800 // 2
            self.game.cameray = -self.cam_following.pos[1] - 600 // 2

    def check_event(self, name, arg):
        if name == "Timer expired":
            # print(self.timers, repr(arg))
            if arg not in self.timers:
                return
            if time.perf_counter() - self.timers[arg][0] > self.timers[arg][1]:
                del self.timers[arg]
                return [self]

        elif name == "Frame start":
            if not self.frame_start_sent:
                self.frame_start_sent = True
                return [self]

    def on_destroy(self):
        raise mmfbase.Exit

    def handle_action(self, name, value):
        if name.startswith("Set timer #"):
            timern = int(name[-1])
            self.timers[timern] = [time.perf_counter(), value]

        elif name == "Close game window":
            raise mmfbase.Exit
        
        elif name == "Create object":
            print(value)
            try:
                objinfo = mmfbase.ObjInfo.from_dict(value)
            except KeyError as e:
                raise mmfbase.ObjectError("Create object failed: " + str(e))

            objinfo.create_object(self.game, self.objs)
            objinfo.fill_attributes()

        elif name == "Camera: Move":
            self.game.camerax = value[0]
            self.game.cameray = -value[1]

        elif name == "Camera: Follow object":
            if value is None:
                self.cam_following = None
            else:
                self.cam_following = self.game.frames[self.game.current_frame].grid.find_objects(self.objs, value)[0]
                self.game.camerax = self.cam_following.pos[0] - 800 // 2
                self.game.cameray = -self.cam_following.pos[1] - 600 // 2
