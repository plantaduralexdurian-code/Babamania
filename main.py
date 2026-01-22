from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle, InstructionGroup
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition 
from random import random, uniform, choice
import math

BARRA_ALTURA = 90
EVENTO_DURACION = 20
MINI_SCALE = 2 / 3

class AgujeroNegro:
    def __init__(self, parent, x, y):
        self.parent = parent
        self.size = 80
        self.radio_succion = 350
        self.fuerza = 1600 
        self.pos = (x, y)
        self.tiempo_vida = 25.0
        
        self.group = InstructionGroup()
        self.color_aura = Color(0.6, 0.1, 1, 0.4)
        self.aura = Line(circle=(x, y, self.size/2 + 5), width=2)
        self.color_centro = Color(0, 0, 0, 1)
        self.circle = Ellipse(size=(self.size, self.size), pos=(x - self.size/2, y - self.size/2))
        
        self.group.add(self.color_aura)
        self.group.add(self.aura)
        self.group.add(self.color_centro)
        self.group.add(self.circle)
        self.parent.canvas.before.add(self.group)

    def update(self, dt, bolas):
        self.tiempo_vida -= dt
        self.size += 12 * dt 
        self.radio_succion += 8 * dt
        latido = math.sin(Clock.get_time() * 7) * 4
        current_s = self.size + latido
        self.circle.size = (current_s, current_s)
        self.circle.pos = (self.pos[0] - current_s/2, self.pos[1] - current_s/2)
        self.aura.circle = (self.pos[0], self.pos[1], current_s/2 + 6)
        
        for b in bolas[:]:
            bx, by = b.circle.pos[0] + b.size/2, b.circle.pos[1] + b.size/2
            dx = self.pos[0] - bx
            dy = self.pos[1] - by
            distancia = math.sqrt(dx**2 + dy**2)
            if distancia < self.size / 2:
                self.size += 2
                self.parent.stats_dict["absorbidas"] += 1 
                self.parent.eliminar_bola(b)
            elif distancia < self.radio_succion:
                fuerza_n = (self.fuerza / (distancia + 1))
                b.vx += dx * fuerza_n * dt
                b.vy += dy * fuerza_n * dt

        if self.tiempo_vida <= 0:
            self.parent.eliminar_agujero(self)

    def limpiar(self):
        self.parent.canvas.before.remove(self.group)

class Bola:
    def __init__(self, parent, x, y, rainbow=False, giant=False, mini=False):
        self.parent = parent
        self.base_size = uniform(25, 80)
        self.factor_actual = 2.0 if giant else (MINI_SCALE if mini else 1.0)
        self.size = self.base_size * self.factor_actual
        self.vx = uniform(-220, 220)
        self.vy = uniform(-220, 220)
        self.rainbow = rainbow
        self.hue = random()
        self.base_color = (uniform(0.3, 1), uniform(0.3, 1), uniform(0.3, 1))

        with parent.canvas.before:
            self.color_instr = Color(*self.base_color, 1)
            self.circle = Ellipse(size=(self.size, self.size))
            self.border_color_instr = Color(0, 0, 0, 1)
            self.border = Line(width=1)

        r = self.size / 2
        self.circle.pos = (x - r, y - r)
        self.actualizar_borde()

    def actualizar_borde(self):
        x, y = self.circle.pos
        r = self.size / 2
        self.border.circle = (x + r, y + r, r)

    def set_scale(self, nuevo_factor):
        centro_x = self.circle.pos[0] + self.size / 2
        centro_y = self.circle.pos[1] + self.size / 2
        self.factor_actual = nuevo_factor
        self.size = self.base_size * self.factor_actual
        self.circle.size = (self.size, self.size)
        r = self.size / 2
        self.circle.pos = (centro_x - r, centro_y - r)
        self.actualizar_borde()

    def update_color(self, dt):
        if self.rainbow:
            self.hue = (self.hue + dt * 0.15) % 1
            self.color_instr.hsv = (self.hue, 0.6, 1)
        else:
            self.color_instr.rgb = self.base_color

    def move(self, dt, speed):
        x, y = self.circle.pos
        x += self.vx * dt * speed
        y += self.vy * dt * speed
        
        if x <= 0: 
            x = 0; self.vx = abs(self.vx); self.parent.stats_dict["rebotes"] += 1
        elif x + self.size >= self.parent.width: 
            x = self.parent.width - self.size; self.vx = -abs(self.vx); self.parent.stats_dict["rebotes"] += 1
        if y <= BARRA_ALTURA: 
            y = BARRA_ALTURA; self.vy = abs(self.vy); self.parent.stats_dict["rebotes"] += 1
        elif y + self.size >= self.parent.height: 
            y = self.parent.height - self.size; self.vy = -abs(self.vy); self.parent.stats_dict["rebotes"] += 1
            
        self.circle.pos = (x, y); self.actualizar_borde()

    def limpiar(self):
        try:
            self.parent.canvas.before.remove(self.circle)
            self.parent.canvas.before.remove(self.border)
            self.parent.canvas.before.remove(self.color_instr)
            self.parent.canvas.before.remove(self.border_color_instr)
        except: pass

