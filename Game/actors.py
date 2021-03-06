import pyglet
import math
import time
import json
import base
from base import Game

class Point:
    pass


class Entity:
    """
    All entities(such as towers and creeps) have the same
    properties, like x and y coordinates and stuff like that.
    """
    def __init__(self, name, x=0, y=0):
        self.name = name
        self.xp = 0
        self.level = 1

        self.alive = True

        self.x = x
        self.y = y
        self.radius = 5

        self.r = 255
        self.g = 255
        self.b = 255

    def render(self):
        pyglet.graphics.draw(6, pyglet.gl.GL_POLYGON,
                             ('v2f', (self.x - 10, self.y - 4,
                             self.x, self.y - 12,
                             self.x + 10, self.y - 4,
                             self.x + 10, self.y + 4,
                             self.x, self.y + 12,
                             self.x - 10, self.y + 4)),
                             ('c3B', (
                              self.r, self.g, self.b,
                              self.r, self.g, self.b,
                              self.r, self.g, self.b,
                              self.r, self.g, self.b,
                              self.r, self.g, self.b,
                              self.r, self.g, self.b))
                             )

    def dist(self, ent):
        return math.sqrt(math.pow(self.x - ent.x, 2) +
                         math.pow(self.y - ent.y, 2))

    def angle(self, ent):
        return math.atan2(ent.y - self.y, ent.x - self.x)

    def update(self):
        pass


class Creep(Entity):
    defs = json.load(open('res/defs/creeps.json'))

    def __init__(self, name, path):
        self.sprite = pyglet.sprite.\
                      Sprite(pyglet.resource.image("%s.png" % name),
                      batch=Game.batch)
        path = self._toObj(path)
        Entity.__init__(self, name, path[0].x, path[0].y)
        self.sprite.x = self.x
        self.sprite.y = self.y

        try:
            tmp = name.split('.')
            if len(tmp) > 1:
                name = tmp[0]
                self.level = int(tmp[1])
        except:
            pass

        self.name = name
        self.path = path
        self.r = 200
        self.g = 40
        self.b = 20

        self.speed = Creep.defs[name]['speed']
        self.hp = Creep.defs[name]['hp'] * self.level
        self.gold = Creep.defs[name]['gold'] * self.level
        self.radius = Creep.defs[name]['radius']

        self.alive = False
        self.path_point = 1
        self.reached_end = False

    def update(self):
        if self.alive is False:
            return

        #Update the position, in function of path point
        angle = self.angle(self.path[self.path_point])
        xdif = self.speed * math.cos(angle)
        ydif = self.speed * math.sin(angle)

        self.sprite.y = self.sprite.y + ydif
        self.sprite.x = self.sprite.x + xdif
        self.x = self.sprite.x
        self.y = self.sprite.y

        #Reach point?
        if self.dist(self.path[self.path_point]) < 5:
            self.path_point += 1

        #End of the line?
        if self.path_point == len(self.path):
            self.alive = False
            self.reached_end = True

    def render(self):
        #Entity.render(self)
        self.sprite.draw()
        pyglet.text.Label("%s Lv.%d - %d" % (self.name, self.level, self.hp),
                          font_name='Arial',
                          font_size=8,
                          x=self.x, y=self.y + 10,
                          anchor_x='center', anchor_y='center').draw()

    def _toObj(self, path):
        points = list()

        for point in path:
            P = Point()
            P.x = point['x']
            P.y = point['y']
            points.append(P)

        return points


class Tower(Entity):
    defs = json.load(open('res/defs/towers.json'))

    def __init__(self, name, x=0, y=0):
        name = int(name)
        T = Tower.defs['towers'][name]

        Entity.__init__(self, T['name'], x, y)
        self.r = 40
        self.g = 40
        self.b = 200

        self.cooldown = T['cooldown']
        self.cooldown_timer = 0
        self.bullet = None
        self.range = T['range']

    def not_shooting(self):
        if self.bullet is None:
            return True
        return False

    def shoot(self, target):
        if self.bullet is None:
            if time.time() - self.cooldown_timer > self.cooldown:
                self.cooldown_timer = time.time()
                self.bullet = Bullet("bang", target, self.x, self.y)

    def render(self):
        Entity.render(self)
        pyglet.text.Label("%s lv%d" % (self.name, self.level),
                          font_name='Arial',
                          font_size=8,
                          x=self.x, y=self.y + 10,
                          anchor_x='center', anchor_y='center').draw()

        #Target died before bullet reached it
        if self.bullet is not None and self.bullet.target.alive is False:
            self.bullet = None

        #Remove bullets
        if self.bullet is not None and self.bullet.alive is False:
            self.bullet = None

        if self.bullet is not None:
            self.bullet.render()
            self.bullet.update()


class Bullet(Entity):
    def __init__(self, name, ent, x=0, y=0, speed=6):
        Entity.__init__(self, name, x, y)
        self.r = 40
        self.g = 40
        self.b = 0

        self.speed = speed
        self.target = ent
        self.damage = 20

    def render(self):
        pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
                             ('v2f', (self.x, self.y))
                             )

    def update(self):
        #Update the position, in function of target's position
        angle = self.angle(self.target)
        xdif = self.speed * math.cos(angle)
        ydif = self.speed * math.sin(angle)

        self.y = self.y + ydif
        self.x = self.x + xdif

        #Impact?
        if self.dist(self.target) < self.target.radius:
            self.alive = False
            self.target.hp -= self.damage

            if self.target.hp <= 0:
                self.target.alive = False
