import pygame
import time
import random
from typing import List, Any, Dict, Tuple, Callable

from component import Component
from bus import BROADCAST, Response, Packet, AddressBus

# Primitives

class Panel(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150):
        super().__init__(x, y, width, height)
        self.name = 'Panel'
        
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        src_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, self.bg, src_rect)
        pygame.draw.rect(surface, self.fg, src_rect, 1)
        super().draw(surface)

class Label(Component):
    def __init__(self, x: int = 0, y: int = 0, text: str = "Label", font_size: int = 12):
        self.font = pygame.font.Font('./assets/Chicago-12.ttf', font_size)
        text_width, text_height = self.font.size(text)
        super().__init__(x, y, text_width + 10, text_height + 6)
        self.name = 'Label'
        self.text = text
            
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        abs_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, self.bg, abs_rect)
        pygame.draw.rect(surface, self.fg, abs_rect, 1)
        
        text_surface = self.font.render(self.text, True, self.font_big)
        text_x = abs_rect.x + (abs_rect.width - text_surface.get_width()) // 2
        text_y = abs_rect.y + (abs_rect.height - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))
        super().draw(surface)
   
class Icon(Component):
    def __init__(self, x: int = 0, y: int = 0, image_path: str = "", size: int = 16):
        self.icon_size = size
        try:
            original_image = pygame.image.load('./assets/' + image_path).convert_alpha()
            self.image = pygame.transform.scale(original_image, (size, size))
        except:
            # Fallback: create a colored square
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(self.image, self.bg, (0, 0, size, size))
        
        super().__init__(x, y, size, size)
        self.name = 'Icon'
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        abs_rect = self.get_absolute_rect()
        surface.blit(self.image, abs_rect.topleft)
        pygame.draw.rect(surface, self.bg, abs_rect, 1)
        super().draw(surface)
        
class Workspace(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 400, height: int = 300):
        super().__init__(x, y, width, height)
        self.name = 'Workspace'
       
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        abs_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, self.bg, abs_rect)
        pygame.draw.rect(surface, self.fg, abs_rect, 1)
        super().draw(surface)

# Window Base

class Window(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150, title: str = 'Window', fixed: bool = False):
        super().__init__(x, y, width, height)
        self.name = 'Window'
        self.caption = title
        self.dragging = False
        self.drag_offset = (0, 0)
        self.can_move = not fixed
        
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
            new_x = event.pos[0] - self.drag_offset[0]
            new_y = event.pos[1] - self.drag_offset[1]
            self.position = (new_x, new_y)
            return True
            
        return super().process_event(event)
    
    def hitbox_test(self, point: tuple[int, int], hitbox_y: int = 0) -> bool:
        """Check if click is within header area"""
        if not self.is_inside(point):
            return False
        abs_rect = self.get_absolute_rect()
        local_y = point[1] - abs_rect.y
        return local_y < self.height - hitbox_y
        
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        abs_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, self.bg, abs_rect)
        pygame.draw.rect(surface, self.fg, abs_rect, 1)
        super().draw(surface)

