#!/usr/bin/env python
#
# Simple viewer for BZFlag world files. Give a .bzw file on the command line.
#
from BZFlag import World, Game, UI, CommandLine
from BZFlag.Event import EventLoop
import sys

ui = CommandLine.Parser(UI.Any, ui = 'overhead').parse()
game = Game.Game()
game.world = World.load(ui.cmdLineArgs[0])
loop = EventLoop()
ui.attach(game, loop)
loop.run()


