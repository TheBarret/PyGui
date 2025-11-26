import pygame
import time
import random
from typing import List, Any, Tuple, Callable
from component import Component
from bus import BROADCAST, Response, Packet, AddressBus

class Panel(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150):
        super().__init__(x, y, width, height)
        self.name = 'Panel'
        self.bg = pygame.Color(0, 0, 0)
        self.fg = pygame.Color(255, 255, 255)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        src_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, self.bg, src_rect)
        pygame.draw.rect(surface, self.fg, src_rect, 1)
        super().draw(surface)

    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
        if msg.rs == Response.M_UPDATE:
            self.bg = pygame.Color(msg.data['bg'])
            self.fg = pygame.Color(msg.data['fg'])
        super().handle_message(msg)

class Label(Component):
    def __init__(self, x: int = 0, y: int = 0, text: str = "Label", font_size: int = 12):
        self.font = pygame.font.Font('./assets/Chicago-12.ttf', font_size)
        text_width, text_height = self.font.size(text)
        super().__init__(x, y, text_width + 10, text_height + 6)
        self.name = 'Label'
        self.text = text
        self.font_big = pygame.Color(255, 255, 255)
        self.bg = pygame.Color(0, 0, 0)
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        abs_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, self.bg, abs_rect)
        text_surface = self.font.render(self.text, True, self.font_big)
        text_x = abs_rect.x + (abs_rect.width - text_surface.get_width()) // 2
        text_y = abs_rect.y + (abs_rect.height - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))
        super().draw(surface)
    
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
        if msg.rs == Response.M_UPDATE:
            self.bg = pygame.Color(msg.data['bg'])
            self.font_big = pygame.Color(msg.data['font_big'])
        super().handle_message(msg)
    
class Icon(Component):
    def __init__(self, x: int = 0, y: int = 0, image_path: str = "", size: int = 16):
        self.icon_size = size
        self.bg = pygame.Color(0, 0, 0)
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
        
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
        if msg.rs == Response.M_UPDATE:
            self.bg = pygame.Color(msg.data['bg'])
                
        super().handle_message(msg)
        
class MenuStrip(Component):
    def __init__(self, height: int = 24):
        super().__init__(3, 1, 0, height)
        self.name = 'MenuStrip'
        self.menu_items = []
        self.item_height = height
        self.fg = pygame.Color(255, 255, 255)
        
    def initialize(self) -> None:
        if self.parent:
            # Position below header (assuming header is first child)
            header = self.parent.children[0] if self.parent.children else None
            if header:
                self.y = header.height
                self.width = self.parent.width
        
    def add_menu(self, text: str, callback: Callable = None) -> 'MenuItem':
        x_pos = sum(item.width for item in self.menu_items)
        item = MenuItem(x_pos, 0, text, callback)
        item.name = f'Menu_{text}'
        self.add(item)
        self.menu_items.append(item)
        return item
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        abs_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, self.fg, abs_rect, 1)
        super().draw(surface)
        
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
        if msg.rs == Response.M_UPDATE:
            self.fg = pygame.Color(msg.data['fg'])
            
        