class BolaColisionable(Bola):
    def __init__(self, parent, x, y, **kwargs):
        super().__init__(parent, x, y, **kwargs)
        if not self.rainbow:
            self.base_color = (0.7, 0.7, 0.8)
            self.color_instr.rgb = self.base_color

    def move(self, dt, speed):
        super().move(dt, speed)
        for otra in self.parent.bolas:
            if otra is self: continue
            c1x, c1y = self.circle.pos[0] + self.size/2, self.circle.pos[1] + self.size/2
            c2x, c2y = otra.circle.pos[0] + otra.size/2, otra.circle.pos[1] + otra.size/2
            dx = c1x - c2x
            dy = c1y - c2y
            distancia = math.sqrt(dx*dx + dy*dy)
            min_dist = (self.size/2) + (otra.size/2)
            if distancia < min_dist:
                self.vx, otra.vx = otra.vx, self.vx
                self.vy, otra.vy = otra.vy, self.vy
                overlap = min_dist - distancia
                angle = math.atan2(dy, dx)
                self.circle.pos = (self.circle.pos[0] + math.cos(angle) * overlap, 
                                   self.circle.pos[1] + math.sin(angle) * overlap)

class BolaFragmento(Bola):
    def __init__(self, parent, x, y):
        super().__init__(parent, x, y, rainbow=True, mini=True)
        self.vida = 10.0
    def move(self, dt, speed):
        super().move(dt, speed); self.vida -= dt
        if self.vida <= 0: self.parent.eliminar_bola(self)

class BolaEvolutiva(Bola):
    def __init__(self, parent, x, y):
        super().__init__(parent, x, y, rainbow=True)
        self.vida = 10.0
        self.en_colision = False
        self.limite_tamano = 400 
    def move(self, dt, speed):
        x, y = self.circle.pos
        toca_pared = False
        x += self.vx * dt * speed
        y += self.vy * dt * speed
        if x <= 0: x = 0; self.vx = abs(self.vx); toca_pared = True
        elif x + self.size >= self.parent.width: x = self.parent.width - self.size; self.vx = -abs(self.vx); toca_pared = True
        if y <= BARRA_ALTURA: y = BARRA_ALTURA; self.vy = abs(self.vy); toca_pared = True
        elif y + self.size >= self.parent.height: y = self.parent.height - self.size; self.vy = -abs(self.vy); toca_pared = True
        if toca_pared:
            if not self.en_colision:
                if self.size < self.limite_tamano: self.set_scale(self.factor_actual * 1.30)
                self.en_colision = True
        else: self.en_colision = False
        self.circle.pos = (x, y); self.actualizar_borde()
        self.vida -= dt
        if self.vida <= 0: self.explotar()
    def explotar(self):
        cx, cy = self.circle.pos[0] + self.size/2, self.circle.pos[1] + self.size/2
        self.parent.eliminar_bola(self)
        for i in range(8):
            ang = (2 * math.pi / 8) * i
            nx, ny = cx + math.cos(ang) * 10, max(cy + math.sin(ang) * 10, BARRA_ALTURA + 15)
            f = BolaFragmento(self.parent, nx, ny)
            f.vx, f.vy = math.cos(ang) * 480, math.sin(ang) * 480
            self.parent.bolas.append(f)
            self.parent.total_bolas += 1 
        self.parent.actualizar_label_contador()

