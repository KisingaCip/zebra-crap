#!/usr/bin/env python

"""
label_render_and_print.py: render and print a label to a ZPL/TCP-speaking printer
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

from PIL import Image
import pygame
import pygame.freetype
import sys
import binascii
import logging
import socket
import math
import time

logging.basicConfig(level=logging.DEBUG)
pygame.init()

dpi = 203
width = 3
height = 1.5

w_px = int(width * dpi)
h_px = int(height * dpi)

screen = None

fonts = {
         #'Note This': pygame.freetype.Font("fonts/Note_this.ttf"),
         #'AmazGoDa': pygame.freetype.Font("fonts/AmazGoDa.ttf"),
         #'Genius': pygame.freetype.Font("fonts/Genius-400-Regular.otf")
         }

class Element:
    def __init__(self, **kwargs):
        self.y = kwargs['y']
        self.x = kwargs['x'] if 'x' in kwargs else None
        self.text = kwargs['text'] if 'text' in kwargs else None
        self.font = kwargs['font'] if 'font' in kwargs else None
        self.width = kwargs['width'] if 'width' in kwargs else None
        self.height = kwargs['height'] if 'height' in kwargs else None
        self.size = kwargs['size'] if 'size' in kwargs else None
        self.r = kwargs['r'] if 'r' in kwargs else None
        self.color = kwargs['color'] if 'color' in kwargs else (0,0,0)
    
    def draw(self, surface):
        if self.font:
            # element is text
            font = fonts[self.font]
            if self.x is not None:
                # defined x location
                # get optimal size
                if self.size is not None:
                    size = self.size
                else:
                    if self.width is not None:
                        # defined maximum width
                        max_width = self.width * dpi
                    else:
                        # width is the full label to the right of x
                        max_width = (width - self.x) * dpi
                    logging.debug('Text "%s" max_width is %s' % (self.text, max_width))
                    # keep trying to draw until we reach maximum permissible dimensions
                    size = 1
                    while True:
                        dims = font.get_rect(self.text, size=size)
                        if dims.width > max_width:
                            logging.debug('Text "%s" hit max width %s at size %s' % (self.text, max_width*dpi, size-1))
                            break
                        #if self.height is not None and dims.height > (self.height * dpi):
                        if self.height is not None and font.get_sized_ascender(size) > (self.height * dpi):
                            logging.debug('Text "%s" hit max height %s at size %s (width %s)' % (self.text, self.height*dpi, size-1, dims.width))
                            break
                        size += 1
                    size -= 1
                txt_dims = font.get_rect(self.text, size=size)
                txt_dims.x = int(self.x * dpi)
                txt_dims.y = int(self.y * dpi)
                font.origin = True
                font.render_to(surface, txt_dims, self.text, fgcolor=self.color, size=size)
            else:
                # centered text
                # get optimal size
                if self.width is not None:
                    # defined maximum width
                    max_width = self.width * dpi
                else:
                    # width is the full label
                    max_width = width * dpi - 1
                logging.debug('Text "%s" max_width is %s' % (self.text, max_width))
                if self.size is not None:
                    size = self.size
                else:
                    # keep trying to draw until we reach maximum permissible dimensions
                    size = 1
                    while True:
                        dims = font.get_rect(self.text, size=size)
                        if dims.width > max_width:
                            logging.debug('Text "%s" hit max width %s at size %s' % (self.text, max_width*dpi, size-1))
                            break
                        if self.height is not None and font.get_sized_ascender(size) > (self.height * dpi):
                            logging.debug('Text "%s" hit max height %s at size %s (width %s)' % (self.text, self.height*dpi, size-1, dims.width))
                            break
                        size += 1
                    size -= 1
                draw_centered_text(surface, fonts[self.font], self.text, size, self.y, self.color)
        else:
            # element is a box
            if self.r is not None:
                # rounded rectangle
                draw_rounded_rect(surface, self.x * dpi, self.y * dpi, self.width * dpi, self.height * dpi, self.r * dpi, self.color)
            else:
                # normal rectangle
                pygame.draw.rect(surface,
                                 self.color,
                                 pygame.Rect(self.x * dpi,
                                             self.y * dpi,
                                             self.width * dpi,
                                             self.height * dpi))

def draw_rounded_rect(surface, x, y, w, h, r, color):
    pygame.draw.rect(surface, color, pygame.Rect(int(x+r), int(y), int(w-2*r), int(h)))
    pygame.draw.rect(surface, color, pygame.Rect(int(x), int(y+r), int(w), int(h-2*r)))
    pygame.draw.circle(surface, color, (int(x+r), int(y+r)), int(r))
    pygame.draw.circle(surface, color, (int(x+w-r), int(y+r)), int(r))
    pygame.draw.circle(surface, color, (int(x+r), int(y+h-r)), int(r))
    pygame.draw.circle(surface, color, (int(x+w-r), int(y+h-r)), int(r))

def draw_centered_text(surface, font, text, size, y, color):
    # use baseline instead of top
    font.origin = True
    txt_dims = font.get_rect(text, size=size)
    # set x to label center minus half of text width (centering text on label)
    txt_dims.x = int((dpi * width / 2) - (txt_dims.w / 2))
    # set y (baseline) to top of fill-in-the-blanks line
    txt_dims.y = int(y * dpi)
    font.render_to(surface, txt_dims, text, fgcolor=color, size=size)

def draw_right_text(surface, font, text, size, x, y, color):
    # use baseline instead of top
    font.origin = True
    txt_dims = font.get_rect(text, size=size)
    # set x to given x - text width
    txt_dims.x = int(x * dpi) - txt_dims.w
    # set y (baseline) to top of fill-in-the-blanks line
    txt_dims.y = int(y * dpi)
    font.render_to(surface, txt_dims, text, fgcolor=color, size=size)

def draw_badge(name, badgetype, line1='', line2=''):
    s = pygame.Surface((w_px, h_px))
    s.fill((255, 255, 255))
    
    # draw sample text
    elements = [Element(y=0.4, font='Note This', text=name, width=2.35, height=0.375),
                Element(x=0.25, y=0.4, width=2.5, height=0.025),
                Element(y=0.7, height=0.16, font='Genius', text=line1, width=2.6),
                Element(y=0.93, height=0.16, font='Genius', text=line2, width=2.6),
                Element(y=1.45, font='AmazGoDa', text=badgetype, height=0.25, width=2.2),
                ]
    
    for el in elements:
        el.draw(s)
    
    # get raw data
    # pygame has a limited vocabulary, so we convert to raw RGB and
    # have PIL/Pillow convert to inverted bilevel
    data = pygame.image.tostring(s, 'RGB')
    i = Image.fromstring('RGB', (int(width * dpi), int(height * dpi)), data)
    i = i.convert('1')
    data = i.tostring('raw', '1;I')
    zebra_data = binascii.b2a_hex(data).upper()
    i.save('test.png')
    
    # ZPL construction
    dots_per_row = dpi * width
    bytes_per_row = int(math.ceil(dots_per_row / 8.0))
    dg_cmd = '~DGR:TEST.GRF,%s,%s,%s\n' % (len(data), bytes_per_row, zebra_data)
    print_cmd = '^XA\n^FO0,0,0^XGR:TEST.GRF,1,1^FS\n^XZ'
    
    # ZPL communication
    do_print = True
    if do_print:
        ZPL_IP = '192.168.1.202'
        ZPL_PORT = 9100
        MESSAGE = dg_cmd + print_cmd
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ZPL_IP, ZPL_PORT))
        sock.send(MESSAGE)
        sock.close()

    # show on screen
    close = False
    screen.blit(s, (0,0))
    pygame.display.flip()
    while not close:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: close = True

def main():
    global screen
    screen = pygame.display.set_mode((w_px, h_px))
    draw_badge('Test Name', 'Test Badge Type', 'this is line 1', 'this is line 2')


if __name__ == '__main__':
    main()
