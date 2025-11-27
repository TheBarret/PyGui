import pygame
import time
import math
import random
from typing import List, Any, Tuple, Callable
from component import Component
from bus import BROADCAST, Response, Packet, AddressBus

class Analog(Component):
    def __init__(self, x: int = 0, y: int = 0, size: int = 64):
        super().__init__(x, y, size, size)
        self.name = 'Analog'
        self.passthrough_events = True
        self.fps_samples = []
        self.max_fps = 120
        
    def update(self, dt: float) -> None:
        if dt > 0:
            self.fps_samples.append(1.0 / dt)
            if len(self.fps_samples) > 10:
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
        # Gauge background
        pygame.draw.circle(surface, self.bg, center, radius)
        pygame.draw.circle(surface, self.fg, center, radius, 1)
        # Tick marks
        for angle in range(-135, 136, 27):  # 10° increments
            rad = math.radians(angle)
            start_x = center[0] + (radius-5) * math.cos(rad)
            start_y = center[1] + (radius-5) * math.sin(rad)
            end_x = center[0] + radius * math.cos(rad)
            end_y = center[1] + radius * math.sin(rad)
            pygame.draw.line(surface, self.fg, (start_x, start_y), (end_x, end_y), 1)
        # Needle
        fps_ratio = min(avg_fps / self.max_fps, 1.0)
        angle = -135 + (fps_ratio * 270)  # -135° to +135°
        rad = math.radians(angle)
        end_x = center[0] + (radius-8) * math.cos(rad)
        end_y = center[1] + (radius-8) * math.sin(rad)
        # needle
        pygame.draw.line(surface, self.font_small, center, (end_x, end_y), 2)
        