class BolaKiller(Bola):
    def __init__(self, parent, x, y):
        super().__init__(parent, x, y)
        self.base_color = (0, 0, 0)
        self.color_instr.rgb = self.base_color
        self.base_size = 100
        self.size = self.base_size
        self.circle.size = (self.size, self.size)
        self.circle.pos = (x - self.size/2, y - self.size/2)
        self.actualizar_borde()
        self.vx *= 1.2
        self.vy *= 1.2
    def move(self, dt, speed):
        super().move(dt, speed)
        c1x, c1y = self.circle.pos[0] + self.size/2, self.circle.pos[1] + self.size/2
        for otra in self.parent.bolas[:]:
            if otra is self: continue
            c2x, c2y = otra.circle.pos[0] + otra.size/2, otra.circle.pos[1] + otra.size/2
            distancia = math.sqrt((c1x - c2x)**2 + (c1y - c2y)**2)
            if distancia < (self.size/0.8 + otra.size/0.8):
                self.parent.eliminar_bola(otra)

class BolaGravity(Bola):
    def __init__(self, parent, x, y):
        super().__init__(parent, x, y)
        self.base_color = (0.1, 0.1, 0.45)
        self.color_instr.rgb = self.base_color
        self.gravedad_fuerza = 50000
        self.radio_influencia = 450
        self.base_size = 100 
        self.size = self.base_size 
        self.circle.size = (self.size, self.size)
        self.circle.pos = (x - self.size/2, y - self.size/2)
        self.actualizar_borde()

    def move(self, dt, speed):
        super().move(dt, speed)
        gx, gy = self.circle.pos[0] + self.size/2, self.circle.pos[1] + self.size/2        
        for otra in self.parent.bolas:
            if otra is self: continue           
            ox, oy = otra.circle.pos[0] + otra.size/2, otra.circle.pos[1] + otra.size/2
            dx = gx - ox
            dy = oy - gy
            distancia = math.sqrt(dx**2 + dy**2)
            if 0.1 < distancia < self.radio_influencia:
                fuerza_n = self.gravedad_fuerza / (distancia + 100)
                otra.vx += (dx / distancia) * fuerza_n * dt
                otra.vy += (dy / distancia) * fuerza_n * dt

class BolaRepel(Bola):
    def __init__(self, parent, x, y):
        super().__init__(parent, x, y)
        self.base_color = (1, 0, 0, 0)
        self.color_instr.rgb = self.base_color
        self.repulsion_fuerza = 60000
        self.base_size = 100 
        self.size = self.base_size 
        self.circle.size = (self.size, self.size)
        self.circle.pos = (x - self.size/2, y - self.size/2)
        self.actualizar_borde()

    def move(self, dt, speed):
        super().move(dt, speed)
        rx, ry = self.circle.pos[0] + self.size/2, self.circle.pos[1] + self.size/2
        for otra in self.parent.bolas:
            if otra is self: continue
            ox, oy = otra.circle.pos[0] + otra.size/2, otra.circle.pos[1] + otra.size/2
            dx = ox - rx
            dy = oy - ry
            distancia = math.sqrt(dx*dx + dy*dy)
            if 0 < distancia < 500:
                fuerza_n = (self.repulsion_fuerza / (distancia * 0.1 + 30))
                otra.vx += (dx / distancia) * fuerza_n * dt
                otra.vy += (dy / distancia) * fuerza_n * dt

