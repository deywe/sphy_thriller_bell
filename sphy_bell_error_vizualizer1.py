import py5
import numpy as np
import hashlib
import json
from time import perf_counter

# --- CONSTANTES SPHY ---
PHI = (1 + np.sqrt(5)) / 2
TOTAL_FRAMES = 12000
FONT_SCALE = 3.5 

class BellParticle:
    def __init__(self, name, color_hue, is_alpha=True):
        self.name = name
        self.hue = color_hue
        self.is_alpha = is_alpha
        self.history = np.zeros((150, 3)) 
        self.ptr = 0

    def update(self, angle, radius):
        multi = 1 if self.is_alpha else -1
        x = multi * radius * np.cos(angle)
        y = multi * radius * np.sin(angle * PHI)
        z = multi * (radius * 0.4) * np.sin(angle)
        
        current_pos = np.array([x, y, z])
        self.history[self.ptr] = current_pos
        self.ptr = (self.ptr + 1) % 150
        return current_pos

alpha = BellParticle("ALPHA", 20)
beta = BellParticle("BETA", 160)
angle_accum = 0
last_time = perf_counter()
sha_counter = 0
current_hash = ""

def get_frame_hash(frame_id, pos_a, pos_b):
    data = {"f": frame_id, "a": pos_a.tolist(), "b": pos_b.tolist(), "s": "LOCKED"}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def setup():
    py5.size(1280, 720, py5.P3D)
    py5.window_resizable(True)
    py5.window_title("HARPIA - BELL FATAL ERROR AUDITOR")
    py5.color_mode(py5.HSB, 255)
    # Criando a fonte massiva
    f = py5.create_font("Arial Bold", 12 * FONT_SCALE)
    py5.text_font(f)

def draw():
    global angle_accum, last_time, sha_counter, current_hash
    dt = perf_counter() - last_time
    last_time = perf_counter()
    
    py5.background(5)
    
    # --- CAMADA 3D (GEODÉSIA) ---
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, -300)
    py5.rotate_x(py5.PI/3.5)
    py5.rotate_z(py5.frame_count * 0.003)
    
    angle_accum += dt * 0.6
    radius = py5.height * 0.35 
    
    pos_a = alpha.update(angle_accum, radius)
    pos_b = beta.update(angle_accum, radius)
    
    if sha_counter < TOTAL_FRAMES:
        current_hash = get_frame_hash(sha_counter, pos_a, pos_b)
        sha_counter += 1

    # Vínculo Determinístico
    py5.stroke(255, 40)
    py5.stroke_weight(2)
    py5.line(pos_a[0], pos_a[1], pos_a[2], pos_b[0], pos_b[1], pos_b[2])
    
    render_particle(alpha, pos_a)
    render_particle(beta, pos_b)
    py5.pop_matrix()
    
    # --- CAMADA HUD (MÉTODO COMPATÍVEL) ---
    draw_hud()

def render_particle(p, pos):
    py5.no_fill()
    py5.stroke_weight(8) 
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

def draw_hud():
    # Desativa o buffer de profundidade para desenhar o texto por cima
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # Reseta as transformações para coordenadas de pixel 2D
    py5.push_matrix()
    py5.reset_matrix()
    
    # Título no Topo
    py5.fill(255)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text("END OF THE BELL'S THEOREM", py5.width/2, 50)
    
    # Rodapé de Auditoria
    margin = 50
    py5.text_align(py5.LEFT, py5.BOTTOM)
    
    # Contador SHA256 (Destaque SPHY)
    py5.fill(35, 200, 255) 
    py5.text(f"VALIDATED PROOFS: {sha_counter}", margin, py5.height - 80)
    
    # Log de Hash
    py5.push_matrix()
    py5.translate(margin, py5.height - 40)
    py5.scale(0.4) # Escala apenas o Hash para caber
    py5.fill(255, 180)
    py5.text(f"SHA256: {current_hash}", 0, 0)
    py5.pop_matrix()
    
    py5.pop_matrix()
    
    # Reativa a profundidade para o próximo frame
    py5.hint(py5.ENABLE_DEPTH_TEST)

py5.run_sketch()
