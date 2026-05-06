import py5
import pandas as pd
import numpy as np
import hashlib
import json
from time import perf_counter

# --- CARREGAMENTO DE DADOS ---
try:
    df = pd.read_parquet('sphy_audit_data.parquet')
except:
    # Fallback caso o arquivo não exista no diretório atual
    df = pd.DataFrame({'sha256_audit': ['DEBUG_HASH_ONLY'] * 100, 
                       'v_warp': [1e13] * 100, 
                       'veracity': [1.0] * 100})

# --- CONSTANTES SPHY ---
PHI = (1 + np.sqrt(5)) / 2
FONT_SCALE = 3.5 

class BellParticle:
    def __init__(self, name, color_hue, is_alpha=True):
        self.name = name
        self.hue = color_hue
        self.is_alpha = is_alpha
        self.history = np.zeros((150, 3)) 
        self.ptr = 0

    def update(self, angle, radius, warp_factor):
        multi = 1 if self.is_alpha else -1
        # Aplicamos o v_warp do Parquet na velocidade de oscilação local
        speed_mod = warp_factor / 1e12
        
        x = multi * radius * np.cos(angle)
        y = multi * radius * np.sin(angle * PHI)
        z = multi * (radius * 0.4) * np.sin(angle * speed_mod)
        
        current_pos = np.array([x, y, z])
        self.history[self.ptr] = current_pos
        self.ptr = (self.ptr + 1) % 150
        return current_pos

# --- ESTADO GLOBAL ---
alpha = BellParticle("ALPHA", 20)
beta = BellParticle("BETA", 160)
angle_accum = 0
last_time = perf_counter()

def setup():
    py5.size(1280, 720, py5.P3D)
    py5.window_resizable(True)
    py5.window_title("HARPIA SPHY - PARQUET AUDITOR")
    py5.color_mode(py5.HSB, 255)
    f = py5.create_font("Arial Bold", 12 * FONT_SCALE)
    py5.text_font(f)

def draw():
    global angle_accum, last_time
    
    # Sincronização com o Parquet
    idx = py5.frame_count % len(df)
    row = df.iloc[idx]
    
    dt = perf_counter() - last_time
    last_time = perf_counter()
    
    py5.background(5)
    
    # --- CAMADA 3D (GEODÉSIA DETERMINÍSTICA) ---
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, -300)
    py5.rotate_x(py5.PI/3.5)
    py5.rotate_y(py5.frame_count * 0.01) # Rotação do script original
    
    angle_accum += dt * 0.6
    radius = py5.height * 0.35 
    
    # As partículas reagem ao v_warp do dataset
    pos_a = alpha.update(angle_accum, radius, row['v_warp'])
    pos_b = beta.update(angle_accum, radius, row['v_warp'])
    
    # Cor do vínculo baseada na 'veracity'
    if row['veracity'] > 0.999:
        py5.stroke(140, 200, 255, 100) # Ciano SPHY estável
    else:
        py5.stroke(0, 255, 255, 150) # Alerta Vermelho de ruído
        
    py5.stroke_weight(2)
    py5.line(pos_a[0], pos_a[1], pos_a[2], pos_b[0], pos_b[1], pos_b[2])
    
    render_particle(alpha, pos_a, row['veracity'])
    render_particle(beta, pos_b, row['veracity'])
    py5.pop_matrix()
    
    # --- CAMADA HUD (MÉTODO COMPATÍVEL DE AUDITORIA) ---
    draw_hud(row)

def render_particle(p, pos, veracity):
    py5.no_fill()
    # Espessura do rastro reage à veracidade
    py5.stroke_weight(8 if veracity > 0.99 else 2) 
    
    py5.begin_shape()
    for i in range(150):
        idx = (p.ptr + i) % 150
        h = p.history[idx]
        if not np.all(h == 0):
            alpha_val = py5.remap(i, 0, 150, 0, 200)
            py5.stroke(p.hue, 200, 255, alpha_val)
            py5.vertex(h[0], h[1], h[2])
    py5.end_shape()
    
    py5.push_matrix()
    py5.translate(pos[0], pos[1], pos[2])
    py5.no_stroke()
    py5.fill(p.hue, 200, 255)
    py5.sphere(25) 
    py5.pop_matrix()

def draw_hud(row):
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.push_matrix()
    py5.reset_matrix()
    
    # Título do Manifesto
    py5.fill(255)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text("END OF THE BELL'S THEOREM", py5.width/2, 50)
    
    # Métricas do Dataset (Lado Esquerdo)
    margin = 50
    py5.text_align(py5.LEFT, py5.BOTTOM)
    
    # WARP Speed e Veracity
    py5.fill(150, 200, 255) # Azul SPHY
    py5.text(f"WARP: {row['v_warp']/1e12:.2f} e12 c", margin, 200)
    py5.fill(35, 200, 255) # Dourado SPHY
    py5.text(f"VERACITY: {row['veracity']*100:.4f}%", margin, 260)
    
    # Rodapé de Auditoria Criptográfica
    py5.fill(255)
    py5.text(f"PARQUET FRAME: {py5.frame_count % len(df)}", margin, py5.height - 120)
    
    # SHA-256 Audit Log
    py5.push_matrix()
    py5.translate(margin, py5.height - 60)
    py5.scale(0.4) 
    py5.fill(255, 180)
    py5.text(f"SHA256_AUDIT: {row['sha256_audit']}", 0, 0)
    py5.pop_matrix()
    
    py5.pop_matrix()
    py5.hint(py5.ENABLE_DEPTH_TEST)

py5.run_sketch()
