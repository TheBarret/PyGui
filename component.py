# component.py
import time
import pygame
from typing import Optional, Tuple, Dict, Callable, Any, List, Set, TYPE_CHECKING
from bus import BROADCAST, Response, Packet, AddressBus

if TYPE_CHECKING:
    from component import Component

class Component:
    def __init__(self, x: int = 0, y: int = 0, width: int = 128, height: int = 64):
        self.rect = pygame.Rect(x, y, max(1, width), max(1, height))
        self.visible = self.enabled = True
        self.active = False
        self.highlight = False
        self.passthrough = False
        self.parent: Optional['Component'] = None
        self.children: List['Component'] = []
        self.bus = None
        self.address = -1
        self.events: Dict[str, List[Callable]] = {event: [] for event in ['click', 'hover', 'focus', 'blur', 'keypress']}
        self.redraw = True
        self.surface: Optional[pygame.Surface] = None
    
    # RENDER & DRAW
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        for child in self.children:
            child.draw(surface)

    def update(self, dt: float) -> None:
        for child in self.children: child.update(dt)
    
    # MANAGEMENT
    
    def add(self, child: 'Component') -> None:
        if child.parent: child.parent.remove(child)
        self.children.append(child)
        child.parent = self
        self.reset()
    
    def remove(self, child: 'Component') -> None:
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            self.reset()
    
    def root(self) -> 'Component':
        if not hasattr(self, '_root_cache'):
            self._root_cache = self if self.parent is None else self.parent.root()
        return self._root_cache
    
    def register_all(self, bus: AddressBus) -> None:
        """Recursively register this component and all children with bus"""
        bus.register(self)
        for child in self.children:
            # Recursive call
            child.register_all(bus)
    
    def get_metadata(self) -> dict:
        return {
            'name': getattr(self, 'name', '?'),
            'type': self.__class__.__name__,
            'length': len(self.children),
            'ts': time.time()
        }
        
    def handle_message(self, msg: Packet) -> None:
        hoster = self.root()
        if hoster:
            # avoid loopback
            if msg.sender == self.address:
                return
            # discovery protocol
            if msg.rs == Response.M_PING:
                hoster.bus.post(Packet(receiver=msg.sender,sender=self.address, rs=Response.M_PONG, data=self.get_metadata()))
            elif msg.rs == Response.M_SHUTDOWN:
                self.destroy()
            elif msg.rs == Response.M_REDRAW:
                hoster.bus.post(Packet(receiver=msg.sender,sender=self.address, rs=Response.M_OK, data=self.get_metadata()))
                self.reset()
    
    # UTILITIES
    
    def get_absolute_rect(self) -> pygame.Rect:
        x, y = self.rect.topleft
        parent = self.parent
        while parent:
            x += parent.rect.x
            y += parent.rect.y
            parent = parent.parent
        return pygame.Rect(x, y, self.rect.width, self.rect.height)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled: return False
        for child in reversed(self.children):
            if child.handle_event(event): return True
        return self.process_event(event)
    
    def process_event(self, event: pygame.event.Event) -> bool:
        if self.passthrough:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_inside(event.pos):
                # deactivate hierarchy
                if self.parent and not self.active:
                    self.parent.deactivate_container(self)
                self.trigger('click', event)
                self.active = True
                self.trigger('focus', event)
                return True
            elif self.active:
                # lost focus
                self.active = False
                self.trigger('blur', event)
        
        elif event.type == pygame.MOUSEMOTION and self.is_inside(event.pos):
            self.trigger('hover', event)
            return True
        
        elif event.type == pygame.KEYDOWN and self.active:
            self.trigger('keypress', event)
            return True
        
        return False
    
    def is_inside(self, point: tuple[int, int]) -> bool:
        return self.get_absolute_rect().collidepoint(point)

    def on(self, event_type: str, handler: Callable) -> None:
        if event_type in self.events: self.events[event_type].append(handler)
    
    def off(self, event_type: str, handler: Callable) -> None:
        if event_type in self.events:
            self.events[event_type] = [h for h in self.events[event_type] if h != handler]
    
    def trigger(self, event_type: str, event: pygame.event.Event) -> None:
        for handler in self.events[event_type]: handler(self, event)
    
    def reset(self) -> None:
        self.redraw = True
        if self.parent: self.parent.reset()

    def reset_cache(self):
        if hasattr(self, '_root_cache'):
            del self._root_cache
        for child in self.children:
            child.reset_cache()
  
    def destroy(self) -> None:
        for child in self.children[:]: child.destroy()
        self.children.clear()
        self.parent = None

    def contains_point(self, point: tuple[int, int]) -> bool:
        return self.is_inside(point) or any(child.contains_point(point) for child in self.children)
    
    def bring_to_front(self) -> None:
        if self.parent:
            self.parent.children.remove(self)
            self.parent.children.append(self)
            self.parent.reset()
    
    def send_to_back(self) -> None:
        if self.parent:
            self.parent.children.remove(self)
            self.parent.children.insert(0, self)
            self.parent.reset()

    def deactivate_container(self, root: 'Component' = None) -> None:
        for child in self.children:
            if child != root and child.active:
                child.active = False
                child.trigger('blur', pygame.event.Event(pygame.USEREVENT))

    # PROPERTIES
    
    @property
    def x(self) -> int: return self.rect.x
    @x.setter
    def x(self, value: int): self.rect.x = value; self.reset()
    
    @property
    def y(self) -> int: return self.rect.y
    @y.setter
    def y(self, value: int): self.rect.y = value; self.reset()
    
    @property
    def width(self) -> int: return self.rect.width
    @width.setter
    def width(self, value: int): self.rect.width = max(1, value); self.reset()
    
    @property
    def height(self) -> int: return self.rect.height
    @height.setter
    def height(self, value: int): self.rect.height = max(1, value); self.reset()
    
    @property
    def position(self) -> Tuple[int, int]: return (self.rect.x, self.rect.y)
    @position.setter
    def position(self, value: Tuple[int, int]): self.rect.x, self.rect.y = value; self.reset()
    
    @property
    def size(self) -> Tuple[int, int]: return (self.rect.width, self.rect.height)
    @size.setter
    def size(self, value: Tuple[int, int]): self.rect.width, self.rect.height = max(1, value[0]), max(1, value[1]); self.reset()
    
    

