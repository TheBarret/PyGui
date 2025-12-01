import pygame
import time
import random
from typing import List, Any, Dict, Tuple, Callable

from component import Component                                                 # base layers
from primitives import Alignment, Style                                         # structures
from primitives import Label, MultiLabel, Button, Toolbar, Slider               # generic components
from window import Window                                                       # window layer
from utilities import Pulsar, Performance, DummyLoad                   # widgets

from bus import BROADCAST, MASTER, Response, Packet, AddressBus

# Window Builders

class WindowBase:
    def __init__(self, engine: Component):
        self.window = None
        self.engine = engine
        self.components = {}
        self.content = {}
        self.title = ''
        
    def make_window(self, x: int = 0, y: int = 0, width: int = 400, height: int = 300,
                    can_close: bool = True, can_move: bool = True) -> 'WindowBase':
        self.window = Window(x ,y, width, height)
        self.window.name = f'window_{len(self.engine.children)+1}'
        self.window.can_close = can_close
        self.window.can_move = can_move
        self.window.passthrough = False
        return self
    
    def build(self) -> 'WindowBase':
        if hasattr(self.engine, 'bus'):
            self.finalize()
        else:
            print('Warning: missing bus messenger instance')
        return self
        
    def finalize(self) -> None:
        # clear references
        title = self.title
        window = self.window
        # copy to avoid modification during iteration
        components = self.components.copy()
        
        # reset state
        self.title = ''
        self.window = None
        self.components = {}
        
        # add window to engine first
        self.engine.add(window)
        
        # Then register and add components
        for name, component in components.items():
            component.register_all(self.engine.bus)
            window.add(component)

class Gui(WindowBase):
    def __init__(self, engine: Component):
        super().__init__(engine)
        self.last_row = None
        self.divisor = 2
        self.offset = 0
        self.header = 24
        self.padding = 2
        
    def add_header(self, title: str, extra: bool = True) -> 'Gui':
        if self.window:
            self.title = title
            # icon
            icon = Pulsar(0, 0, 24, 24)
            icon.name = 'icon'
            icon.passthrough = True
            icon.border = True
            icon.border_style = 2
            
            # label
            caption = Label(24, 0, self.window.width-48, 24, title)
            caption.name = 'caption'
            caption.passthrough = True
            caption.border = True
            caption.border_style = 2
            caption.filler = True
            caption.filler_style = 4
            
            # closer
            closer = Button(self.window.width-24, 0, 24, 24, 'X')
            closer.name = 'button_close'
            closer.passthrough = False
            closer.on_click = self.window.destroy
            closer.border_style = 2
            
            if extra:
                # toggle
                rtc = Button(self.window.width-48, 0, 24, 24, 'S')
                rtc.name = 'button_rtc'
                rtc.passthrough = False
                rtc.on_click = self.window.toggle_snap
                rtc.border_style = 2
                
                # lock
                lock = Button(self.window.width-72, 0, 24, 24, 'L')
                lock.name = 'button_lock'
                lock.passthrough = False
                lock.on_click = self.window.toggle_lock
                lock.border_style = 2
                
                 # update
                self.components.update({
                    'icon': icon,
                    'caption': caption,
                    'close': closer,
                    'rtc': rtc,
                    'lock': lock
                })
                return self
            
        # update
        self.components.update({
            'icon': icon,
            'caption': caption,
            'close': closer,
        })
        return self
    
    def add_load(self, resistance: float = 1.0) -> 'Gui':
        if self.window:
            dl = DummyLoad(resistance)
            ref = str(len(self.components)+1)
            dl.name = 'artificial_load'
            self.components.update({
                'dummy_'+ ref: dl,
            })
        return self
    
    # Y-Stacked 'Toolbar' containers
    
    def add_toolbars(self, amount: int, div: int = 2) -> 'Gui':
        for i in range(0, amount):
            self.add_toolbar(div)
        return self
    
    def add_toolbar(self, div: int = 2) -> 'Gui':
        if self.window:
            # set divisor
            self.divisor = min(8, max(2, div))

            # set height offset
            _height = self.header + self.padding
            if self.last_row:
                _height = self.last_row.y + self.last_row.height
                
            # create toolbar
            ref = str(len(self.components)+1)
            row = Toolbar(self.padding, _height, self.window.width-self.padding*2, self.header, Alignment.CENTER, Alignment.CENTER)
            row.name = f'toolbar_{ref}'
            row.passthrough = True
            row.border = True
            row.border_style = 0
            row.filler = True
            row.filler_style = 0
            self.components.update({
                'toolbar_' + ref: row,
            })
            # update position
            self.offset = (row.width * 0.90)
            self.last_row = row
        return self
    
    # X-Stacked Toolbar Items
    
    def add_debug(self) -> 'Gui':
        if self.window and self.last_row:
            # get width
            _width = self.offset // self.divisor
            _length = len(self.last_row.children)
            # based on previous items
            _x = self.padding + (_width * _length)
            
            item = Performance(_x, 2, _width, self.last_row.height - 4)
            item.name = 'monitor_' + str(_length)  # Unique names
            item.passthrough = False
            item.border = True
            item.border_style = 2
            self.last_row.add(item)
            
        return self
    
    def add_label(self, caption: str) -> 'Gui':
        if self.window and self.last_row:
            # get width
            _width = self.offset // self.divisor
            _length = len(self.last_row.children)
            # based on previous items
            _x = self.padding + (_width * _length)

            item = Label(_x, 2, _width, self.last_row.height - 4, caption)
            item.name = 'label_' + str(_length)  # Unique names
            item.passthrough = False
            item.border = False
            item.filler = False
            self.last_row.add(item)
        return self

    def add_button(self, caption: str, cb: Callable) -> 'Gui':
        if self.window and self.last_row:
            # get width
            _width = self.offset // self.divisor
            _length = len(self.last_row.children)
            # based on previous items
            _x = self.padding + (_width * _length)

            item = Button(_x, 2, _width, self.last_row.height - 4, caption)
            item.name = 'button_' + str(_length)  # Unique names
            item.passthrough = False
            item.on_click = cb
            self.last_row.add(item)
        return self
    
    def add_slider(self, min_value: float, max_value: float, cb: Callable = None) -> 'Gui':
        if self.window and self.last_row:
            # get width
            _width = self.offset // self.divisor
            _length = len(self.last_row.children)
            # based on previous items
            _x = self.padding + (_width * _length)
            
            item = Slider(_x, 2, _width, self.last_row.height - 4, min_value, max_value, (min_value + max_value) // 2, cb)
            item.name = 'slider_' + str(_length)  # Unique names
            item.passthrough = False
            item.border = True
            item.border_style = 2
            self.last_row.add(item)
        return self

    def set_theme(self, hue: int = -1, contrast: float = 0.5) -> 'Gui':
        if hasattr(self.engine, 'bus'):
            theme = self.window.new_theme(hue, contrast)
            self.engine.bus.post(Packet(
                receiver=BROADCAST,
                sender=MASTER,
                rs=Response.M_THEME,
                data=theme
            ))
        return self
        
