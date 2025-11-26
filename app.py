from core import Engine, Application
        
# ─── Bootstrapper ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    
    init = Engine(1000, 600, 60, 'Editor')
    ws = Application(0, 0, init.width, init.height, 'Workspace')
    
    init.add(ws)
    ws.initialize()
    
    init.run()
    