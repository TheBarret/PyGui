import pygame
import time
import random
from typing import List, Any, Dict, Tuple, Callable

from component import Component
from primitives import Alignment, Style
from primitives import Container, Label, MultiLabel, Button, Toolbar

from bus import BROADCAST, MASTER, Response, Packet, AddressBus

# Window Layers

class WindowRoot(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150, title: str = 'Window', fixed: bool = False):
        super().__init__(x, y, width, height)
        self.name = 'Window'
        self.caption = title
        
class WindowManagement(WindowRoot):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150, title: str = 'Window', fixed: bool = False):
        super().__init__(x, y, width, height)
        self.dragging = False
        self.drag_offset = (0, 0)
        self.can_move = not fixed
        self.can_snap = True
        self.can_close = True
    
    def toggle_snap(self) -> None:
        self.can_snap = not self.can_snap
        hoster = self.root()
        if hasattr(hoster, 'bus'):
            hoster.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.address,
                rs=Response.M_SNAP,
                data=self.get_metadata()
            ))
    def toggle_theme(self) -> None:
        hoster = self.root()
        theme = self.new_theme(-1, random.random())
        if hasattr(hoster, 'bus'):
            hoster.bus.post(Packet(
                receiver=BROADCAST,
                sender=MASTER,
                rs=Response.M_THEME,
                data=theme
            ))
    
    def toggle_lock(self) -> None:
        self.can_move = not self.can_move
        hoster = self.root()
        if hasattr(hoster, 'bus'):
            hoster.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.address,
                rs=Response.M_LOCK,
                data=self.get_metadata()
            ))

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        if not self.can_move:
            self.border_style = 0
        elif self.dragging:
            self.border_style = 1
        else:
            self.border_style = 0
            
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
                hoster = self.root()
                if hasattr(hoster, 'bus'):
                    hoster.bus.post(Packet(
                        receiver=BROADCAST,
                        sender=self.address,
                        rs=Response.M_PULSE,
                        data=self.get_metadata()
                    ))
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
        
    def hitbox_test(self, point: tuple[int, int], hitbox_y: int = 0) -> bool:
        """Check if click is within header area"""
        if not self.is_inside(point):
            return False
        abs_rect = self.get_absolute_rect()
        local_y = point[1] - abs_rect.y
        return local_y < self.height - hitbox_y
        
    def snap_on(self, threshold: int = 10) -> None:
        if not self.parent or not self.can_snap:
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
                
class Window(WindowManagement):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150, title: str = 'Window', fixed: bool = False):
        super().__init__(x, y, width, height)
        self.filler = True
        self.filler_style = 0
        self.border = True
        self.border_style = 0
        
    def destroy(self) -> None:
        if self.can_close:
            hoster = self.root()
            if hasattr(hoster, 'bus'):
                hoster.bus.post(Packet(receiver=BROADCAST,sender=self.address, rs=Response.M_BYE, data=self))
            super().destroy()
    
    
            

        
    