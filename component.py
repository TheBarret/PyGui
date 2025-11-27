import time
import random
import pygame
from typing import Optional, Tuple, Dict, Callable, Any, List, Set, TYPE_CHECKING

from chain import Dispatcher, Messenger, Theme

if TYPE_CHECKING:
    from component import Component

class Component(Dispatcher, Messenger, Theme):
    def __init__(self, x: int = 0, y: int = 0, width: int = 128, height: int = 64):
        # initializer
        Dispatcher.__init__(self)
        Messenger.__init__(self)
        Theme.__init__(self)
        
        # allocate region
        self.rect = pygame.Rect(x, y, max(1, width), max(1, height))
        
    # MANAGEMENT
    def add(self, child: 'Component') -> None:
        if child.parent: 
            child.parent.remove(child)
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
    
    def destroy(self) -> None:
        for child in self.children[:]: 
            child.destroy()
        self.children.clear()
        self.parent = None
        self.terminated = True
    
    def reset(self) -> None:
        self.redraw = True
        if self.parent: 
            self.parent.reset()

    def reset_cache(self):
        if hasattr(self, '_root_cache'):
            del self._root_cache
        for child in self.children:
            child.reset_cache()
    
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

    # UTILITIES
    def get_absolute_rect(self) -> pygame.Rect:
        x, y = self.rect.topleft
        parent = self.parent
        while parent:
            x += parent.rect.x
            y += parent.rect.y
            parent = parent.parent
        return pygame.Rect(x, y, self.rect.width, self.rect.height)

    @staticmethod
    def next_theme(base_hue: int = None) -> Dict[str, Tuple[int, int, int]]:
        """Generate a harmonious pastel theme based on hue"""
        if base_hue is None:
            base_hue = random.randint(0, 360)
        
        return {
            'bg': Component._hsl_to_rgb(base_hue, 15, 12),        # Dark background
            'fg': Component._hsl_to_rgb(base_hue, 25, 25),        # Medium foreground  
            'shade': Component._hsl_to_rgb(base_hue, 20, 18),     # Border/shadow
            'font_small': Component._hsl_to_rgb(base_hue, 70, 85), # Light text
            'font_big': Component._hsl_to_rgb(base_hue, 80, 95),   # Bright text
        }
    
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
    def size(self, value: Tuple[int, int]): 
        self.rect.width, self.rect.height = max(1, value[0]), max(1, value[1])
        self.reset()