import pygame
import time
import random
from typing import List, Any, Tuple, Callable
from component import Component
from bus import BROADCAST, Response, Packet, AddressBus

class Node(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 120, height: int = 80):
        super().__init__(x, y, width, height)
        self.name = 'Node'
        self.passthrough_events = False
        self.inputs = []  # List of input terminals
        self.outputs = []  # List of output terminals  
        self.node_color = pygame.Color(80, 80, 120)
        self.terminal_radius = 6
        self.terminal_spacing = 20
        self.value = None  # Current node value
        
    def initialize(self) -> None:
        """Setup inputs/outputs - override in subclasses"""
        # Default: one input, one output
        self.add_input("in")
        self.add_output("out")
        
    def add_input(self, name: str) -> 'Terminal':
        """Add an input terminal on left side"""
        terminal = Terminal(0, 0, name, is_input=True)
        terminal.name = f'Input_{name}'
        # Position inputs on left edge
        y_pos = 20 + (len(self.inputs) * self.terminal_spacing)
        terminal.position = (2, y_pos)
        self.inputs.append(terminal)
        self.add(terminal)
        return terminal
        
    def add_output(self, name: str) -> 'Terminal':
        """Add an output terminal on right side"""
        terminal = Terminal(0, 0, name, is_input=False)
        terminal.name = f'Output_{name}'
        # Position outputs on right edge  
        y_pos = 20 + (len(self.outputs) * self.terminal_spacing)
        terminal.position = (self.width - 12, y_pos)
        self.outputs.append(terminal)
        self.add(terminal)
        return terminal
        
    def process(self, input_values: dict) -> any:
        """Override this with node-specific logic"""
        # Default: pass through first input
        return input_values.get('in') if input_values else None
        
    def execute(self) -> any:
        """Execute node logic and return output"""
        # Gather input values
        input_vals = {}
        for i, terminal in enumerate(self.inputs):
            if terminal.connected_to:
                input_vals[terminal.name] = terminal.connected_to.value
        
        # Process and set output
        self.value = self.process(input_vals)
        
        # Propagate to outputs
        for terminal in self.outputs:
            terminal.value = self.value
            
        return self.value
        
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        abs_rect = self.get_absolute_rect()
        
        # Node body (rounded rect)
        pygame.draw.rect(surface, self.node_color, abs_rect, border_radius=8)
        pygame.draw.rect(surface, (120, 120, 160), abs_rect, 2, border_radius=8)
        
        # Node title
        font = pygame.font.Font(None, 12)
        title = font.render(self.name, True, (220, 220, 220))
        title_x = abs_rect.x + (abs_rect.width - title.get_width()) // 2
        surface.blit(title, (title_x, abs_rect.y + 5))
        
        super().draw(surface)