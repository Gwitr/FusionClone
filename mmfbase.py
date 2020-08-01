import abc

class Frame():

    __slots__ = ["objs", "grid"]
    
    def __init__(self, objects, grid):
        self.objs = objects
        self.grid = grid

    @classmethod
    def from_dict(cls, d):
        objs = []
        for i in d["objs"]:
            objs.append(ObjInfo.from_dict(i))

        for objinfo, obj in zip(objs, d["objs"]):
            if obj["duplicate_of"] is not None:
                objinfo.duplicate_of = objs[obj["duplicate_of"]]
            else:
                objinfo.duplicate_of = None
        
        return cls(objs, EventGrid.from_dict(d["grid"]))

class Exit(Exception):
    pass

class AxisNames:
    def __new__(self):
        raise TypeError

    @classmethod
    def to_string(cls, axis):
        try:
            return [i for i in cls.__dict__ if cls.__dict__[i] == axis][0]
        except IndexError:
            raise LookupError from None

    @staticmethod
    def player(axis):
        return axis // 6 + 1

    @staticmethod
    def as_p1(axis):
        return axis % 6

    P1_VERTICAL   = 0
    P1_HORIZONTAL = 1
    P1_FIRE1      = 2
    P1_FIRE2      = 3
    P1_FIRE3      = 4
    P1_FIRE4      = 5

    P2_VERTICAL   = 6
    P2_HORIZONTAL = 7
    P2_FIRE1      = 8
    P2_FIRE2      = 9
    P2_FIRE3      = 10
    P2_FIRE4      = 11

    P3_VERTICAL   = 12
    P3_HORIZONTAL = 13
    P3_FIRE1      = 14
    P3_FIRE2      = 15
    P3_FIRE3      = 16
    P3_FIRE4      = 17

    P4_VERTICAL   = 18
    P4_HORIZONTAL = 19
    P4_FIRE1      = 20
    P4_FIRE2      = 21
    P4_FIRE3      = 22
    P4_FIRE4      = 23

class ObjectError(RuntimeError):
    pass

class Game(abc.ABC):

    def __init__(self, fileloader):
        self.display = None        # The "display" attribute MUST implement "blit"
        self.camerax = 0
        self.cameray = 0
        self.current_frame = None
        self.frames = []
        self.objs = set()
        self.fileloader = fileloader

        self.init()

    def run(self):
        self.switch_frame(0)
        while 1:
            try:
                self.pre_update()
                self.frames[self.current_frame].grid.tick(self.objs)
                for obj in self.objs:
                    obj.tick()
                self.post_update()
            except Exit:
                self.exit()
                return

    @abc.abstractmethod
    def init(self):
        ...

    @abc.abstractmethod
    def exit(self):
        ...

    @abc.abstractmethod
    def image_scale(self, img, x, y):
        ...

    @abc.abstractmethod
    def image_load(self, path):
        ...

    @abc.abstractmethod
    def sfx_load(self, path):
        ...

    @abc.abstractmethod
    def mus_play(self, path):
        ...

    @abc.abstractmethod
    def pre_update(self):
        ...

    @abc.abstractmethod
    def post_update(self):
        ...

    @abc.abstractmethod
    def get_axis(self, axis_name):
        ...

    @abc.abstractmethod
    def get_time(self):
        ...

    @classmethod
    def from_dict(cls, fileloader, d):
        frames = []
        for i in d["frames"]:
            frames.append(Frame.from_dict(i))

        game = cls(fileloader)
        game.frames = frames
        return game

    def switch_frame(self, fn):
        for i in self.objs:
            i.trigger_action("Destroy")

        self.current_frame = fn
        for objinfo in self.frames[self.current_frame].objs:
            objinfo.create_object(self, self.objs)

        for obj in self.objs:
            obj.update_duplicate()
        
        for objinfo in self.frames[self.current_frame].objs:
            objinfo.fill_attributes()

class Reader(abc.ABC):

    def __init__(self, fp):
        self.fp = fp

    @abc.abstractmethod
    def get_file(self, fn):
        ...

    @abc.abstractmethod
    def get_project_file(self):
        ...

