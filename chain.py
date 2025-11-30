import time
import random
import pygame
from pygame.event import Event
from typing import Optional, Tuple, Dict, Callable, Any, List, Set, TYPE_CHECKING
from bus import BROADCAST, MASTER, Response, Packet, AddressBus

if TYPE_CHECKING:
    from component import Component

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
        if not self.enabled:
            return False
        # container first (reverse, front-to-back)
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
            # deactivate siblings in container
            if self.parent:
                self.parent.deactivate_container(self)
            # trigger 'focus' if state changes
            if not self.active:
                self.active = True
                self.trigger('focus', event)
            self.trigger('click', event)
            return True
        elif self.active:
            # focus lost
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
        """Check if point is inside component bounds"""
        return self.get_absolute_rect().collidepoint(point)
    
    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Check if point is within this component or any children"""
        return self.is_inside(point) or any(
            child.contains_point(point) for child in self.children
        )
    
    # Geometry contract (must implement)
    def get_absolute_rect(self) -> pygame.Rect:
        raise NotImplementedError(f"Error: {self.name} is missing get_absolute_rect() override")
        
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
                hoster.bus.post(Packet(receiver=msg.sender,sender=self.address, rs=Response.M_OK, data=True))
                self.reset()
            elif msg.rs == Response.M_THEME:
                self.bg = pygame.Color(msg.data['bg'])
                self.fg = pygame.Color(msg.data['fg'])
                self.shade = pygame.Color(msg.data['shade'])
                self.font_small = pygame.Color(msg.data['font_small'])
                self.font_big = pygame.Color(msg.data['font_big'])
                self.reset()
class Theme:
    def __init__(self):
        # Border & Filler
        self.border = False
        self.border_style = 0  # 0: solid, 1: dashed, 2: dotted
        self.border_thickness = 1
        self.filler = False
        self.filler_style = 0 # 0-4: solid, dots, lines, crossed, gradient
        
        # Rendering
        self.surface: Optional[pygame.Surface] = None
        self.redraw = True
        
        # basics
        self.bg             = pygame.Color(90, 90, 90)
        self.fg             = pygame.Color(255, 255, 255)
        self.shade          = pygame.Color(70, 70, 70)
        
        # fonts
        self.font_big       = pygame.Color(255, 255, 255)
        self.font_small     = pygame.Color(155, 155, 155)
        self.font           = pygame.font.Font('./assets/JetBrainsMono-Regular.ttf', 12)
        self.fontS          = pygame.font.Font('./assets/JetBrainsMono-Bold.ttf', 9)
        self.fontB          = pygame.font.Font('./assets/JetBrainsMono-Bold.ttf', 15)
    
    def draw_locked(self, surface: pygame.Surface) -> None:
        abs_rect = self.get_absolute_rect()
        x, y, w, h = abs_rect
        pygame.draw.line(surface, (255,90,90), (x-1, y-1), (x-1 + w+1, y-1), 2)
        
    def draw_frame(self, surface: pygame.Surface) -> None:
        if not self.visible or not self.border:
            return
        
        abs_rect = self.get_absolute_rect()
        x, y, w, h = abs_rect
        color = self.fg
        thickness = self.border_thickness
        
        style = getattr(self, 'border_style', 0)
        
        if style == 0:
            # Solid
            pygame.draw.rect(surface, color, abs_rect, thickness)
        elif style == 1:
            # Dashed
            self._draw_dashed_rect(surface, abs_rect, color, thickness, dash_len=5, gap_len=3)
        elif style == 2:
            # Dotted
            self._draw_dashed_rect(surface, abs_rect, color, thickness, dash_len=1, gap_len=2)

    def _draw_dashed_rect(self, surface: pygame.Surface, rect: pygame.Rect, color: pygame.Color, thickness: int, dash_len: int, gap_len: int) -> None:
        x, y, w, h = rect
        # Top edge
        # Bottom edge
        # Left edge
        # Right edge
        self._draw_dashed_line(surface, (x, y), (x + w, y), color, thickness, dash_len, gap_len)
        self._draw_dashed_line(surface, (x, y + h - thickness), (x + w, y + h - thickness), color, thickness, dash_len, gap_len)
        self._draw_dashed_line(surface, (x, y), (x, y + h), color, thickness, dash_len, gap_len)
        self._draw_dashed_line(surface, (x + w - thickness, y), (x + w - thickness, y + h), color, thickness, dash_len, gap_len)

    def _draw_dashed_line(self, surface: pygame.Surface, start: Tuple[int, int], end: Tuple[int, int], color: pygame.Color, thickness: int, dash_len: int, gap_len: int) -> None:
        x1, y1 = start
        x2, y2 = end
        dx = x2 - x1
        dy = y2 - y1
        length = max(abs(dx), abs(dy))
        if length == 0:
            return

        # Normalize direction
        step_x = dx / length
        step_y = dy / length

        pos = 0.0
        drawing = True
        while pos < length:
            seg_len = dash_len if drawing else gap_len
            next_pos = min(pos + seg_len, length)
            
            if drawing:
                sx = int(x1 + pos * step_x)
                sy = int(y1 + pos * step_y)
                ex = int(x1 + next_pos * step_x)
                ey = int(y1 + next_pos * step_y)
                pygame.draw.line(surface, color, (sx, sy), (ex, ey), thickness)
            
            pos = next_pos
            drawing = not drawing
    
    def fill_region(self, surface: pygame.Surface, pattern: int = 0) -> None:
        abs_rect = self.get_absolute_rect()
        
        if pattern == 0:
            pygame.draw.rect(surface, self.bg, abs_rect)
        elif pattern == 1:
            for y in range(abs_rect.y, abs_rect.bottom, 4):
                pygame.draw.line(surface, self.shade, (abs_rect.x, y), (abs_rect.right, y), 1)
        elif pattern == 2:
            for y in range(abs_rect.y, abs_rect.bottom, 3):
                pygame.draw.line(surface, self.shade, (abs_rect.x, y), (abs_rect.right, y), 1)
            for x in range(abs_rect.x, abs_rect.right, 3):
                pygame.draw.line(surface, self.shade, (x, abs_rect.y), (x, abs_rect.bottom), 1)
        elif pattern == 3:
            for y in range(abs_rect.y + 2, abs_rect.bottom, 4):
                for x in range(abs_rect.x + 2, abs_rect.right, 4):
                    surface.set_at((x, y), self.shade)
        elif pattern == 4:
            for i, y in enumerate(range(abs_rect.y, abs_rect.bottom)):
                ratio = i / abs_rect.height
                color = self._color_lerp(self.shade, self.bg, ratio)
                pygame.draw.line(surface, color, (abs_rect.x, y), (abs_rect.right, y))

    def new_theme(self, base_hue: int = None) -> Dict[str, Tuple[int, int, int]]:
        if base_hue is None:
            base_hue = random.randint(0, 360)
        return {
            'fg':        Theme._hsl_to_rgb(base_hue, 80, 80),   # default foreground
            'bg':        Theme._hsl_to_rgb(base_hue, 20, 20),   # default background
            'shade':     Theme._hsl_to_rgb(base_hue, 45, 45),   # default shadow

            # Text
            'font_small': Theme._hsl_to_rgb(base_hue, 80, 80),  # default text
            'font_big':   Theme._hsl_to_rgb(base_hue, 90, 90),  # default header
            }
            
    def _color_lerp(self, color1: pygame.Color, color2: pygame.Color, ratio: float) -> pygame.Color:
        """Interpolate between two colors"""
        r = int(color1.r + (color2.r - color1.r) * ratio)
        g = int(color1.g + (color2.g - color1.g) * ratio)
        b = int(color1.b + (color2.b - color1.b) * ratio)
        return pygame.Color(r, g, b)
   
    @staticmethod
    def _hsl_to_rgb(h: int, s: int, l: int) -> Tuple[int, int, int]:
        """Convert HSL to RGB tuple"""
        h = h / 360.0
        s = s / 100.0
        l = l / 100.0
        
        if s == 0:
            rgb = l, l, l
        else:
            def hue_to_rgb(p, q, t):
                if t < 0: t += 1
                if t > 1: t -= 1
                if t < 1/6: return p + (q - p) * 6 * t
                if t < 1/2: return q
                if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                return p
            
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
            rgb = r, g, b
        
        return int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)