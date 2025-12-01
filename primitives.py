import pygame
import time
import random
from enum import IntEnum
from typing import List, Any, Dict, Tuple, Callable, Optional

from component import Component
from bus import BROADCAST, MASTER, Response, Packet, AddressBus

# Pre-load fonts
pygame.font.init()

# Globals

class Alignment(IntEnum):
    CENTER = 0
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4

class Style(IntEnum):
    NORMAL = 0
    SMALL = 1
    BIG = 2
    
"""    
    Primitive Components
    
"""

# Placeholder component

class Container(Component):
    def __init__(self, x: int = 0, y: int = 0,  width: int = 90, height: int = 45):
        super().__init__(x, y, width, height)
        self.name = 'Container'
            
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        super().draw(surface)

# Functional components

class Label(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 100, height: int = 24, text: str = "",
                 align: Alignment = Alignment.LEFT, valign: Alignment = Alignment.CENTER,
                 style: Style = Style.NORMAL):
        super().__init__(x, y, width, height)
        self.name = 'Label'
        self._text = ""
        self.padding = 4
        self.text_align = align
        self.text_valign = valign
        self.text_style = style
        self._font = self.fontB if self.text_style == Style.BIG else \
                     self.fontS if self.text_style == Style.SMALL else \
                     self.font
        self.text = text
        self.filler = True
        self.filler_style = 4

    @property
    def text(self) -> str:
        return self._text
    
    @text.setter
    def text(self, value: str):
        value = str(value) if value else ""
        if self._text == value:
            return
        self._text = value
        self.reset()

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        # filler first
        super().draw(surface)
        
        # text last
        if self.text:
            text_surf = self._font.render(self.text, True, self.fg)
            text_rect = text_surf.get_rect()
            
            abs_rect = self.get_absolute_rect()
            
            # Horizontal alignment
            if self.text_align == Alignment.LEFT:
                text_rect.left = abs_rect.left + self.padding
            elif self.text_align == Alignment.RIGHT:
                text_rect.right = abs_rect.right - self.padding
            else:  # center
                text_rect.centerx = abs_rect.centerx
            
            # Vertical alignment
            if self.text_valign == Alignment.TOP:
                text_rect.top = abs_rect.top + self.padding
            elif self.text_valign == Alignment.BOTTOM:
                text_rect.bottom = abs_rect.bottom - self.padding
            else:  # center
                text_rect.centery = abs_rect.centery
            
            # Clip to bounds
            surface.blit(text_surf, text_rect)
        
        

class MultiLabel(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 200, height: int = 100, text: str = "",
                 align: Alignment = Alignment.CENTER, valign: Alignment = Alignment.CENTER,
                 style: Style = Style.NORMAL):
        super().__init__(x, y, width, height)
        self.name = 'MultiLabel'
        self._text = ""
        self._lines = []
        self.padding = 2
        self.line_spacing = 2
        self.text_align = align
        self.text_valign = valign
        self.text_style = style
        self._font = self.fontB if self.text_style == Style.BIG else \
                     self.fontS if self.text_style == Style.SMALL else \
                     self.font
        self.text = text
        self.filler = True
        self.filler_style = 0
        self.border = True
        self.border_style = 2

    @property
    def text(self) -> str:
        return self._text
    
    @text.setter
    def text(self, value: str):
        value = str(value) if value else ""
        if self._text == value:
            return
        self._text = value
        self._update_lines()
        self.reset()

    def _update_lines(self) -> None:
        """Precompute wrapped lines — called only on text/size change"""
        self._lines = []
        if not self._text:
            return

        avail_width = max(0, self.width - 2 * self.padding)
        if avail_width <= 0:
            return

        # Split into paragraphs (preserve \n)
        paragraphs = self._text.split('\n')
        for para in paragraphs:
            if not para:
                self._lines.append("")
                continue
            
            words = para.split(' ')
            current_line = ""
            
            for word in words:
                # Test adding this word to current line
                test_line = f"{current_line} {word}".strip() if current_line else word
                test_width = self._font.size(test_line)[0]
                
                if test_width <= avail_width:
                    current_line = test_line
                else:
                    # If current line is empty, this word is too long for any line
                    if not current_line:
                        # Force break the long word
                        current_line = self._break_long_word(word, avail_width)
                        self._lines.append(current_line)
                        current_line = ""
                    else:
                        # Current line fits, but adding word doesn't - add current line and start new
                        self._lines.append(current_line)
                        current_line = word
            
            if current_line:
                self._lines.append(current_line)

    def _break_long_word(self, word: str, max_width: int) -> str:
        """Break a word that's too long for the available width"""
        if not word:
            return word
        
        # Binary search for the longest substring that fits
        left, right = 0, len(word)
        best = 0
        
        while left <= right:
            mid = (left + right) // 2
            test = word[:mid] + "…"
            if self._font.size(test)[0] <= max_width:
                best = mid
                left = mid + 1
            else:
                right = mid - 1
        
        if best == 0:
            return word[:1] + "…" if len(word) > 1 else word
        elif best == len(word):
            return word
        else:
            return word[:best] + "…"

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible or not self._lines:
            return
        # filler first
        super().draw(surface)
        
        # text last
        abs_rect = self.get_absolute_rect()
        line_height = self._font.get_height() + self.line_spacing

        # Vertical start (respect valign)
        total_text_height = len(self._lines) * line_height - self.line_spacing
        if self.text_valign == Alignment.TOP:
            y = abs_rect.top + self.padding
        elif self.text_valign == Alignment.BOTTOM:
            y = abs_rect.bottom - self.padding - total_text_height
        else:  # center
            y = abs_rect.centery - total_text_height // 2

        # Clip rendering to self bounds
        old_clip = surface.get_clip()
        try:
            surface.set_clip(abs_rect)
            for line in self._lines:
                if y + line_height < abs_rect.top:
                    y += line_height
                    continue  # skip off-top lines
                if y > abs_rect.bottom:
                    break    # stop at bottom

                # Render line
                text_surf = self._font.render(line, True, self.fg)
                text_rect = text_surf.get_rect()

                if self.text_align == Alignment.LEFT:
                    text_rect.left = abs_rect.left + self.padding
                elif self.text_align == Alignment.RIGHT:
                    text_rect.right = abs_rect.right - self.padding
                else:  # center
                    text_rect.centerx = abs_rect.centerx

                text_rect.top = y
                surface.blit(text_surf, text_rect)
                y += line_height
        finally:
            surface.set_clip(old_clip)