class MenuItem(Component):
    def __init__(self, x: int, y: int, text: str, callback: Callable = None):
        self.font = pygame.font.Font('./assets/Chicago-12.ttf', 11)
        text_width = self.font.size(text)[0] + 20  # Padding
        super().__init__(x, y, text_width, 24)
        self.text = text
        self.callback = callback
        self.hovered = False
        self.bg = pygame.Color(0, 0, 0)
        self.shade = pygame.Color(60, 60, 80)
        self.font_small = pygame.Color(255, 255, 255)
        
        
    def draw(self, surface: pygame.Surface) -> None:
        abs_rect = self.get_absolute_rect()
        
        # Background
        color = self.bg if self.hovered else self.shade
        pygame.draw.rect(surface, color, abs_rect)
        
        # Text
        text_surf = self.font.render(self.text, True, self.font_small)
        text_x = abs_rect.x + (abs_rect.width - text_surf.get_width()) // 2
        text_y = abs_rect.y + (abs_rect.height - text_surf.get_height()) // 2
        surface.blit(text_surf, (text_x, text_y))
        
        super().draw(surface)
    
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.is_inside(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            if self.callback:
                self.callback()
            return True
        return False
        
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
        if msg.rs == Response.M_UPDATE:
            self.bg = pygame.Color(msg.data['bg'])
            self.shade = pygame.Color(msg.data['shade'])
            self.font_small = pygame.Color(msg.data['font_small'])


class NodeTree(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 180, height: int = 400):
        super().__init__(x, y, width, height)
        self.name = 'NodeTree'
        self.passthrough_events = True
        self.nodes = {}  # address -> node_data
        self.selected_node = None
        self.font = pygame.font.Font('./assets/Chicago-12.ttf', 10)
        self.line_height = 16
        self.indent = 20
        self.bg = pygame.Color(0, 0, 0)
        self.fg = pygame.Color(0, 0, 0)
        self.shade = pygame.Color(60, 60, 80)
        self.font_small = pygame.Color(155, 155, 155)
        self.font_big = pygame.Color(255, 255, 255)
        
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
        if msg.rs == Response.M_PONG:
            self.nodes[msg.sender] = msg.data
        elif msg.rs == Response.M_UPDATE:
            self.bg = pygame.Color(msg.data['bg'])
            self.fg = pygame.Color(msg.data['fg'])
            self.shade = pygame.Color(msg.data['shade'])
            self.font_small = pygame.Color(msg.data['font_small'])
            self.font_big = pygame.Color(msg.data['font_big'])

        super().handle_message(msg)

    def _ping(self) -> None:
        hoster = self.root()
        if hoster:
            self.root().bus.post(Packet(
                                    receiver=BROADCAST,
                                    sender=self.address,
                                    rs=Response.M_PING,
                                    data=True
                                ))
          
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        abs_rect = self.get_absolute_rect()
        # Background
        pygame.draw.rect(surface, self.bg, abs_rect)
        pygame.draw.rect(surface, self.fg, abs_rect, 1)
        
        # Title
        title = self.font.render("Viewer", True, self.font_big)
        surface.blit(title, (abs_rect.x + 5, abs_rect.y + 5))
        
        # Draw node tree
        y_offset = abs_rect.y + 25
        
        # Root node (engine) - always first
        root_nodes = [addr for addr, data in self.nodes.items()]
        
        for addr in root_nodes:
            y_offset = self._draw_node(surface, addr, abs_rect.x, y_offset, 0)
    
    def _draw_node(self, surface, address, x, y, level) -> int:
        """Draw a node and return next y position"""
        if address not in self.nodes:
            return y
            
        node = self.nodes[address]
        indent_x = x + (level * self.indent)
        
        # Selection highlight
        if address == self.selected_node:
            pygame.draw.rect(surface, self.shade, 
                           (indent_x, y, self.width - indent_x + x, self.line_height))
        
        # Node text
        text = f"[{node['length']}] {node['type']}"
        text_surf = self.font.render(text, True, self.font_small)
        surface.blit(text_surf, (indent_x, y))
        
       
        y += self.line_height
        return y
    
    
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_inside(event.pos):
                # find node
                abs_rect = self.get_absolute_rect()
                rel_y = event.pos[1] - abs_rect.y - 25
                node_index = rel_y // self.line_height
                
                if node_index >= 0 and node_index < len(self.nodes):
                    addresses = list(self.nodes.keys())
                    self.selected_node = addresses[node_index]
                    self.reset()
                    return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if self.is_inside(event.pos):
                self._ping()
                return True
            
        return False
        
class Workspace(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 400, height: int = 300):
        super().__init__(x, y, width, height)
        self.name = 'Workspace'
        self.passthrough_events = False  # Should handle drops
        self.dropped_nodes = []         # Track placed components
        self.bg = pygame.Color(0, 0, 0)
        self.fg = pygame.Color(0, 0, 0)
        self.shade = pygame.Color(60, 60, 80)
        self.font_small = pygame.Color(255, 255, 255)
        
    def add_node(self, node_type: str, position: tuple = None) -> Component:
        if position is None:
            position = (self.width // 2, self.height // 2)  # Center
            
        node = self._create_node(node_type, position)
        if node:
            self.add(node)
            self.dropped_nodes.append(node)
            self.reset()
            return node
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        abs_rect = self.get_absolute_rect()
        
        # Workspace background
        pygame.draw.rect(surface, self.bg, abs_rect)
        pygame.draw.rect(surface, self.fg, abs_rect, 1)
        
        # Grid pattern for visual reference
        for x in range(0, abs_rect.width, 20):
            pygame.draw.line(surface, self.shade, 
                           (abs_rect.x + x, abs_rect.y),
                           (abs_rect.x + x, abs_rect.bottom), 1)
        for y in range(0, abs_rect.height, 20):
            pygame.draw.line(surface, self.shade,
                           (abs_rect.x, abs_rect.y + y),
                           (abs_rect.right, abs_rect.y + y), 1)
        
        super().draw(surface)
        
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
        if msg.rs == Response.M_UPDATE:
            self.bg = pygame.Color(msg.data['bg'])
            self.fg = pygame.Color(msg.data['fg'])
            self.shade = pygame.Color(msg.data['shade'])
            self.font_small = pygame.Color(msg.data['font_small'])
            
            
class Window(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150, title: str = 'Window', fixed: bool = False):
        super().__init__(x, y, width, height)
        self.name = 'Window'
        self.caption = title
        self.dragging = False
        self.drag_offset = (0, 0)
        self.can_move = not fixed
        
    def initialize(self) -> None:
        """Override this in subclasses to create custom layouts"""
        pass
        
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
    
    def hitbox_test(self, point: tuple[int, int]) -> bool:
        """Check if click is within header area"""
        if not self.is_inside(point):
            return False
        abs_rect = self.get_absolute_rect()
        local_y = point[1] - abs_rect.y
        return local_y < 30
        
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        abs_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, (50, 50, 60), abs_rect)
        pygame.draw.rect(surface, (100, 100, 120), abs_rect, 2)
        
        if self.dragging:
            header_rect = pygame.Rect(abs_rect.x, abs_rect.y, abs_rect.width, 30)
            pygame.draw.rect(surface, (80, 80, 100), header_rect)
        
        super().draw(surface)
        
