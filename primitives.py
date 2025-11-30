import pygame
import time
import random
from enum import IntEnum
from typing import List, Any, Dict, Tuple, Callable

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
            line = ""
            for word in words:
                test_line = f"{line} {word}".strip()
                if self._font.size(test_line)[0] <= avail_width:
                    line = test_line
                else:
                    if line:
                        self._lines.append(line)
                    line = word  # start new line
            if line:
                self._lines.append(line)

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
        consumed = super().process_event(event)
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active:
                if self.on_click:
                    self.on_click()
                return True
        return consumed

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