class Button(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 80, height: int = 30, text: str = "OK",
                 align: Alignment = Alignment.CENTER, valign: Alignment = Alignment.CENTER,
                 style: Style = Style.SMALL):
        super().__init__(x, y, width, height)
        self.name = 'Button'
        self.filler = True
        self.filler_style = 0
        self.border = True
        self.border_style = 0
        self.text = text
        self.padding = 4
        self.text_style = style
        self.text_align = align
        self.text_valign = valign
        self.on_click: Optional[Callable[[], None]] = self._null
        self._font = self.fontB if self.text_style == Style.BIG else \
                     self.fontS if self.text_style == Style.SMALL else \
                     self.font
    
    def _null(self) -> None:
        return
        
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active and self.is_inside(event.pos):
                if self.on_click:
                    self.on_click()
                return True
        return super().process_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        super().draw(surface)
        
        abs_rect = self.get_absolute_rect()
        if self.text:
            # Clip text to self bounds (uses active font + padding)
            max_width = self.width - 2 * self.padding
            raw_text = self.text
            text_width = self._font.size(raw_text)[0]
            
            if text_width > max_width:
                ellipsis = "…"
                ellipsis_w = self._font.size(ellipsis)[0]
                avail = max(0, max_width - ellipsis_w)
                display = ellipsis
                for i in range(len(raw_text), 0, -1):
                    trial = raw_text[:i]
                    if self._font.size(trial)[0] <= avail:
                        display = trial + ellipsis
                        break
            else:
                display = raw_text
            
            text_surf = self._font.render(display, True, self.font_small)
            text_rect = text_surf.get_rect()
            if self.text_align == Alignment.LEFT:
                text_rect.left = abs_rect.left + self.padding
            elif self.text_align == Alignment.RIGHT:
                text_rect.right = abs_rect.right - self.padding
            else:
                text_rect.centerx = abs_rect.centerx
            
            if self.text_valign == Alignment.TOP:
                text_rect.top = abs_rect.top + self.padding
            elif self.text_valign == Alignment.BOTTOM:
                text_rect.bottom = abs_rect.bottom - self.padding
            else:
                text_rect.centery = abs_rect.centery
            
            surface.blit(text_surf, text_rect)

