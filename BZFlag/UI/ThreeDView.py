""" BZFlag.UI.ThreeDView

A 3d scene renderer similar to BZFlag proper
"""
#
# Python BZFlag Protocol Package
# Copyright (C) 2003 David Trowbridge <davidtrowbridge@users.sourceforge.net>
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import pygame, math
from pygame.locals import *
from BZFlag import Event
from OpenGL.GL import *
from OpenGL.GLU import *
from BZFlag.UI.Objects import Ground

class Camera:
    def __init__(self):
        self.focus = (0, 0, 4.0)
	self.distance = 750
	self.rotation = 45
	self.elevation = -75
	self.isFocused = True

    def load(self):
        glLoadIdentity()
	glTranslatef(0, 0, -self.distance)
	glRotatef(self.elevation, 1.0, 0.0, 0.0)
	glRotatef(self.rotation, 0.0, 0.0, 1.0)
	if self.isFocused:
	    glTranslatef(self.focus[0], self.focus[1], self.focus[2])

class ThreeDView:
    def __init__(self, game):
        self.game = game
	self.camera = Camera()
	self.ground = Ground.Ground()

    def configure(self, size):
	glViewport(0, 0, size[0], size[1]);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	gluPerspective(45.0, size[0] / size[1], 3.0, 2500.0);
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();

    def initialize(self, surface):
        """Initialize the opengl view"""
	self.size = surface.get_size()

	light_ambient = (0.5, 0.5, 0.5, 1.0)
	light_diffuse = (0.75, 0.75, 0.75, 1.0)
	light_position = (400, 400, 400, 1.0)

	glEnable(GL_TEXTURE_2D)
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_NORMALIZE)
	glEnable(GL_CULL_FACE)

	glClearColor(0.0, 0.0, 0.0, 0.0)
	glClearDepth(1.0);
	glDepthFunc(GL_LESS);
	glShadeModel(GL_SMOOTH);
	glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE);
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
	glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST);

	glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient);
	glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse);
	glLightfv(GL_LIGHT0, GL_POSITION, light_position);
	glEnable(GL_LIGHT0);
	glEnable(GL_LIGHTING);
	self.configure(self.size)

    def render(self):
        """Render the view to the given surface. This includes the game
	   world, with transient objects such as players and flags"""
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	self.camera.load()
	self.ground.draw()

def attach(game, eventLoop, size=(800,600), targetFrameRate=60):
    """Set up a window and opengl context on the given game and event loop"""

    def updateView():
        global view, screen
	if view:
	    game.update()
	    view.render()
	    pygame.display.flip()
    eventLoop.add(Event.PeriodicTimer(1.0 / targetFrameRate, updateView))

    global view, screen
    pygame.init()
    screen = pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF)
    view = ThreeDView(game)
    view.initialize(screen)
    updateView()
