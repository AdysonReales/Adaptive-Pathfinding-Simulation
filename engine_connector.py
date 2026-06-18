# engine_connector.py
import subprocess
import sys

class CppEngineConnector:
    def __init__(self):
        self.exe = './engine.exe' if sys.platform.startswith('win') else './engine'

    def calculate_path(self, w, h, start, goal, algo, walls):
        startupinfo = None
        if sys.platform.startswith('win'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        try:
            process = subprocess.Popen([self.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, startupinfo=startupinfo)
        except FileNotFoundError:
            return [], []
        
        data = f"{w} {h} {start[0]} {start[1]} {goal[0]} {goal[1]} {algo}\n"
        for wx, wy in walls: data += f"{wx} {wy}\n"
        data += "-1 -1\n"
        
        stdout, _ = process.communicate(input=data)
        
        path, evaluated = [], []
        for line in stdout.strip().split('\n'):
            tokens = line.split()
            if not tokens: continue
            if tokens[0] == "PATH": path.append((int(tokens[1]), int(tokens[2])))
            if tokens[0] == "EVAL": evaluated.append((int(tokens[1]), int(tokens[2])))
            
        return path, evaluated