class Toolbar(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 400, height: int = 24,
                 h_align: Alignment = Alignment.LEFT, v_align: Alignment = Alignment.CENTER):
        super().__init__(x, y, width, height)
        self.name = 'HorizontalStrip'
        self.filler = True
        self.filler_style = 0
        self.border = True
        self.border_style = 1
        self.spacing = 4
        self.padding = 4
        self.auto_reposition = True
        
        # Alignment properties
        self.h_align = h_align  # Horizontal alignment for items
        self.v_align = v_align  # Vertical alignment for items
        
    def add(self, child: 'Component') -> None:
        super().add(child)
        if self.auto_reposition:
            self.reposition_items()
    
    def remove(self, child: 'Component') -> None:
        super().remove(child)
        if self.auto_reposition:
            self.reposition_items()
    
    def reposition_items(self) -> None:
        if not self.children:
            return

        total_content_width = sum(child.width for child in self.children) + \
                             (len(self.children) - 1) * self.spacing
        
        if self.h_align == Alignment.LEFT:
            current_x = self.padding
        elif self.h_align == Alignment.RIGHT:
            current_x = self.width - self.padding - total_content_width
        else:  # CENTER
            current_x = self.padding + (self.width - 2 * self.padding - total_content_width) // 2
        
        current_x = max(self.padding, current_x)  # Ensure not negative
        
        for child in self.children:
            child.x = current_x
            
            available_height = self.height - 2 * self.padding
            if self.v_align == Alignment.TOP:
                child.y = self.padding
            elif self.v_align == Alignment.BOTTOM:
                child.y = self.height - self.padding - child.height
            else:  # CENTER
                child.y = self.padding + (available_height - child.height) // 2
            
            child.y = max(self.padding, min(child.y, self.height - child.height - self.padding))
            current_x += child.width + self.spacing
            if current_x > self.width - self.padding:
                child.visible = False
            else:
                child.visible = True
            if child.height > self.height - 2 * self.padding:
                child.height = self.height - 2 * self.padding
 
class Slider(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = 100, height: int = 20, 
                 min_val: float = 0, max_val: float = 100, initial_val: float = 50,
                 on_change: Callable[[float], None] = None):
        super().__init__(x, y, width, height)
        self.name = 'Slider'
        self.filler = True
        self.filler_style = 0
        self.border = True
        self.border_style = 0
        self.padding = 2
        
        # Slider properties
        self.min_value = min_val
        self.max_value = max_val
        self.value = initial_val
        self.on_change = on_change
        
        # Interaction
        self.dragging = False
        self.knob_size = min(15, height - 4)
        self.knob_x = self._value_to_position(self.value)
        
        # Visual
        self.knob_color = self.fg
        self.track_color = self.shade
    
    def _value_to_position(self, value: float) -> int:
        """Convert value to knob x position"""
        normalized = (value - self.min_value) / (self.max_value - self.min_value)
        return int(self.padding + normalized * (self.width - 2 * self.padding - self.knob_size))
    
    def _position_to_value(self, x: int) -> float:
        """Convert position to value"""

        abs_rect = self.get_absolute_rect()
        local_x = x - abs_rect.x
        max_range = self.width - 2 * self.padding - self.knob_size
        relative_x = max(0, min(local_x - self.padding, max_range))
        
        # Normalize to 0-1 range
        if max_range <= 0:
            normalized = 0.0
        else:
            normalized = relative_x / max_range
        
        # Convert to actual value range
        return self.min_value + normalized * (self.max_value - self.min_value)
    
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            abs_rect = self.get_absolute_rect()
            
            # Check if click is on knob
            knob_rect = pygame.Rect(self.knob_x, abs_rect.y + (abs_rect.height - self.knob_size) // 2, 
                                   self.knob_size, self.knob_size)
            
            if knob_rect.collidepoint(event.pos):
                self.dragging = True  # Start dragging the knob
                return True
            # Check if click is on track (jump to position and start dragging)
            elif abs_rect.collidepoint(event.pos):
                self.knob_x = event.pos[0] - abs_rect.x - self.knob_size // 2
                self.knob_x = max(self.padding, min(self.knob_x, 
                                                  self.width - self.knob_size - self.padding))
                self.value = self._position_to_value(self.knob_x + abs_rect.x)
                if self.on_change:
                    self.on_change(self.value)
                self.dragging = True  # Start dragging after jump to position
                self.reset()
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
                
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            abs_rect = self.get_absolute_rect()
            self.knob_x = event.pos[0] - abs_rect.x - self.knob_size // 2
            self.knob_x = max(self.padding, min(self.knob_x, 
                                              self.width - self.knob_size - self.padding))
            self.value = self._position_to_value(self.knob_x + abs_rect.x)
            if self.on_change:
                self.on_change(self.value)
            self.reset()
            return True
            
        return super().process_event(event)
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        super().draw(surface)
        
        abs_rect = self.get_absolute_rect()
        
        # Draw track
        track_y = abs_rect.centery
        track_height = 4
        pygame.draw.line(surface, self.track_color, 
                        (abs_rect.left + self.padding, track_y),
                        (abs_rect.right - self.padding, track_y), track_height)
        
        # Draw knob
        knob_rect = pygame.Rect(
            abs_rect.left + self.knob_x,
            abs_rect.centery - self.knob_size // 2,
            self.knob_size, 
            self.knob_size
        )
        pygame.draw.rect(surface, self.knob_color, knob_rect)
        pygame.draw.rect(surface, self.fg, knob_rect, 1)