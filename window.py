import pygame
import time
import random
from typing import List, Any, Dict, Tuple, Callable

from component import Component
from primitives import Alignment, Style, Container, Label, MultiLabel, Button

from bus import BROADCAST, MASTER, Response, Packet, AddressBus

# Window Base

class Window(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150, title: str = 'Window', fixed: bool = False):
        super().__init__(x, y, width, height)
        self.name = 'Window'
        self.caption = title
        self.dragging = False
        self.drag_offset = (0, 0)
        self.can_move = not fixed
        self.filler = True
        self.filler_style = 0
        self.border = True
        self.border_style = 0
        
    def update(self, dt: float) -> None:
        super().update(dt)
        
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        if not self.can_move:
            self.draw_locked(surface)
        super().draw(surface)
        
    def process_event(self, event: pygame.event.Event) -> bool:
        if not self.can_move:
            return super().process_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hitbox_test(event.pos):
                self.dragging = True
                abs_rect = self.get_absolute_rect()
                self.drag_offset = (event.pos[0] - abs_rect.x, event.pos[1] - abs_rect.y)
                self.bring_to_front()
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
                
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            old_pos = self.position
            new_x = event.pos[0] - self.drag_offset[0]
            new_y = event.pos[1] - self.drag_offset[1]
            self.position = (new_x, new_y)

            # auto snap
            self.snap_on()

            return True
            
        return super().process_event(event)
    
    # Default dialog pre-states
    
    def click_ok(self) -> None:
        hoster = self.root()
        if hoster:
            theme = self.new_theme()
            hoster.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.address,
                rs=Response.M_OK,
                data=self
            ))
        self.destroy()
        
    def click_cancel(self) -> None:
        hoster = self.root()
        if hoster:
            theme = self.new_theme()
            hoster.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.address,
                rs=Response.M_CANCEL,
                data=self
            ))
        self.destroy()
        
    def cycle_theme(self) -> None:
        hoster = self.root()
        if hoster:
            theme = self.new_theme()
            hoster.bus.post(Packet(
                receiver=BROADCAST,
                sender=0, # root
                rs=Response.M_THEME,
                data=theme
            ))
    
    def toggle_lock(self) -> None:
        self.can_move = not self.can_move
        hoster = self.root()
        if hoster:
            hoster.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.address,
                rs=Response.M_LOCK,
                data=not self.can_move
            ))
        
    def destroy(self) -> None:
        hoster = self.root()
        if hoster:
            hoster.bus.post(Packet(receiver=hoster.address,sender=self.address, rs=Response.M_BYE, data=self))
        super().destroy()
    
    def hitbox_test(self, point: tuple[int, int], hitbox_y: int = 0) -> bool:
        """Check if click is within header area"""
        if not self.is_inside(point):
            return False
        abs_rect = self.get_absolute_rect()
        local_y = point[1] - abs_rect.y
        return local_y < self.height - hitbox_y
        
    def snap_on(self, threshold: int = 10) -> None:
        if not self.parent:
            return

        # Get all sibling windows (same parent, visible, not self)
        siblings = [
            child for child in self.parent.children
            if child is not self
            and isinstance(child, Window)
            and child.visible
            and not child.terminated
        ]

        my_rect = self.get_absolute_rect()

        for win in siblings:
            their_rect = win.get_absolute_rect()

            # Horizontal snapping: left/right edges
            if abs(my_rect.left - their_rect.left) <= threshold:
                dx = their_rect.left - my_rect.left
                self.x += dx
            elif abs(my_rect.right - their_rect.right) <= threshold:
                dx = their_rect.right - my_rect.right
                self.x += dx

            # Vertical snapping: top/bottom edges
            if abs(my_rect.top - their_rect.top) <= threshold:
                dy = their_rect.top - my_rect.top
                self.y += dy
            elif abs(my_rect.bottom - their_rect.bottom) <= threshold:
                dy = their_rect.bottom - my_rect.bottom
                self.y += dy
            
# Window Builders

class WindowBase:
    def __init__(self, engine: Component):
        self.window = None
        self.engine = engine
        self.header = 0
        self.footer = 0
        
    def create(self, x: int = 0, y: int = 0, width: int = 400, height: int = 300) -> 'WindowBase':
        self.window = Window(x ,y, width, height)
        self.window.can_close = True
        self.window.passthrough = False
        return self
    
    def build(self) -> 'WindowBase':
        if hasattr(self.engine, 'bus'):
            self.engine.add(self.window)
            self.engine.bus.post(Packet(receiver=BROADCAST,sender=self.window.address, rs=Response.M_PING, data=True))
        else:
            print('Warning: missing bus messenger instance')
        return self

