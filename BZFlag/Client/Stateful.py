""" BZFlag.Client.Stateful

Provides the StatefulClient class, which extends BaseClient to
support updating a game state and transmitting changes.
"""
#
# Python BZFlag Protocol Package
# Copyright (C) 2003 Micah Dowty <micahjd@users.sourceforge.net>
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
import BZFlag
from BZFlag import Errors, Player, Game, World, Event, Flag
from StringIO import StringIO
from BZFlag.Client.Base import BaseClient


class StatefulClient(BaseClient):
    """Extends the BaseClient to keep track of the state of the game
       world, as reported by the server and the other clients.
       """
    def init(self):
        BaseClient.init(self)
        self.game = Game.Game()
        self.worldCache = None
        Event.attach(self, 'onLoadWorld', 'onStartWorldDownload',
                     'onNegotiateFlags')

        # Immediately after connecting, ask for a world hash so
        # we can check our cache for a copy of that world
        self.onConnect.observe(self.negotiateFlags)

    def onMsgSuperKill(self, msg):
        """The server wants us to die immediately"""
        self.disconnect()

    def onMsgLagPing(self, msg):
        """The server is measuring our lag, reply with the same message."""
        msg.socket.write(msg)

    def negotiateFlags(self):
        """Send a MsgNegotiateFlags to the server to indicate which
           flags we know about. The server will respond with a
           MsgNegotiateFlags listing all the flags we need to participate
           in the game that we don't know about.
           """
        self.tcp.write(self.outgoing.MsgNegotiateFlags(
            data = Flag.joinAbbreviations(Flag.getDict().keys())))

    def onMsgNegotiateFlags(self, msg):
        """The server responded with a list of flags we need. If it's
           empty, we're good to go on with the rest of the connection.
           """
        unknownFlags = Flag.splitAbbreviations(msg.data)
        if unknownFlags:
            raise Errors.ProtocolError(
                "Server knows about the following flags that we don't: %s" %
                ", ".join(unknownFlags))
        self.onNegotiateFlags()

    def onNegotiateFlags(self):
        """Immediately after flag negotiation we usually want to start downloading
           the world. The first step is to get the world hash, so we can see if we
           have a cached copy of it.
           """
        self.getWorldHash()

    def getWorldHash(self):
        """Ask for a hash of the binary world data, so we can
           check our cache for it. This will trigger onMsgWantHash()
           """
        self.tcp.write(self.outgoing.MsgWantWHash())

    def onMsgWantWHash(self, msg):
        """Receive the world hash. If this is a permanent
           (not automatically generated by bzfs) map, try
           to cache it.
           """
        if msg.lifetime == 'permanent':
            self.worldCache = World.Cache()
        else:
            self.worldCache = None
        self.worldHash = msg.hash

        if self.worldCache and self.worldCache.hasWorld(self.worldHash):
            # Yay, the world is in our cache
            f = self.worldCache.openWorld(self.worldHash)
            self.game.world.loadBinary(f)
            f.close()
            self.onLoadWorld()
        else:
            # We're not using the cache or it didn't have our world.
            # Start a download.
            self.downloadWorld()

    def downloadWorld(self):
        """Start downloading the game world from the server.
           This will trigger onMsgGetWorld(), which will send
           more MsgGetWorlds until the entire world has been downloaded.
           """
        self.onStartWorldDownload()
        self.binaryWorld = ''
        self.tcp.write(self.outgoing.MsgGetWorld(offset=0))

    def onMsgGetWorld(self, msg):
        """We've received one chunk of the binary world. If there's more,
           request it, otherwise load the world and move on.
           """
        self.binaryWorld += msg.data
        if msg.remaining:
            # We need more data!
            self.tcp.write(self.outgoing.MsgGetWorld(offset=len(self.binaryWorld)))
        else:
            # Download is complete. Convert the binary world
            # into a World object and discard the binary world.
            # If we're using a cache, save a copy of the map.
            if self.worldCache:
                self.worldCache.storeWorld(self.worldHash, self.binaryWorld)
            self.game.world.loadBinary(StringIO(self.binaryWorld))
            del self.binaryWorld
            self.worldDownloaded = 1
            self.onLoadWorld()

    def onMsgAddPlayer(self, msg):
        self.game.addPlayer(Player.fromMessage(msg))

    def onMsgRemovePlayer(self, msg):
        self.game.removePlayer(msg.id)

    def onMsgPlayerUpdate(self, msg):
        try:
            self.game.players[msg.id].updateFromMessage(msg)
        except KeyError:
            pass

    def updateFlag(self, msg):
        """Generic handler for all messages that update a flag"""
        try:
            flag = self.game.getFlag(msg.flagNum, Flag.getDict()[msg.update.id])
            flag.updateFromMessage(msg)
        except KeyError:
            raise Errors.ProtocolWarning("Can't update flag number %d with unknown ID %d" %
                                         (msg.flagNum, msg.update.id))

    def onMsgFlagUpdate(self, msg):
        self.updateFlag(msg)

    def onMsgGrabFlag(self, msg):
        self.updateFlag(msg)

    def onMsgDropFlag(self, msg):
        self.updateFlag(msg)

    def onMsgTeamUpdate(self, msg):
        # FIXME
        pass

    def onMsgNewRabbit(self, msg):
        # FIXME
        pass

    def onMsgShotBegin(self, msg):
        # FIXME
        pass

    def onMsgShotEnd(self, msg):
        # FIXME
        pass

    def onMsgAlive(self, msg):
        # FIXME
        pass

    def onMsgTeleport(self, msg):
        # FIXME
        pass

### The End ###
