import pygame
import time
import json
import os
import random
import traceback
from typing import List, Any, Tuple, Callable, Optional
from component import Component
from bus import BROADCAST, MASTER, Response, Packet, AddressBus

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
        self.current_hue = 180.0
        self.current_contrast = 0.7
        self.profile = './assets/profile.json'
        
        
    def root(self) -> 'Component':
        return self
    
    def handle_message(self, msg: Packet) -> None:
        super().handle_message(msg)
    
    def add(self, child: 'Component') -> None:
        super().add(child)
        self.bus.register(child)
        print(f'[engine] created {child.name} at address {child.address}')
        
    def remove(self, child: 'Component') -> None:
        super().remove(child)
        self.bus.unregister(child)
        print(f'[engine] terminated {child.name} at address {child.address}')
        
    def run(self) -> None:
        closing = False
        self.running = True
        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.destroy()
                        closing = True
                        continue
                    #if not closing:
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
        except KeyboardInterrupt:
            print("Interrupted by user...")
            self.destroy()
        except Exception as e:
            print(f"Fatal:\n{e}")
            print(f"Stack:\n{traceback.format_exc()}")
            self.destroy()
        finally:
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
            data=self.get_metadata()
        ))
        super().destroy()
        
    def handle_message(self, msg: Packet) -> None:
        if msg.sender == self.address:
            return
            
        if msg.rs == Response.M_BYE:
            defunkt = msg.data
            if defunkt and defunkt.terminated:
                self.remove(defunkt)
                
        if not msg.rs == Response.M_PING:
            if msg.receiver  == BROADCAST:
                print(f'[engine] * <BROADCAST:{msg.rs.name}> {msg.data}')
            else:
                print(f'[engine] * <{msg.sender}:{msg.rs.name}> {msg.data}')
        
        super().handle_message(msg)
    
    def set_theme(self, hue: float, contrast: float) -> None:
        theme = self.new_theme(hue, contrast)
        self.bus.post(Packet(
            receiver=BROADCAST,
            sender=MASTER,
            rs=Response.M_THEME,
            data=theme
        ))
        
    def load_profile(self) -> bool:
        filepath = self.profile
        
        try:
            if not os.path.exists(filepath):
                print(f'[engine] * * profile not found: {filepath}, using defaults * *')
                # Set default values
                self.current_hue = 180
                self.current_contrast = 0.7
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            profile_data = profile.get('profile', {})
            
            self.current_hue = float(profile_data.get('hue', 180))
            self.current_contrast = float(profile_data.get('contrast', 0.7))
            self.set_theme(self.current_hue, self.current_contrast)
            
            print(f'[engine] * * profile loaded from {filepath} * * ')
            return True
            
        except Exception as e:
            print(f'Error: Failed to load theme profile: {e}')
            # Set defaults on error
            self.current_hue = 180
            self.current_contrast = 0.7
            self.current_saturation = 50
            self.text_brightness = 15
            return False
            
    def save_profile(self) -> bool:
        filepath = self.profile
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            profile = {
                'profile': {
                    'hue': getattr(self, 'hue', 180),
                    'contrast': getattr(self, 'contrast', 0.7),
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
            print(f'[engine] profile saved to {filepath}')
            return True
            
        except Exception as e:
            print(f'[engine] Failed to save theme profile: {e}')
            return False