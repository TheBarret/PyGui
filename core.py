import pygame
import time
import random
from typing import List, Any, Tuple, Callable
from component import Component
from bus import BROADCAST, Response, Packet, AddressBus

from primitives import Panel, Label, Icon, NodeTree, MenuStrip, Workspace, Window
from gauges import Lister, FPSMeter, AnalogFPS
from logic import Node

# ─── Engine ───────────────────────────────────────────────────────────


class Engine(Component):
    def __init__(self, width: int = 800, height: int = 600, fps: int = 60, title: str = "Engine"):
        super().__init__(0, 0, width, height)
        pygame.init()
        pygame.display.set_caption(title)
        self.name = "engine"
        self.clock = pygame.time.Clock()
        self.surface: pygame.Surface = pygame.display.set_mode((width, height), 0)
        self.dt = 0.0
        self.fps = fps
        self.running = False
        self.bus = AddressBus()
        self.bus_freq = 0.2
        self.bus_accumulator = 0.0
        self.bus.register(self)
        
    def root(self) -> 'Component':
        return self
    
    def handle_message(self, msg: Packet) -> None:
        super().handle_message(msg)
    
    def add(self, child: 'Component') -> None:
        super().add(child)
        self.bus.register(child)
        
    def remove(self, child: 'Component') -> None:
        super().remove(child)
        self.bus.unregister(child)
        
    def run(self) -> None:
        self.running = True
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.destroy()
                    continue
                self.handle_event(event)
            
            self.dt = self.clock.tick(self.fps) / 1000.0
            
            # throttle bus pump
            self.bus_accumulator += self.dt
            if self.bus_accumulator >= self.bus_freq:
                self.bus.pump()
                self.bus_accumulator = 0.0
            
            self.update(self.dt)
            self.surface.fill((0, 0, 0))
            self.draw(self.surface)
            pygame.display.flip()
        
        pygame.quit()
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
                return True
        return super().handle_event(event)

    def destroy(self) -> None:
        self.running = False
        super().destroy()
        
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
        print(f'bus: rx={msg.sender} tx={msg.receiver} proto={msg.rs} {msg.data}')
        super().handle_message(msg)

# ─── Complex Components ──────────────────────────────────────────────────

