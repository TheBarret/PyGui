import pygame
import time
import math
import random
from typing import List, Any, Tuple, Callable
from component import Component
from bus import BROADCAST, Response, Packet, AddressBus

class Lister(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 150):
        super().__init__(x, y, width, height)
        self.name = 'Lister'
        self.passthrough_events = True
        self.lines = []
        self.font = pygame.font.Font('./assets/Chicago-12.ttf', 10)
        sample = self.font.render("abc", True, (255, 255, 255))
        self.line_height = sample.get_height() + 2
        self.max_lines = height // self.line_height
        self.column_width = 50
        self.bg = pygame.Color(0, 0, 0)
        self.fg = pygame.Color(255, 255, 255)
        self.shade = pygame.Color(220, 220, 220)
        self.font_small = pygame.Color(220, 220, 220)
        self.colors = {
            'INFO': pygame.Color(180, 180, 200),
            'API': pygame.Color(255, 255, 100), 
            'ERROR': pygame.Color(255, 100, 100)
        }

    def write(self, text: str, event: str = 'INFO') -> None:
        self.lines.append((event, str(text)))
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)
        self.reset()
    
    def clear(self) -> None:
        self.lines.clear()
        self.reset()
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        abs_rect = self.get_absolute_rect()
        pygame.draw.rect(surface, self.bg, abs_rect)
        pygame.draw.rect(surface, self.fg, abs_rect, 1)
        
        # Draw column separator
        sep_x = abs_rect.x + self.column_width
        pygame.draw.line(surface, (80, 80, 100), (sep_x, abs_rect.y), (sep_x, abs_rect.bottom), 1)
        
        # Draw text lines with columns
        y_offset = abs_rect.bottom - (len(self.lines) * self.line_height)
        max_msg_width = abs_rect.width - self.column_width - 10  # Available width for messages
        
        for i, (msg_type, line) in enumerate(self.lines):
            text_y = y_offset + (i * self.line_height)
            
            # Only draw if within bounds
            if text_y + self.line_height >= abs_rect.y:
                # Draw type in first column
                type_color = self.colors.get(msg_type, self.font_small)
                type_surface = self.font.render(msg_type, True, type_color)
                surface.blit(type_surface, (abs_rect.x + 5, text_y))
                
                # Draw message in second column (with clipping)
                msg_width = self.font.size(line)[0]
                if msg_width > max_msg_width:
                    # Find where to clip
                    for clip_pos in range(len(line), 0, -1):
                        clipped = line[:clip_pos] + "..."
                        if self.font.size(clipped)[0] <= max_msg_width:
                            line = clipped
                            break
                
                msg_surface = self.font.render(line, True, self.font_small)
                surface.blit(msg_surface, (sep_x + 5, text_y))
        
        super().draw(surface)
        
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
        if msg.rs == Response.M_UPDATE:
            self.bg = pygame.Color(msg.data['bg'])
            self.fg = pygame.Color(msg.data['fg'])
            self.font_small = pygame.Color(msg.data['font_small'])
            self.colors = {
            'INFO': pygame.Color(msg.data['INFO']),
            'API': pygame.Color(msg.data['API']), 
            'ERROR': pygame.Color(msg.data['ERROR'])
            }
            
        super().handle_message(msg)

class FPSMeter(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 80, height: int = 20):
        super().__init__(x, y, width, height)
        self.name = 'FPSMeter'
        self.passthrough_events = True
        self.font = pygame.font.Font('./assets/Chicago-12.ttf', 10)
        self.fps_samples = []
        self.max_samples = 30
        
    def update(self, dt: float) -> None:
        if dt > 0:
            current_fps = 1.0 / dt
            self.fps_samples.append(current_fps)
            if len(self.fps_samples) > self.max_samples:
                self.fps_samples.pop(0)
            self.reset()
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible or not self.fps_samples:
            return
            
        abs_rect = self.get_absolute_rect()
        avg_fps = sum(self.fps_samples) / len(self.fps_samples)
        
        # 8-bit style background
        pygame.draw.rect(surface, (20, 20, 30), abs_rect)
        pygame.draw.rect(surface, (80, 80, 100), abs_rect, 1)
        
        # FPS text with color coding
        fps_color = (100, 255, 100) if avg_fps > 50 else (255, 255, 100) if avg_fps > 30 else (255, 100, 100)
        fps_text = f"FPS:{avg_fps:04.1f}"
        text_surf = self.font.render(fps_text, True, fps_color)
        
        # Center text
        text_x = abs_rect.x + (abs_rect.width - text_surf.get_width()) // 2
        text_y = abs_rect.y + (abs_rect.height - text_surf.get_height()) // 2
        surface.blit(text_surf, (text_x, text_y))
        
        
class AnalogFPS(Component):
    def __init__(self, x: int = 0, y: int = 0, size: int = 64):
        super().__init__(x, y, size, size)
        self.name = 'AnalogFPS'
        self.passthrough_events = True
        self.fps_samples = []
        self.max_fps = 120
        self.bg = pygame.Color(0, 0, 0)
        self.fg = pygame.Color(255, 255, 255)
        self.shade = pygame.Color(60, 60, 80)
        self.font_small = pygame.Color(255, 255, 255)
        
    def update(self, dt: float) -> None:
        if dt > 0:
            self.fps_samples.append(1.0 / dt)
            if len(self.fps_samples) > 15:
                self.fps_samples.pop(0)
            self.reset()
    
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
        if msg.rs == Response.M_UPDATE:
            self.fg = pygame.Color(msg.data['fg'])
            self.bg = pygame.Color(msg.data['bg'])
            self.shade = pygame.Color(msg.data['shade'])
            self.font_small = pygame.Color(msg.data['font_small'])
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible or not self.fps_samples:
            return
            
        abs_rect = self.get_absolute_rect()
        center = abs_rect.center
        radius = min(abs_rect.width, abs_rect.height) // 2 - 5
        avg_fps = sum(self.fps_samples) / len(self.fps_samples)
        
        # Gauge background (8-bit circle)
        pygame.draw.circle(surface, self.bg, center, radius)
        pygame.draw.circle(surface, self.fg, center, radius, 2)
        
        # Tick marks (chunky 8-bit style)
        for angle in range(-135, 136, 27):  # 10° increments
            rad = math.radians(angle)
            start_x = center[0] + (radius-5) * math.cos(rad)
            start_y = center[1] + (radius-5) * math.sin(rad)
            end_x = center[0] + radius * math.cos(rad)
            end_y = center[1] + radius * math.sin(rad)
            pygame.draw.line(surface, self.fg, (start_x, start_y), (end_x, end_y), 2)
        
        # Needle (chunky pixelated)
        fps_ratio = min(avg_fps / self.max_fps, 1.0)
        angle = -135 + (fps_ratio * 270)  # -135° to +135°
        rad = math.radians(angle)
        end_x = center[0] + (radius-8) * math.cos(rad)
        end_y = center[1] + (radius-8) * math.sin(rad)
        
        # Thick 8-bit needle
        pygame.draw.line(surface, self.font_small, center, (end_x, end_y), 1)
        
        # Center pivot (big pixel)
        pygame.draw.circle(surface, self.font_small, center, 4)