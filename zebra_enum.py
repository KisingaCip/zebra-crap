#!/usr/bin/env python

"""
zebra_enum.py: enumerate Zebra printers on the local network
Copyright © 2014-2015 Andrew Brockert

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# change to '' to bind to first adapter
sock.bind(('192.168.1.85', 0))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.setblocking(0)

known_addrs = []
while True:
    sock.sendto('\x2e\x2c\x3a\x01\x00\x00', ('<broadcast>', 4201))
    timeout = 1000
    for i in range(timeout / 50):
        try:
            data, addr = sock.recvfrom(1024)
            if addr not in known_addrs:
                known_addrs.append(addr)
                print '[%s] new printer: %s' % (time.strftime('%H:%M:%S', time.localtime()), addr[0])
        except socket.error:
            pass
        time.sleep(0.05)
