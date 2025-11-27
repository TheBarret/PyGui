from core import Engine
from primitives import Gui


# ─── Bootstrapper ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    
    init = Engine(1000, 600, 60, 'init')
    
    stack = (Gui(init)
              .create(10, 10, 600, 400)
              .with_caption('Console')
              .with_workspace()
              .with_debugger()
              .arrange()
              .with_random_theme())

    stack.build()
    init.run()
    
    
    
