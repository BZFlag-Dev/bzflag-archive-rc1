""" BZFlag.Client.Base

Provides the BaseClient class, which implements basic communication
with the server and provides hooks for adding more functionality
in subclasses.
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
from BZFlag import Network, Protocol, Errors, Event


class BaseClient(Network.Endpoint):
    """A basic client class that doesn't process any messages."""

    outgoing = Protocol.ToServer
    incoming = Protocol.FromServer
    
    def init(self):
        Network.Endpoint.init(self)
        self.connected = 0
        self.options.update({
            'server': None,
            })
        Event.attach(self, 'onConnect', 'onDisconnect')

        def setOptions(**options):
            if 'server' in options.keys():
                self.connect(options['server'])
        self.onSetOptions.observe(setOptions)

    def connect(self, server):
        """This does the bare minimum necessary to connect to the
           BZFlag server. It does not negotiate flags, obtain the
           world database, or join the game. After this function
           returns, the client is connected to the server and can
           receive and transmit messages.
           """
        if not server:
            raise Errors.NetworkException("A server must be specified")

        # Establish the TCP socket
        if self.tcp:
            self.disconnect()
        self.tcp = Network.Socket()
        self.tcp.connect(server, Protocol.Common.defaultPort)
        self.eventLoop.add(self.tcp)

        # Until we establish a UDP connection, we'll need to send
        # normally-multicasted messages over TCP
        self.multicast = self.tcp

        # Now we have to wait for the server's Hello packet,
        # with the server version and client ID.
        self.tcp.handler = self.handleHelloPacket

    def disconnect(self):
        if self.tcp:
            self.tcp.close()
            self.eventLoop.remove(self.tcp)
            self.tcp = None
        if self.udp:
            self.udp.close()
            self.eventLoop.remove(self.udp)
            self.udp = None
        self.multicast = None
        self.connected = 0
        self.onDisconnect()

    def onDisconnect(self):
        self.eventLoop.stop()

    def handleHelloPacket(self, socket, eventLoop):
        """This is a callback used to handle incoming socket
           data when we're expecting a hello packet.
           """
        # We should have just received a Hello packet with
        # the server version and our client ID.
        hello = socket.readStruct(self.incoming.HelloPacket)
        if hello.version != BZFlag.protocolVersion:
            raise Errors.ProtocolError(
                "Protocol version mismatch: The server is version " +
                "'%s', this client is version '%s'." % (
                hello.version, BZFlag.protocolVersion))
        self.id = hello.clientId

        # Now we're connected
        self.connected = 1
        socket.handler = self.handleMessage
        self.onConnect()

### The End ###