class Application(Window):
    def __init__(self, x: int = 0, y: int = 0, width: int = 800, height: int = 600, title: str = 'App'):
        super().__init__(x, y, width, height, title)
        self.name = title
        
        # Layout constants
        self.header_height = 32
        self.footer_height = height // 4
        self.sidebar_width = width // 5
        
        # Component references
        self.menu = None
        self.sidebar = None
        self.workspace = None
        self.fps = None
        self.debugger = None
        
    def initialize(self) -> None:
        """Main initialization flow"""
        self._create_components()
        self._assemble_layout()
        self._setup_bus_communication()
        self._on_final()

    # internal routines
    
    def _create_components(self) -> None:
        """Create all UI components"""
        self.menu = self._create_menu()
        self.sidebar = self._create_sidebar()
        self.workspace = self._create_workspace()
        self.fps = self._create_fps_meter()
        self.debugger = self._create_debugger()

    def _create_menu(self) -> MenuStrip:
        menu = MenuStrip()
        menu.name = 'MainMenu'
        menu.add_menu("[X]", self._shutdown)
        menu.add_menu("|", self._null)
        menu.add_menu("[RST]", self._redraw)
        menu.add_menu("|", self._null)
        menu.add_menu("[FPS]", self._show_fps)
        menu.initialize()
        return menu

    def _create_sidebar(self) -> NodeTree:
        body_height = self.height - self.header_height - self.footer_height
        sidebar = NodeTree(1, self.header_height, self.sidebar_width, body_height - self.header_height - 2)
        sidebar.name = 'Sidebar'
        sidebar.passthrough = True
        return sidebar

    def _create_workspace(self) -> Workspace:
        body_height = self.height - self.header_height - self.footer_height
        workspace_width = self.width - self.sidebar_width - 2
        workspace = Workspace(self.sidebar_width, self.header_height, workspace_width, body_height - self.header_height - 1)
        workspace.name = 'Workspace'
        workspace.passthrough = True
        return workspace

    def _create_fps_meter(self) -> AnalogFPS:
        fps = AnalogFPS(self.width - 64, 2, 64)
        fps.name = 'FPSMeter'
        fps.passthrough = True
        return fps

    def _create_debugger(self) -> Lister:
        debugger = Lister(0, self.height - self.footer_height, self.width, self.footer_height)
        debugger.name = 'Debugger'
        debugger.passthrough = True
        return debugger

    # Layout
    
    def _assemble_layout(self) -> None:
        """Assemble all components into the window hierarchy"""
        header = self._create_header()
        body = self._create_body()
        
        # Add components to body
        body.add(self.menu)
        body.add(self.sidebar)
        body.add(self.workspace)
        body.add(self.fps)
        
        # Assemble window
        self.add(header)
        self.add(body)
        self.add(self.debugger)
        
        self.debugger.bring_to_front()

    def _create_header(self) -> Panel:
        header = Panel(0, 0, self.width, self.header_height)
        header.name = 'Header'
        header.passthrough = True
        
        title = Label(32, 2, self.caption, 12)
        title.name = 'Title'
        title.passthrough = True
        
        icon = Icon(5, 5, "window.png", 16)
        icon.name = 'Logo'
        icon.passthrough = True
        
        header.add(title)
        header.add(icon)
        return header

    def _create_body(self) -> Panel:
        body_height = self.height - self.header_height - self.footer_height
        body = Panel(0, self.header_height, self.width, body_height)
        body.name = 'Body'
        body.passthrough = False
        return body

    # Bus
    
    def _setup_bus_communication(self) -> None:
        """Register components and send initial discovery ping"""
        self.hoster = self.root()
        if self.hoster and hasattr(self.hoster, 'bus'):
            self.register_all(self.hoster.bus)
            self.hoster.bus.post(Packet(
                receiver=BROADCAST, 
                sender=self.address, 
                rs=Response.M_PING, 
                data=True
            ))
        else:
            self.debugger.write('Error: No bus instance found', 'ERROR')

    def _post(self, response: Response, payload: Any = True) -> None:
        """Helper for sending bus messages"""
        if self.hoster:
            self.hoster.bus.post(Packet(
                receiver=BROADCAST,
                sender=self.address,
                rs=response,
                data=payload
            ))

    # Menu Callbacks
    
    def _shutdown(self) -> None:
        self._post(Response.M_SHUTDOWN)

    def _redraw(self) -> None:
        self._post(Response.M_UPDATE, self._generate_theme())
        self._post(Response.M_REDRAW)

    def _show_fps(self) -> None:
        self.fps.visible = not self.fps.visible

    def _null(self) -> None:
        pass

    # Theme Generator
    
    def _generate_theme(self) -> dict:
        """Generate a new color theme"""
        hue = random.randint(0, 360)
        return {
            'bg':        self._hsl_to_rgb(hue, 16, 16),   # background
            'fg':        self._hsl_to_rgb(hue, 32, 32),   # foreground
            'shade':     self._hsl_to_rgb(hue, 24, 24),   # border
            'font_small': self._hsl_to_rgb(hue, 85, 85),  # paragraph text
            'font_big':   self._hsl_to_rgb(hue, 85, 85),  # header text
            'INFO':      self._hsl_to_rgb(hue, 16, 85),   # info text
            'API':       self._hsl_to_rgb(hue, 32, 85),   # api text
            'ERROR':     self._hsl_to_rgb(hue, 24, 85)    # error text
        }

    def _hsl_to_rgb(self, h: int, s: int, l: int) -> Tuple[int, int, int]:
        """Convert HSL color to RGB tuple"""
        h = h / 360.0
        s = s / 100.0  
        l = l / 100.0
        
        if s == 0:
            return int(l * 255), int(l * 255), int(l * 255)
            
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        
        r = self._hue_to_rgb(p, q, h + 1/3)
        g = self._hue_to_rgb(p, q, h)
        b = self._hue_to_rgb(p, q, h - 1/3)
        
        return int(r * 255), int(g * 255), int(b * 255)

    def _hue_to_rgb(self, p: float, q: float, t: float) -> float:
        """Helper for HSL conversion"""
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p

    # Lifecycle
    
    def _on_final(self) -> None:
        """Log startup information"""
        self.debugger.write(f'{self.name} - {self.width}x{self.height}')

    def handle_message(self, msg: Packet) -> None:
        """Handle incoming bus messages"""
        if msg.sender == self.address:
            return
        super().handle_message(msg)