class Juego(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bolas, self.agujeros = [], []
        self.paredes = []
        self.paredes_killer = []
        self.paused, self.speed_scale = False, 1
        self.evento_timer, self.total_bolas, self.total_rainbow = 0, 0, 0
        self.total_crecientes, self.total_eventos, self.tiempo, self.bg_hue = 0, 0, 0, 0
        self.stats_dict = {"rebotes": 0, "max_simultaneas": 0, "absorbidas": 0, "fragmentos": 0}
        
        self.debug_mode = "OFF"
        self.wall_mode = "OFF"
        self.gravity_active = False 
        self.touch_pos = None
        self.magnetos = {} 

        with self.canvas.before:
            self.bg_color = Color(1, 1, 1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(size=self._resize, pos=self._resize)
        self._crear_ui_botones()
        
        self.lbl_evento = Label(text="", color=(0,0,0,1), font_size=26, bold=True, size_hint=(None, None), size=(400, 50), pos_hint={"center_x": 0.5, "top": 0.98})
        self.add_widget(self.lbl_evento)
        
        self._crear_ui_paneles()
        self.clock_event = Clock.schedule_interval(self.update, 1 / 60)

    def _resize(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos
        self.barra_rect.size = (self.width, BARRA_ALTURA)
        ancho_p, alto_p = self.width * 0.8, self.height * 0.7
        pos_x, pos_y = self.width * 0.1, self.height * 0.15
        for panel, bg in [(self.stats_panel, self.stats_bg), (self.debug_panel, self.debug_bg)]:
            panel.size, panel.pos = (ancho_p, alto_p), (pos_x, pos_y)
            bg.size, bg.pos = (ancho_p, alto_p), (pos_x, pos_y)

    def _crear_ui_botones(self):
        self.ui_inferior = FloatLayout(size_hint=(1, None), height=BARRA_ALTURA)
        with self.ui_inferior.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.barra_rect = Rectangle(pos=(0, 0), size=(self.width, BARRA_ALTURA))
            
        self.btn_evento = Button(text="Evento", size_hint=(.25, 1), pos_hint={"x": 0})
        self.btn_evento.bind(on_release=self.evento)
        self.btn_pausa = Button(text="Pausa", size_hint=(.25, 1), pos_hint={"x": .25})
        self.btn_pausa.bind(on_release=self.toggle_pausa)
        self.btn_reset = Button(text="Reset", size_hint=(.25, 1), pos_hint={"x": .5})
        self.btn_reset.bind(on_release=self.reset)
        self.lbl_contador = Label(text="Bolas: 0", color=(0,0,0,1), size_hint=(.25, 1), pos_hint={"x": .75})
        
        self.ui_inferior.add_widget(self.btn_evento); self.ui_inferior.add_widget(self.btn_pausa)
        self.ui_inferior.add_widget(self.btn_reset); self.ui_inferior.add_widget(self.lbl_contador)
        self.add_widget(self.ui_inferior)
        
        self.btn_stats = Button(text="?", size_hint=(None, None), size=(70, 70), pos_hint={"x": 0.01, "top": 0.99}, background_color=(0, 0.5, 0.8, 1))
        self.btn_stats.bind(on_release=self.mostrar_stats); self.add_widget(self.btn_stats)
        
        self.btn_debug_trigger = Button(text="!", size_hint=(None, None), size=(70, 70), pos_hint={"right": 0.99, "top": 0.99}, background_color=(1,0,0,1))
        self.btn_debug_trigger.bind(on_release=self.mostrar_debug); self.add_widget(self.btn_debug_trigger)

    def _crear_ui_paneles(self):
        self.stats_panel = FloatLayout(opacity=0, disabled=True, size_hint=(None, None))
        with self.stats_panel.canvas.before:
            Color(0.1, 0.1, 0.15, .95); self.stats_bg = RoundedRectangle(radius=[25])
        
        self.stats_title = Label(text="ESTADÍSTICAS", font_size=32, bold=True, size_hint=(1, 0.1), pos_hint={"center_x": 0.5, "top": 0.95})
        self.stats_panel.add_widget(self.stats_title)
        self.stats_grid = GridLayout(cols=2, spacing=15, padding=30, size_hint=(.9, .6), pos_hint={"center_x": .5, "center_y": .5})
        self.btn_cerrar_stats = Button(text="Cerrar", size_hint=(None, None), size=(180, 65), pos_hint={"center_x": .5, "y": .05}, bold=True)
        self.btn_cerrar_stats.bind(on_release=self.ocultar_paneles)
        self.stats_panel.add_widget(self.stats_grid); self.stats_panel.add_widget(self.btn_cerrar_stats)
        self.add_widget(self.stats_panel)
        
        self.debug_panel = FloatLayout(opacity=0, disabled=True, size_hint=(None, None))
        with self.debug_panel.canvas.before:
            Color(.1, .1, .1, .95); self.debug_bg = RoundedRectangle(radius=[25])
        
        grid = GridLayout(cols=2, spacing=15, size_hint=(.9, .8), pos_hint={"center_x": .5, "center_y": 0.55})

        opc = [("Rainbow", lambda x: self.crear_bola_especifica("RAINBOW")), 
               ("Creciente", lambda x: self.crear_bola_especifica("CRECIENTE")), 
               ("Colisionable", lambda x: self.crear_bola_especifica("COLISION")), 
               ("Gigante", lambda x: self.crear_bola_especifica("GIGANTE")),
               ("KILLER", lambda x: self.crear_bola_especifica("KILLER")), 
               ("GRAVITY", lambda x: self.crear_bola_especifica("GRAVITY")),
               ("REPEL", lambda x: self.crear_bola_especifica("REPEL")),
               ("BOLA COMÚN", lambda x: self.crear_bola_especifica("NORMAL")), 
               ("Ocultar UI", self.toggle_ui_visibility)]

        for t, f in opc:
            b = Button(text=t, font_size=18, bold=True); b.bind(on_release=f); grid.add_widget(b)

        # SE HA AÑADIDO 'Evento RAINBOW' AQUÍ:
        eventos_debug = [("Evento MINI", "MINI"), ("Evento GIANT", "GIANT"), ("Evento SPEED", "SPEED"), ("Evento SLOWED", "SLOWED"), ("Evento RAINBOW", "RAINBOW")]
        for t, ev in eventos_debug:
            b = Button(text=t, font_size=18, bold=True)
            b.bind(on_release=lambda x, e=ev: self.forzar_evento(e))
            grid.add_widget(b)

        self.btn_gravity = Button(text="GRAVEDAD: OFF", font_size=18, bold=True, background_color=(1, 0, 0, 1))
        self.btn_gravity.bind(on_release=self.toggle_gravity)
        grid.add_widget(self.btn_gravity)

        self.btn_wall = Button(text="PARED: OFF", font_size=18, bold=True, background_color=(1, 0, 0, 1))
        self.btn_wall.bind(on_release=self.toggle_wall_mode)
        grid.add_widget(self.btn_wall)

        self.btn_magnet = Button(text="MAGNETO: OFF", font_size=18, bold=True, background_color=(1, 0, 0, 1))
        self.btn_magnet.bind(on_release=self.toggle_magnet_mode)
        grid.add_widget(self.btn_magnet)

        self.btn_bh = Button(text="AGUJERO NEGRO", font_size=18, bold=True, background_color=(0.6, 0.1, 1, 1))
        self.btn_bh.bind(on_release=self.crear_agujero)
        grid.add_widget(self.btn_bh)

        self.btn_cerrar_debug = Button(text="Cerrar Debug", size_hint=(None, None), size=(180, 55), pos_hint={"center_x": .5, "y": .05}, font_size=18)
        self.btn_cerrar_debug.bind(on_release=self.ocultar_paneles)
        self.debug_panel.add_widget(grid); self.debug_panel.add_widget(self.btn_cerrar_debug)
        self.add_widget(self.debug_panel)

    def mostrar_stats(self, *_):
        self.stats_grid.clear_widgets()
        fps_actuales = int(Clock.get_fps())
        m, s = divmod(int(self.tiempo), 60)
        datos = [
            ("TIEMPO TOTAL:", f"{m:02d}:{s:02d}"), 
            ("FPS ACTUALES:", f"{fps_actuales}"), 
            ("BOLAS CREADAS:", str(self.total_bolas)),
            ("EN PANTALLA:", str(len(self.bolas))), 
            ("MÁXIMO RÉCORD:", str(self.stats_dict["max_simultaneas"])),
            ("REBOTES PARED:", str(self.stats_dict["rebotes"])), 
            ("ABSORBIDAS:", str(self.stats_dict["absorbidas"]))
        ]
        for titulo, valor in datos:
            self.stats_grid.add_widget(Label(text=titulo, bold=True))
            self.stats_grid.add_widget(Label(text=valor))
        self.stats_panel.opacity, self.stats_panel.disabled = 1, False

    def toggle_wall_mode(self, *_):
        if self.wall_mode == "OFF":
            self.wall_mode = "WALL"
            self.btn_wall.text = "PARED: ON"
            self.btn_wall.background_color = (0, 1, 0, 1)
        elif self.wall_mode == "WALL":
            self.wall_mode = "KILL"
            self.btn_wall.text = "KILL ON"
            self.btn_wall.background_color = (0, 1, 0, 1)
        else:
            self.wall_mode = "OFF"
            self.btn_wall.text = "PARED: OFF"
            self.btn_wall.background_color = (1, 0, 0, 1)

    def toggle_magnet_mode(self, *_):
        modos = ["OFF", "ATRAER", "REPELER"]
        idx = (modos.index(self.debug_mode) + 1) % len(modos)
        self.debug_mode = modos[idx]
        self.btn_magnet.text = f"MAGNETO: {self.debug_mode}"
        self.btn_magnet.background_color = (1, 0, 0, 1) if self.debug_mode == "OFF" else (0, 1, 0, 1)

    def toggle_gravity(self, *_):
        self.gravity_active = not self.gravity_active
        if self.gravity_active:
            self.btn_gravity.text = "GRAVEDAD: CAER"
            self.btn_gravity.background_color = (0, 1, 0, 1)
        else:
            self.btn_gravity.text = "GRAVEDAD: OFF"
            self.btn_gravity.background_color = (1, 0, 0, 1)

    def on_touch_down(self, touch):
        if self.stats_panel.opacity > 0:
            if self.btn_cerrar_stats.collide_point(*touch.pos): return self.btn_cerrar_stats.on_touch_down(touch)
            return True
        if self.debug_panel.opacity > 0:
            if self.debug_panel.collide_point(*touch.pos): return super(Juego, self).on_touch_down(touch)
            return True
        if self.ui_inferior.collide_point(*touch.pos) or self.btn_stats.collide_point(*touch.pos) or self.btn_debug_trigger.collide_point(*touch.pos):
            return super(Juego, self).on_touch_down(touch)
        
        if not self.paused and touch.y > BARRA_ALTURA:
            if self.wall_mode != "OFF":
                with self.canvas.before:
                    if self.wall_mode == "KILL":
                        Color(1, 0, 0, 1)
                        target_list = self.paredes_killer
                    else:
                        Color(0, 0, 0, 1)
                        target_list = self.paredes
                    
                    touch.ud['line'] = Line(points=(touch.x, touch.y), width=4.5, group='paredes')
                    touch.ud['target_list'] = target_list
                    target_list.append(touch.ud['line'])
                return True
            
            if self.debug_mode != "OFF":
                self.touch_pos = touch.pos
                with self.canvas:
                    Color(0, 0.1, 1, 0.5)
                    self.magnetos[touch.id] = Line(circle=(touch.x, touch.y, 200), width=2)
            else:
                self.crear_bola(touch.x, touch.y)
            return True
        return False

    def on_touch_move(self, touch):
        if self.stats_panel.opacity > 0 or self.debug_panel.opacity > 0: 
            return False
        if not self.paused and touch.y > BARRA_ALTURA:
            if self.wall_mode != "OFF" and 'line' in touch.ud:
                touch.ud['line'].points += [touch.x, touch.y]
                return True

            if getattr(self, 'debug_mode', "OFF") == "OFF":
                self.crear_bola(touch.x, touch.y)
            else:
                if hasattr(self, 'magnetos') and touch.id in self.magnetos:
                    self.magnetos[touch.id].circle = (touch.x, touch.y, 200)
                    self.touch_pos = touch.pos
            return True
        return False

    def on_touch_up(self, touch):
        if 'line' in touch.ud:
            del touch.ud['line']
            if 'target_list' in touch.ud: del touch.ud['target_list']
        if hasattr(self, 'magnetos') and touch.id in self.magnetos:
            self.canvas.remove(self.magnetos[touch.id])
            del self.magnetos[touch.id]
        if not getattr(self, 'magnetos', {}):
            self.touch_pos = None
        return super(Juego, self).on_touch_up(touch)

    def resolver_colisiones_paredes(self, dt):
        for b in self.bolas[:]:
            cx, cy = b.circle.pos[0] + b.size/2, b.circle.pos[1] + b.size/2
            r = b.size / 2
            
            ball_killed = False
            for wall_line in self.paredes_killer:
                pts = wall_line.points
                for i in range(0, len(pts) - 2, 2):
                    x1, y1, x2, y2 = pts[i], pts[i+1], pts[i+2], pts[i+3]
                    seg_dx, seg_dy = x2 - x1, y2 - y1
                    bol_dx, bol_dy = cx - x1, cy - y1
                    seg_len_sq = seg_dx**2 + seg_dy**2
                    if seg_len_sq == 0: continue
                    t = max(0, min(1, (bol_dx * seg_dx + bol_dy * seg_dy) / seg_len_sq))
                    closest_x, closest_y = x1 + t * seg_dx, y1 + t * seg_dy
                    dist_sq = (cx - closest_x)**2 + (cy - closest_y)**2
                    if dist_sq < r**2:
                        self.eliminar_bola(b)
                        ball_killed = True
                        break
                if ball_killed: break
            
            if ball_killed: continue
            
            for wall_line in self.paredes:
                pts = wall_line.points
                for i in range(0, len(pts) - 2, 2):
                    x1, y1, x2, y2 = pts[i], pts[i+1], pts[i+2], pts[i+3]
                    seg_dx, seg_dy = x2 - x1, y2 - y1
                    bol_dx, bol_dy = cx - x1, cy - y1
                    seg_len_sq = seg_dx**2 + seg_dy**2
                    if seg_len_sq == 0: continue
                    t = max(0, min(1, (bol_dx * seg_dx + bol_dy * seg_dy) / seg_len_sq))
                    closest_x, closest_y = x1 + t * seg_dx, y1 + t * seg_dy
                    dist_dx, dist_dy = cx - closest_x, cy - closest_y
                    dist_sq = dist_dx**2 + dist_dy**2
                    if dist_sq < r**2:
                        dist = math.sqrt(dist_sq)
                        if dist == 0: continue
                        nx, ny = dist_dx / dist, dist_dy / dist
                        overlap = r - dist
                        b.circle.pos = (b.circle.pos[0] + nx * overlap, b.circle.pos[1] + ny * overlap)
                        dot_prod = b.vx * nx + b.vy * ny
                        b.vx, b.vy = (b.vx - 2 * dot_prod * nx) * 0.9, (b.vy - 2 * dot_prod * ny) * 0.99
                        b.actualizar_borde()
                        self.stats_dict["rebotes"] += 1

    def update(self, dt):
        v_fondo = 0.10 if self.speed_scale > 1 else 0.02
        self.bg_hue = (self.bg_hue + dt * v_fondo) % 1
        self.bg_color.hsv = (self.bg_hue, 0.1, 1)
        if self.paused: return
        self.tiempo += dt
        sub_steps = 3
        sub_dt = dt / sub_steps
        for _ in range(sub_steps):
            for b in self.bolas:
                if self.gravity_active:
                    b.vy -= 1200 * sub_dt
                if self.touch_pos and self.debug_mode != "OFF":
                    tx, ty = self.touch_pos
                    fuerza = 2500 if self.debug_mode == "ATRAER" else -35000
                    bx, by = b.circle.pos[0] + b.size / 2, b.circle.pos[1] + b.size / 2
                    dx, dy = tx - bx, ty - by
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist > 10:
                        f_calc = fuerza / (dist * 0.03 + 1)
                        b.vx += (dx / dist) * f_calc * sub_dt
                        b.vy += (dy / dist) * f_calc * sub_dt

            for b in self.bolas[:]: b.move(sub_dt, self.speed_scale)
            self.resolver_colisiones_paredes(sub_dt)

        for a in self.agujeros[:]: a.update(dt, self.bolas)
        if self.stats_panel.opacity > 0: self.mostrar_stats()
        if self.evento_timer > 0:
            self.evento_timer -= dt
            if self.evento_timer <= 0: self.limpiar_efectos_evento()
        for b in self.bolas: b.update_color(dt)

    def crear_bola(self, x, y):
        prob = random()
        if prob < 0.10: 
            bola = BolaEvolutiva(self, x, y); self.total_crecientes += 1
        else:
            rb = random() < 0.25 or "RAINBOW" in self.lbl_evento.text
            bola = Bola(self, x, y, rb, "GIANT" in self.lbl_evento.text, "MINI" in self.lbl_evento.text)
            if rb: self.total_rainbow += 1
        self.bolas.append(bola); self.total_bolas += 1; self.actualizar_label_contador()

    def crear_agujero(self, *_):
        self.agujeros.append(AgujeroNegro(self, self.width/2, (self.height + BARRA_ALTURA)/2)); self.ocultar_paneles()

    def eliminar_agujero(self, a): 
        if a in self.agujeros: a.limpiar(); self.agujeros.remove(a)

    def toggle_ui_visibility(self, *_): 
        self.ui_inferior.opacity = self.btn_stats.opacity = 0 if self.ui_inferior.opacity == 1 else 1
    
    def crear_bola_especifica(self, t):
        x, y = self.width/2, self.height/2
        b = None
        if t=="RAINBOW": b=Bola(self, x, y, rainbow=True)
        elif t=="CRECIENTE": b=BolaEvolutiva(self, x, y)
        elif t=="COLISION": b=BolaColisionable(self, x, y)
        elif t=="GIGANTE": b=Bola(self, x, y, giant=True)
        elif t=="KILLER": b=BolaKiller(self, x, y)
        elif t=="GRAVITY": b=BolaGravity(self, x, y)
        elif t=="REPEL": b=BolaRepel(self, x, y)
        if b: self.bolas.append(b); self.total_bolas+=1; self.actualizar_label_contador()

    def limpiar_efectos_evento(self):
        self.speed_scale, self.lbl_evento.text, self.evento_timer = 1, "", 0
        for b in self.bolas:
            if not isinstance(b, (BolaEvolutiva, BolaFragmento)): b.rainbow = False
            b.set_scale(1.0)

    def forzar_evento(self, t):
        self.limpiar_efectos_evento()
        self.evento_timer, self.lbl_evento.text = EVENTO_DURACION, f"Evento: {t}"
        if t == "SPEED": self.speed_scale = 4
        elif t == "SLOWED": self.speed_scale = 0.35
        elif t == "RAINBOW":
            for b in self.bolas: b.rainbow = True
        elif t == "GIANT":
            for b in self.bolas: b.set_scale(2.0)
        elif t == "MINI":
            for b in self.bolas: b.set_scale(MINI_SCALE)

    def evento(self, *_): 
        self.forzar_evento(choice(["SPEED", "SLOWED", "RAINBOW", "GIANT", "MINI"]))

    def toggle_pausa(self, *_): 
        self.paused = not self.paused
        self.btn_pausa.text = "Reanudar" if self.paused else "Pausa"

    def reset(self, *_):
        for b in self.bolas: b.limpiar()
        for a in self.agujeros: a.limpiar()
        self.canvas.before.remove_group('paredes')
        self.paredes.clear()
        self.paredes_killer.clear()
        self.bolas.clear(); self.agujeros.clear()
        self.actualizar_label_contador(); self.limpiar_efectos_evento()

    def eliminar_bola(self, b):
        if b in self.bolas: b.limpiar(); self.bolas.remove(b); self.actualizar_label_contador()

    def actualizar_label_contador(self):
        actual = len(self.bolas)
        self.lbl_contador.text = f"Bolas: {actual}"
        if actual > self.stats_dict["max_simultaneas"]: self.stats_dict["max_simultaneas"] = actual

    def mostrar_debug(self, *_): 
        self.paused, self.debug_panel.opacity, self.debug_panel.disabled = True, 1, False

    def ocultar_paneles(self, *_): 
        self.stats_panel.opacity = self.debug_panel.opacity = 0
        self.stats_panel.disabled = self.debug_panel.disabled = True
        self.paused = False
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)
        layout = FloatLayout()
        with layout.canvas.before:
            Color(0.7, 0.9, 0.7, 1)
            self.rect = Rectangle(size=(2000, 2000))
        lbl = Label(text="[b][i]BALL MANIA[/i][/b]", markup=True, font_size=80, 
                    color=(0, 0, 0, 1), pos_hint={"center_x": 0.5, "center_y": 0.7})
        btn_jugar = Button(text="[b][i]JUGAR[/i][/b]", markup=True, 
                     size_hint=(0.6, 0.08), pos_hint={"center_x": 0.5, "center_y": 0.5}, 
                     background_color=(0.5, 0.5, 0.5, 1))
        btn_jugar.bind(on_release=self.iniciar)
        btn_salir = Button(text="[b][i]SALIR[/i][/b]", markup=True, 
                     size_hint=(0.6, 0.08), pos_hint={"center_x": 0.5, "center_y": 0.38}, 
                     background_color=(0.5, 0.5, 0.5, 1))
        btn_salir.bind(on_release=self.salir)
        layout.add_widget(lbl)
        layout.add_widget(btn_jugar)
        layout.add_widget(btn_salir)
        lbl_version = Label(
            text="BALL MANIA VERSIÓN 0.4",
            font_size=37,
            color=(0, 0, 0, 0.9),
            size_hint=(1, None),
            height=30,
            pos_hint={"center_x": 0.5, "y": 0.01}
        )
        layout.add_widget(lbl_version)
        self.add_widget(layout)

    def iniciar(self, *_): 
        self.manager.current = 'loading'

    def salir(self, *_):
        App.get_running_app().stop()

class LoadingScreen(Screen):
    def on_enter(self):
        layout = FloatLayout()
        with layout.canvas.before:
            Color(0,0,0,1)
            Rectangle(size=(2000,2000))
        lbl = Label(text="[i]CARGANDO...[/i]", markup=True, font_size=50)
        layout.add_widget(lbl); self.add_widget(layout)
        Clock.schedule_once(self.fin_carga, 7)

    def fin_carga(self, *_): self.manager.current = 'game'

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.add_widget(Juego())

class JuegoApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(LoadingScreen(name='loading'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == "__main__":
    JuegoApp().run()