class ObjInfo():

    OBJ_TYPES = {}
    __slots__ = ["name", "pos", "type", "attrib", "duplicate_of", "obj"]

    def __init__(self, type, name, pos, attrib):
        self.name = name
        self.pos = pos
        self.type = type
        self.attrib = attrib
        self.duplicate_of = None
        self.obj = None

    @staticmethod
    def from_dict(d):
        return ObjInfo(d["type"], d["name"], d["pos"], d["attrib"])

    @staticmethod
    def register_object_type(name, type):
        ObjInfo.OBJ_TYPES[name] = type

    def create_object(self, game, objs):
        obj = ObjInfo.OBJ_TYPES[self.type](game, objs, self.name, self.pos)
        self.obj = obj
        obj.duplicate_of = self.duplicate_of
        return obj

    def fill_attributes(self):
        self.obj.fill_attributes(self.attrib)

class Object(abc.ABC):

    ATTRUBUTE_NAMES = []
    # Editor stuff
    ACTIONS = [("Destroy",)]
    EVENTS = []
    
    def __init__(self, game, objs, name, pos):
        self.game = game
        self.name = name
        self.pos = pos
        self.objs = objs
        self.duplicate_of = None
        self.attrs = {}
        self.objs.add(self)

    @abc.abstractmethod
    def tick(self):
        ...

    @abc.abstractmethod
    def init(self):
        ...

    def update_duplicate(self):
        if self.duplicate_of is not None:
            self.duplicate_of = self.duplicate_of.obj

    def getattr(self, x):
        if self.duplicate_of is None:
            return self.attrs[x]
        else:
            return self.duplicate_of.getattr(x)

    def setattr(self, x, y):
        if self.duplicate_of is None:
            self.attrs[x] = y
        else:
            self.duplicate_of.setattr(x, y)

    def is_duplicate(self, obj):
        return self.duplicate_of is obj
    
    def trigger_action(self, name, arg):
        if name == "Destroy":
            try:
                self.objs.remove(self)
            except KeyError:
                pass
            else:
                self.on_destroy()
        else:
            self.handle_action(name, arg)

    def fill_attributes(self, d):
        if self.duplicate_of is None:
            self.attrs = d
            for i in self.__class__.ATTRIBUTE_NAMES:
                if i not in self.attrs:
                    raise AttributeError("Missing \"%s\" attribute" % i)

        self.init()  # Last loading step

    def on_destroy(self):
        ...
    
    @abc.abstractmethod
    def handle_action(self, name, arg):
        ...
    
    @abc.abstractmethod
    def check_event(self, name, arg):
        ...

class Event():

    __slots__ = ["name", "arg", "objname"]
    
    def __init__(self, name, objname, arg):
        self.name = name
        self.objname = objname
        self.arg = arg

    def __hash__(self):
        return hash((self.name, self.arg, self.objname))

    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d["objname"], d["arg"])

class Action():

    __slots__ = ["name", "objname", "value"]

    def __init__(self, name, objname, value):
        self.name = name
        self.objname = objname
        self.value = value

    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d["objname"], d["value"])

class EventGrid():

    __slots__ = ["grid"]
    def __init__(self):
        self.grid = {}

    def tick(self, objs):
        for event in self.grid:
            for obj in self.find_objects(objs, event.objname):
                related = obj.check_event(event.name, event.arg)
                if related:
                    for action in self.grid[event]:
                        for aobj in self.find_objects(objs, action.objname, related):
                            # print(event.name, event.objname, event.arg, id(obj), "->", action.name, action.objname, action.value, aobj.name, id(aobj))
                            aobj.trigger_action(action.name, action.value)

    def find_objects(self, objs, name, related=None):
        # TODO: VERIFY THIS LOGIC
        if related is None:
            return [i for i in objs if i.name == name]
        else:
            res = []
            if related[0].name == name:
                res.append(related[0])
            if len(related) > 1:
                if related[1].name == name:
                    res.append(related[1])
            for i in objs:
                if i.name == name and (not i.is_duplicate(related[0])) and (i != related[0]):
                    res.append(i)
            if len(res) == 0:
                for i in objs:
                    if i.name == related[0].name:
                        res.append(i)
            return res

    @classmethod
    def from_dict(cls, d):
        grid = cls()
        grid.grid = {Event.from_dict(event): [Action.from_dict(action) for action in actions] for event, actions in d}
        return grid

def register(name):
    def decorator(f):
        nonlocal name
        ObjInfo.register_object_type(name, f)
        return f
    return decorator
