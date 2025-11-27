import pygame
import time
import random
from typing import List, Any, Tuple, Callable
from component import Component
from bus import BROADCAST, Response, Packet, AddressBus

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
        self.bus.post(Packet(
            receiver=BROADCAST,
            sender=self.address,
            rs=Response.M_SHUTDOWN,
            data=None
        ))
        super().destroy()
        
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
        if msg.rs == Response.M_TERM:
            defunkt = msg.data
            if defunkt:
                self.remove(defunkt)
        super().handle_message(msg)
