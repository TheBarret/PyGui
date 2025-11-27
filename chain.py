import time
import pygame
from pygame.event import Event
from typing import Optional, Tuple, Dict, Callable, Any, List, Set, TYPE_CHECKING
from bus import BROADCAST, Response, Packet, AddressBus

class Dispatcher:
    def __init__(self):
        # states
        self.visible = True
        self.enabled = True
       
        # hierarchy
        self.parent: Optional['Component'] = None
        self.children: List['Component'] = []        

        # interaction
        self.active = False
        self.passthrough = False
        
        # events
        self.terminated = False
        self.events: Dict[str, List[Callable]] = {
            event: [] for event in ['click', 'hover', 'focus', 'blur', 'keypress']
        }
    
    # Core methods
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        for child in self.children:
            child.draw(surface)

    def update(self, dt: float) -> None:
        for child in self.children: 
            child.update(dt)
    
    # Event Propagation
    def handle_event(self, event: Event) -> bool:
        """Process event through hierarchy, returns True if event was consumed"""
        if not self.visible or not self.enabled:
            return False
            
        # Process children first (reverse order for front-to-back)
        for child in reversed(self.children):
            if child.handle_event(event):
                return True
                
        return self.process_event(event)
    
    def process_event(self, event: Event) -> bool:
        """Process event for this specific component"""
        if self.passthrough:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_mouse_click(event)
        elif event.type == pygame.MOUSEMOTION:
            return self._handle_mouse_motion(event)
        elif event.type == pygame.KEYDOWN and self.active:
            return self._handle_keypress(event)
            
        return False
    
    def _handle_mouse_click(self, event: Event) -> bool:
        """Handle mouse click events"""
        if self.is_inside(event.pos):
            # Deactivate other components in hierarchy
            if self.parent and not self.active:
                self.parent.deactivate_container(self)
                
            self.active = True
            self.trigger('click', event)
            self.trigger('focus', event)
            return True
        elif self.active:
            # Lost focus
            self.active = False
            self.trigger('blur', event)
            
        return False
    
    def _handle_mouse_motion(self, event: Event) -> bool:
        """Handle mouse motion events"""
        if self.is_inside(event.pos):
            self.trigger('hover', event)
            return True
        return False
    
    def _handle_keypress(self, event: Event) -> bool:
        """Handle keyboard events"""
        self.trigger('keypress', event)
        return True
    
    def deactivate_container(self, root=None) -> None:
        """Deactivate all children except the specified root"""
        for child in self.children:
            if child != root and child.active:
                child.active = False
                child.trigger('blur', pygame.event.Event(pygame.USEREVENT))
    
    # Event Registration API
    def on(self, event_type: str, handler: Callable) -> None:
        """Register event handler"""
        if event_type in self.events:
            self.events[event_type].append(handler)
    
    def off(self, event_type: str, handler: Callable) -> None:
        """Unregister event handler"""
        if event_type in self.events:
            self.events[event_type] = [h for h in self.events[event_type] if h != handler]
    
    def trigger(self, event_type: str, event: Event) -> None:
        """Trigger all handlers for event type"""
        for handler in self.events[event_type]:
            handler(self, event)
    
    # Geometry-dependent methods
    def is_inside(self, point: Tuple[int, int]) -> bool:
        """Check if point is inside component bounds - relies on Component.get_absolute_rect()"""
        return self.get_absolute_rect().collidepoint(point)
    
    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Check if point is within this component or any children"""
        return self.is_inside(point) or any(
            child.contains_point(point) for child in self.children
        )
        
class Messenger:
    def __init__(self):
        self.bus = None
        self.address = -1
    
    def register_all(self, bus: AddressBus) -> None:
        bus.register(self)
        for child in self.children:
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
            if msg.sender == self.address:
                return
            if msg.rs == Response.M_PING:
                hoster.bus.post(Packet(receiver=msg.sender,sender=self.address, rs=Response.M_PONG, data=self.get_metadata()))
            elif msg.rs == Response.M_SHUTDOWN:
                self.destroy()
            elif msg.rs == Response.M_REDRAW:
                hoster.bus.post(Packet(receiver=msg.sender,sender=self.address, rs=Response.M_OK, data=self.get_metadata()))
                self.reset()
            elif msg.rs == Response.M_UPDATE:
                self.bg = pygame.Color(msg.data['bg'])
                self.fg = pygame.Color(msg.data['fg'])
                self.shade = pygame.Color(msg.data['shade'])
                self.font_small = pygame.Color(msg.data['font_small'])
                self.font_big = pygame.Color(msg.data['font_big'])
                self.reset()
                
class Theme:
    def __init__(self):
        # Rendering
        self.surface: Optional[pygame.Surface] = None
        
        # Visual properties
        self.bg = pygame.Color(90, 25, 10)
        self.fg = pygame.Color(255, 255, 255)
        self.shade = pygame.Color(10, 10, 10)
        self.font_big = pygame.Color(255, 255, 255)
        self.font_small = pygame.Color(155, 155, 155)
        self.surface: Optional[pygame.Surface] = None
        self.redraw = True
