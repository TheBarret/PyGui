import time
import pygame
import random

from enum import IntEnum
from typing import List, Any, Dict, Tuple, Callable, Optional

from component import Component
from primitives import Button
from bus import BROADCAST, MASTER, Response, Packet, AddressBus


class DummyLoad(Component):
    def __init__(self, resistance: float = 1.0):
        super().__init__(0, 0, 0, 0)
        self.name = 'DummyLoad'
        self.visible = False
        self.resistance = resistance 
        self.processing_delay = 0.0
    
    def set_resistance(self, value: float):
        """Set resistance level (0.0 = no delay, higher = more delay)"""
        self.resistance = max(0.0, value)
    
    def process_event(self, event: pygame.event.Event) -> bool:
        """Add resistance to event processing"""
        self._apply_resistance()
        return super().process_event(event)
    
    def update(self, dt: float) -> None:
        """Add resistance to update cycle"""
        self._apply_resistance()
        super().update(dt)
    
    def handle_message(self, msg: Packet) -> None:
        """Add resistance to message handling"""
        self._apply_resistance()
        super().handle_message(msg)
    
    def _apply_resistance(self):
        """Apply processing delay based on resistance"""
        if self.resistance > 0:
            import random
            # Convert resistance to delay (0-50ms range based on resistance)
            max_delay = 0.050  # 50ms maximum
            base_delay = self.resistance * 0.010  # 10ms per resistance unit
            random_factor = random.uniform(0.5, 1.5)  # ±50% variation
            actual_delay = min(max_delay, base_delay * random_factor)
            
            if actual_delay > 0:
                time.sleep(actual_delay)

class Performance(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 30):
        super().__init__(x, y, width, height)
        self.name = 'Performance'
        self.filler = True
        self.filler_style = 0
        self.border = True
        self.border_style = 0
        
        # Data management
        self.window_data = {}  # address -> [time_series_data]
        self.max_points = width  # One point per pixel width
        self.graph_buffer = []  # Recent performance values
        self.update_interval = 1.0  # Update graph every 100ms
        self.last_update = 0
        
        # Visual settings
        self.graph_color = pygame.Color(0, 255, 0)  # Green for good performance
        self.warning_color = pygame.Color(255, 255, 0)  # Yellow for warning
        self.error_color = pygame.Color(255, 0, 0)  # Red for poor performance
        self.grid_color = pygame.Color(60, 60, 60)
        
        # Performance thresholds (in seconds)
        self.good_threshold = 0.250  
        self.warning_threshold = 0.300
        self.max_display_time = 0.500
    
    def handle_message(self, msg: Packet) -> None:
        super().handle_message(msg)
        
        if msg.rs == Response.M_PONG and msg.data and msg.data.get('type') == 'Window':
            # Calculate time since the message was generated
            current_time = time.time()
            if 'time' in msg.data:
                response_time = current_time - msg.data['time']
                self._add_performance_sample(response_time)
    
    def _add_performance_sample(self, response_time: float):
        """Add a new performance sample to the graph"""
        # Cap the response time for display purposes
        capped_time = min(response_time, self.max_display_time)
        self.graph_buffer.append(capped_time)
        
        # Keep only the last N points
        if len(self.graph_buffer) > self.max_points:
            self.graph_buffer.pop(0)
        
        self.redraw = True
    
    def update(self, dt: float) -> None:
        super().update(dt)
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            self.send_ping()
            self.last_update = current_time
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        super().draw(surface)
        
        if not self.graph_buffer:
            return
        
        abs_rect = self.get_absolute_rect()
        
        # Draw grid lines for reference
        self._draw_grid(surface, abs_rect)
        
        # Draw the performance graph
        self._draw_performance_curve(surface, abs_rect)
    
    def _draw_grid(self, surface: pygame.Surface, abs_rect: pygame.Rect):
        """Draw reference grid lines"""
        # Horizontal reference lines at 50ms and 100ms
        thresholds = [
            (self.warning_threshold, self.warning_color),
            (self.max_display_time / 2, self.grid_color),
        ]
        
        for threshold, color in thresholds:
            if threshold <= self.max_display_time:
                y_pos = abs_rect.bottom - (threshold / self.max_display_time) * abs_rect.height
                pygame.draw.line(surface, color, (abs_rect.left, y_pos), (abs_rect.right, y_pos), 1)
    
    def _draw_performance_curve(self, surface: pygame.Surface, abs_rect: pygame.Rect):
        """Draw the performance curve"""
        if len(self.graph_buffer) < 2:
            return
        
        # Draw line segments connecting each point
        points = []
        for i, response_time in enumerate(self.graph_buffer):
            x = abs_rect.left + i * (abs_rect.width / len(self.graph_buffer))
            y = abs_rect.bottom - (response_time / self.max_display_time) * abs_rect.height
            y = max(abs_rect.top, min(y, abs_rect.bottom))  # Clamp to bounds
            points.append((x, y))
        
        if len(points) > 1:
            # Draw the line with color based on performance
            for i in range(len(points) - 1):
                start_point = points[i]
                end_point = points[i + 1]
                
                # Choose color based on the first point's performance
                response_time = self.graph_buffer[i]
                if response_time < self.good_threshold:
                    color = self.graph_color
                elif response_time < self.warning_threshold:
                    color = self.warning_color
                else:
                    color = self.error_color
                
                pygame.draw.line(surface, color, start_point, end_point, 2)


class Pulsar(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 12, height: int = 12):
        super().__init__(x, y, width, height)
        self.name = 'Pulsar'
        self.filler = False
        self.border = True
        self.border_style = 2
        self.activity_timeout = 0.95
        self.activity_timer = 0.0
        self.is_active = False
        self.pulse_phase = 0.0
        self.pulse_speed = 15.0
        self.redraw = True
    
    def handle_message(self, msg: Packet) -> None:
        super().handle_message(msg)
        self._trigger_activity()
    
    def _trigger_activity(self):
        self.is_active = True
        self.activity_timer = self.activity_timeout
        self.pulse_phase = 0.0
        self.redraw = True
    
    def update(self, dt: float) -> None:
        super().update(dt)
        
        if self.is_active:
            self.activity_timer -= dt
            self.pulse_phase += dt * self.pulse_speed
            
            if self.activity_timer <= 0:
                self.is_active = False
            self.redraw = True
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        abs_rect = self.get_absolute_rect()

        if self.is_active:
            pulse_intensity = min(1.0, self.pulse_phase) if self.pulse_phase < 1.0 else 1.0
            # Fade out as timer decreases
            fade_factor = max(0.0, self.activity_timer / self.activity_timeout)
            pulse_intensity *= fade_factor
        else:
            pulse_intensity = 0.0
        
        # Create pulsing color
        r = int(255 * pulse_intensity)
        g = int(self.fg.g * pulse_intensity)
        b = int(self.fg.b * pulse_intensity)
        pulse_color = pygame.Color(r, g, b)
        
        # Draw the indicator
        if pulse_intensity > 0:
            pygame.draw.rect(surface, pulse_color, abs_rect)
        else:
            # Draw a dim indicator when not active
            dim_color = pygame.Color(30, 30, 30)
            pygame.draw.rect(surface, dim_color, abs_rect)
        
        if self.border:
            pygame.draw.rect(surface, self.fg, abs_rect, 1)
