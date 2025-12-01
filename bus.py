# bus.py
from enum import IntEnum
from dataclasses import dataclass
from typing import Any, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from component import Component

# multicast address
BROADCAST = -1
MASTER = 0


class Response(IntEnum):
    # generic (dialog) states
    M_OK = 0
    M_ERR = 1
    M_BUSY = 2
    M_CANCEL = 3

    # discovery
    M_PING = 10     # get local metadata
    M_PONG = 11     # metadata reply
    
    # management
    M_REDRAW = 20   # force redraw
    M_SHUTDOWN = 21 # kill switch
    M_THEME = 22    # redraw theme
    M_CONTRAST = 23 # update contrast
    
    # advertisers
    M_BYE = 30      # component closure
    M_LOCK = 31     # component lock
    M_SNAP = 32     # component snap
    M_PULSE = 33     # component is touched
    

@dataclass(frozen=True)
class Packet:
    receiver: int
    sender: int
    rs: Response = Response.M_OK
    data: Any = None


class AddressBus:
    __slots__ = (
        "_messages",
        "_components",
        "_next_addr",
        "_max_queue_size",
    )

    def __init__(self, max_queue_size: int = 255):
        self._messages: List[Packet] = []
        self._components: Dict[int, 'Component'] = {}
        self._next_addr = 0
        self._max_queue_size = max_queue_size

    
    # Registration
    
    def register(self, component: 'Component') -> int:
        addr = getattr(component, "address", -1)
        if addr < 0:
            addr = self._next_addr
            self._next_addr += 1
            component.address = addr
        
        self._components[addr] = component
        print(f'[added] 0x{component.address}: {component.name}({component.rect})')
        return addr

    def unregister(self, component: 'Component') -> None:
        self._components.pop(component.address, None)
        print(f'[removed] 0x{component.address}: {component.name}({component.rect})')
    
    # Posting
    def post(self, msg: Packet) -> bool:
        """Queue a message; return False if full."""
        if len(self._messages) >= self._max_queue_size:
            return False
        self._messages.append(msg)
        return True

    # Pump
    def pump(self) -> None:
        """Process all queued messages in FIFO order."""
        queue = self._messages
        if not queue:
            return

        self._messages = []

        for msg in queue:
            if msg.receiver == BROADCAST:
                # Snapshot list to allow safe mutation during dispatch
                targets = list(self._components.values())
                for comp in targets:
                    handler = getattr(comp, "handle_message", None)
                    if handler:
                        handler(msg)
            else:
                comp = self._components.get(msg.receiver)
                if comp:
                    handler = getattr(comp, "handle_message", None)
                    if handler:
                        handler(msg)

    
    # Peek
    def peek(self, address: int) -> List[Packet]:
        """Return queued messages targeted to `address` or broadcast."""
        return [
            m for m in self._messages
            if m.receiver == address or m.receiver == BROADCAST
        ]