class Gui(WindowBase):
    def __init__(self, engine: Component):
        super().__init__(engine)
        self.tag = ""
        self.header = 24
        self.padding = 10
        self.content = None
        self.components = {}
        
    def as_window(self, title: str) -> 'Gui':
        self.tag = title
        if self.window:
            # icon
            c_icon = Button(0, 0, self.header, self.header, 'L',
                                Alignment.CENTER, Alignment.CENTER, Style.SMALL)
            c_icon.name = 'Icon'
            c_icon.passthrough = False
            c_icon.on_click = self.window.toggle_lock
            c_icon.border = True
            self.components['icon'] = c_icon
            self.window.add(c_icon)
            
            # title caption
            c_label = Label(self.header, 0, 1, self.header, self.tag, 
                            Alignment.LEFT, Alignment.CENTER, Style.BIG)
            c_label.passthrough = True
            c_label.border = True
            self.components['label'] = c_label
            self.window.add(c_label)
            
            # finalize layout
            self._layout_dialog(True)
        return self

    def as_dialog(self, title: str, message: str) -> 'Gui':
        self.tag = title
        self.content = message
        if self.window:
            # icon #######################
            c_icon = Button(0, 0, self.header, self.header, 'L',
                                Alignment.CENTER, Alignment.CENTER, Style.SMALL)
            c_icon.name = 'Icon'
            c_icon.passthrough = False
            c_icon.border = True
            c_icon.on_click = self.window.toggle_lock
            self.components['icon'] = c_icon
            self.window.add(c_icon)
            
            # title caption
            c_label = Label(self.header, 0, 1, self.header, self.tag, 
                            Alignment.LEFT, Alignment.CENTER, Style.BIG)
            c_label.passthrough = True
            c_label.border = True
            self.components['label'] = c_label
            self.window.add(c_label)
            
            # finalize layout
            self._layout_dialog(False)
        return self

    def _layout_dialog(self, window: bool = False) -> None:
        if not self.window or 'icon' not in self.components:
            return
        c_icon = self.components['icon']
        c_label = self.components['label']
        
        c_icon.size = (self.header, self.header)
        c_icon.position = (0, 0)
        
        c_label.position = (self.header, 0)
        c_label.size = (self.window.width - self.header, self.header)
        if not window:
            if 'button_ok' not in self.components:
                btn_ok = Button(self.window.width - 120, self.window.height - 30, 60, 30, 'OK',
                                Alignment.CENTER, Alignment.CENTER, Style.SMALL)
                btn_ok.name = 'button_ok'
                btn_ok.border = True
                btn_ok.on_click = self.window.click_ok
                self.components['button_ok'] = btn_ok
                self.window.add(btn_ok)
            if 'button_cancel' not in self.components:
                btn_cancel = Button(self.window.width - 60, self.window.height - 30, 60, 30, 'CANCEL',
                                    Alignment.CENTER, Alignment.CENTER, Style.SMALL)
                btn_cancel.name = 'button_cancel'
                btn_cancel.border = True
                btn_cancel.on_click = self.window.click_cancel
                self.components['button_cancel'] = btn_cancel
                self.window.add(btn_cancel)
            if 'information' not in self.components:
                c_msg = MultiLabel(0, 0, 1, 1, '',
                                   Alignment.LEFT, Alignment.CENTER, Style.SMALL)
                c_msg.name = 'information'
                c_msg.passthrough = True
                self.components['information'] = c_msg
                self.window.add(c_msg)
            
            # Final update & reposition
            button_spacer = 1
            btn_ok.position = (self.window.width - 120-self.padding, self.window.height - 30-self.padding+button_spacer)
            btn_cancel.position = (self.window.width - 60-self.padding, self.window.height - 30-self.padding+button_spacer)
            usable_height = self.window.height - self.header - btn_ok.height - 2 * self.padding+button_spacer
            usable_width = self.window.width - 2 * self.padding
            c_msg.size = (usable_width, max(1, usable_height))
            c_msg.position = (self.padding, self.header + self.padding)
            c_msg.text = self.content
            # Register components
            if hasattr(self.engine, 'bus'):
                self.engine.bus.register(c_icon)
                self.engine.bus.register(c_label)
                self.engine.bus.register(btn_ok)
                self.engine.bus.register(btn_cancel)
                self.engine.bus.register(c_msg)
        else: # window mode
            self.engine.bus.register(c_icon)
            self.engine.bus.register(c_label)
                

    def reset(self) -> None:
        self._layout_dialog()
        if self.parent:
            self.parent.reset()
        else:
            self.window.reset()

    def set_theme(self, base_hue: int = None) -> 'Gui':
        if hasattr(self.engine, 'bus'):
            theme = self.window.new_theme(base_hue)
            self.engine.bus.post(Packet(
                receiver=BROADCAST,
                sender=MASTER,
                rs=Response.M_THEME,
                data=theme
            ))
        return self
        
    