class Status(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 400, height: int = 20):
        super().__init__(x, y, width, height)
        self.name = 'Status'

        # Status metrics
        self.bus_activity = 0  # 0-1 scale
        self.status_text = '|'
        
        # Activity indicators
        self.bus_active = False
        self.bus_activity_timer = 0
        
        # Discovery protocol
        self.echo_timer = 0
        self.echo_clock = 1.0  # 1Hz
        self.active_components = 0
        # animation sequence
        self.echo_loop = ['[|...]','[.|..]','[..|.]','[...|]', '[..|.]', '[.|..]', '[|...]']
        self.echo_index = 0
        
        # font (default)
        self.font = pygame.font.Font('./assets/Chicago-12.ttf', 10)
        
    def update(self, dt: float) -> None:
        if self.bus_active:
            # 300ms highlight
            self.bus_activity_timer = 0.3
            self.bus_active = False
            
        if self.bus_activity_timer > 0:
            self.bus_activity_timer -= dt
                
        self.echo_timer += dt
        if self.echo_timer >= self.echo_clock:
            self._solliciate()
        
        if self.active_components > 0:
            self.echo_timer = 0
            self.active_components -= 2
            self.echo_index = (self.echo_index + 1) % len(self.echo_loop)

        _r = self.root()
        ar = _r.get_absolute_rect()
        hb_symbol = self.echo_loop[self.echo_index]
        self.set_status(f'{_r.name} | {_r.fps} | {_r.dt:.2f} | X{ar.x} Y{ar.x} | W{ar.w} H{ar.h} | {hb_symbol}')
            
        super().update(dt)
    
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
            
        if msg.rs == Response.M_PONG:
            self.bus_active = True
            self.active_components += 1
            
        super().handle_message(msg)
        
    def set_status(self, text: str) -> None:
        self.status_text = text
        
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        abs_rect = self.get_absolute_rect()
        
        # Draw background
        pygame.draw.rect(surface, self.bg, abs_rect)
        pygame.draw.rect(surface, self.fg, abs_rect, 1)
        
        # Draw status text
        status_surface = self.font.render(self.status_text, True, self.font_small)
        surface.blit(status_surface, (abs_rect.x + 5, abs_rect.y + (abs_rect.height - status_surface.get_height()) // 2))
        
        # Draw metrics
        metrics_x = abs_rect.right - 10
        
        # Bus activity indicator
        bus_color = self._get_bus_color()
        bus_rect = pygame.Rect(metrics_x - 10, abs_rect.y + 5, 10, 10)
        pygame.draw.rect(surface, bus_color, bus_rect)
        pygame.draw.rect(surface, self.fg, bus_rect, 1)
        
        super().draw(surface)
        
    def _get_bus_color(self) -> pygame.Color:
        if self.bus_activity_timer > 0:
            intensity = int(255 * (self.bus_activity_timer / 0.3))
            return pygame.Color(intensity, 10, 10)
        else:
            return self.bg
    
    def _solliciate(self) -> None:
        host = self.root()
        if host and hasattr(host, 'bus'):
            host.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.address,
                rs=Response.M_PING,
                data=True
            ))
            
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
            self.window.register_all(self.engine.bus)
            self.engine.add(self.window)
            self.engine.bus.post(Packet(receiver=BROADCAST,sender=self.window.address, rs=Response.M_PING, data=True))
        else:
            print('warning: missing messenger')
        return self

class Gui(WindowBase):
    def __init__(self, engine: Component):
        super().__init__(engine)
        self.font_size = 12
        self.status_size = 20
        self.components = {}
        
    def with_caption(self, text: str) -> 'Gui':
        if self.window:
            label = Label(0, 0, text, self.font_size)
            label.passthrough = True
            self.components['caption'] = label
            self.window.add(label)
        return self
        
    def with_workspace(self) -> 'Gui':
        if self.window:
            ws = Workspace(0, 0, self.window.width, self.window.height)
            ws.passthrough = False
            self.components['workspace'] = ws
            self.window.add(ws)
        return self
        
    def with_debugger(self) -> 'Gui':
        if self.window:
            statusbar = Status(0, 0, self.window.width, self.status_size)
            statusbar.passthrough = True
            self.components['debugger'] = statusbar
            self.window.add(statusbar)
        return self
        
    def with_random_theme(self, base_hue: int = None) -> 'Gui':
        if self.window and hasattr(self.engine, 'bus'):
            theme = self.window.next_theme(base_hue)
            self.engine.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.window.address,
                rs=Response.M_UPDATE,
                data=theme
            ))
        return self
        
    def arrange(self) -> 'Gui':
        """Auto-arrange components within window bounds"""
        if not self.window:
            return self
            
        window_rect = self.window.rect
        current_y = 0
        
        # Caption
        if 'caption' in self.components:
            caption = self.components['caption']
            caption.position = (0, current_y)
            caption.width = window_rect.width
            current_y += caption.height
        
        # Debugger
        debugger_height = 0
        if 'debugger' in self.components:
            debugger = self.components['debugger']
            debugger_height = debugger.height
            debugger.position = (0, window_rect.height - debugger_height)
            debugger.width = window_rect.width
        
        # Workspace
        if 'workspace' in self.components:
            workspace = self.components['workspace']
            workspace_height = window_rect.height - current_y - debugger_height
            workspace.position = (0, current_y)
            workspace.size = (window_rect.width, max(0, workspace_height))
            
        return self