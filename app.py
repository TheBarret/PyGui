from core import Engine
from window import Gui


# ─── Bootstrapper ───────────────────────────────────────────────────────────

sample = f'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n'
sample += 'Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.\n'
sample += 'Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.\n'
sample += 'Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'

if __name__ == "__main__":
    
    init = Engine(1000, 600, 60, 'init')
    
    for i in range(1, 3):
        dialog = (Gui(init)
              .create(50*i, 50*i, 350, 200)
              .as_dialog(f'Message {i}', sample)
              .build())
              
              
    for i in range(1, 3):
        window = (Gui(init)
                  .create(70*i, 70*i, 250, 220)
                  .as_window(f'Window {i}')
                  .build())
              
    init.set_theme(240)
    
    init.run()
    
    
    
