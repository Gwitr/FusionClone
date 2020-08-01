from mmfbase import Object, register, AxisNames

@register("Background")
class VisibleObject(Object):

    ATTRIBUTE_NAMES = ["Sprite name"]
    ACTIONS = [("Destroy", None), ("Move", list)]
    EVENTS = [("Collision", Object)]

    # Overriden abstract methods
    def init(self):
        self.img = self.game.image_load(self.getattr("Sprite name"))
        self.size = [self.img.get_width(), self.img.get_height()]

    def check_event(self, name, arg):
        r = super().check_event(name, arg)
        if r: return r
        
        if name == "Collision":
            frame = self.game.frames[self.game.current_frame]
            for obj in frame.grid.find_objects(self.objs, arg):
                if isinstance(obj, VisibleObject):
                    if self.check_overlap(obj):
                        return [self, obj]
            return None
        else:
            return None

    def handle_action(self, name, arg):
        if name == "Move":
            if not isinstance(arg, list):
                raise TypeError("arg is not list")
            if len(arg) != 2:
                raise TypeError("arg is %dD vector, must be 2D" % len(arg))
            if not isinstance(arg[0], int):
                raise TypeError("arg.x is not int")
            if not isinstance(arg[1], int):
                raise TypeError("arg.y is not int")
            
            self.pos = arg

    def tick(self):
        self.game.display.blit(self.img, [self.pos[0], -self.pos[1]])

    # VisibleObject internal methods
    def check_overlap(self, other):
        self_x0 = self.pos[0]
        self_x1 = self.pos[0] + self.size[0]
        self_y0 = self.pos[1]
        self_y1 = self.pos[1] + self.size[1]
        
        other_x0 = other.pos[0]
        other_x1 = other.pos[0] + other.size[0]
        other_y0 = other.pos[1]
        other_y1 = other.pos[1] + other.size[1]

        p0res = (other_x0 >= self_x0 and other_x0 <= self_x1) and\
                (other_y0 >= self_y0 and other_y0 <= self_y1)
        
        p1res = (other_x0 >= self_x0 and other_x0 <= self_x1) and\
                (other_y1 >= self_y0 and other_y1 <= self_y1)

        p2res = (other_x1 >= self_x0 and other_x1 <= self_x1) and\
                (other_y0 >= self_y0 and other_y0 <= self_y1)

        p3res = (other_x1 >= self_x0 and other_x1 <= self_x1) and\
                (other_y1 >= self_y0 and other_y1 <= self_y1)

        return p0res or p1res or p2res or p3res

@register("Active")
class Active(VisibleObject):

    ATTRIBUTE_NAMES = VisibleObject.ATTRIBUTE_NAMES + \
                      ["Movement type", "Damping value", "Speed"]

    def init(self):
        super().init()
        self.vx = 0
        self.vy = 0

    def tick(self):
        mvtype = self.getattr("Movement type")
        if mvtype == "None":
            pass
        elif mvtype == "Top-down":
            hor = self.game.get_axis(AxisNames.P1_HORIZONTAL)
            ver = self.game.get_axis(AxisNames.P1_VERTICAL)
            if hor:
                self.vx = hor * self.getattr("Speed")
            if ver:
                self.vy = ver * self.getattr("Speed")
        else:
            raise ObjectError("Unknown movement type %s" % mvtype)

        damping = self.getattr("Damping value") ** self.game.get_time()
        self.vx *= damping
        self.vy *= damping
        # print(self.vx, self.vy)
        
        self.pos = [
            self.pos[0] + self.vx * self.game.get_time(),
            self.pos[1] + self.vy * self.game.get_time()
        ]

        super().tick()
