from core import Engine
from builders import Gui

# ─── Bootstrapper ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    init = Engine(1000, 600, 60, 'init')
    
    # GUI callbacks
    def on_change_hue(value: float) -> None:
        init.set_theme(value, init.contrast)
    
    def on_change_contrast(value: float) -> None:
        init.set_theme(init.hue, value/100)

    # GUI stack
    window1 = (Gui(init)
              .make_window(10, 10, 200, init.height - 50, False, False)
              
              .add_header(f'UI Debugger', False)
              
              .add_toolbar(2)
              .add_label('Latency')
              .add_debug()
              
              .add_toolbar(2)
              .add_label('hue')
              .add_slider(1,360, on_change_hue)
              
              .add_toolbar(2)
              .add_label('contrast')
              .add_slider(1,100, on_change_contrast)
              .add_toolbar(2)
              .add_button('save', init.save_profile)
              .add_button('load', init.load_profile)
              
              .build())

    for i in range(1, 5):
        window2 = (Gui(init)
                  .make_window((init.width//2)-(i*1), (init.height//2)-(i*1), 200, 200)
                  .add_header(f'{i}')
                  .build())

    
    # set theme
    init.set_theme(20, 0.9)
    
    # run
    init.run()
    
    
    
    

