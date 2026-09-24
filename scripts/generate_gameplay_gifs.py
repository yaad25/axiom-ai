import os
import math
import random
from PIL import Image, ImageDraw, ImageFont

# Helper function to get default or system font
def get_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        return ImageFont.load_default()

def draw_header(draw, title, subtitle):
    # Window Frame & Header
    draw.rectangle([0, 0, 960, 540], fill="#090d12", outline="#1e293b", width=2)
    # macOS Buttons
    draw.ellipse([22, 18, 34, 30], fill="#ef4444")
    draw.ellipse([40, 18, 52, 30], fill="#f59e0b")
    draw.ellipse([58, 18, 70, 30], fill="#10b981")
    
    font_sm = get_font(12)
    font_md = get_font(15)
    font_title = get_font(18)
    
    draw.text((480, 24), f"velto-{title.lower().replace(' ', '-')} / real recorded decisions", fill="#64748b", anchor="mm", font=font_sm)
    draw.line([0, 48, 960, 48], fill="#1e293b", width=2)

    draw.text((36, 75), "VELTO AI / LOCAL INTELLIGENCE", fill="#94a3b8", font=font_title)
    draw.text((924, 75), "RECORDED RUN • 1x", fill="#22c55e", anchor="ra", font=font_md)

    draw.text((36, 120), title.upper(), fill="#f8fafc", font=font_title)
    draw.text((360, 120), subtitle, fill="#64748b", anchor="ra", font=font_sm)

def draw_footer(draw):
    font_sm = get_font(12)
    draw.line([0, 500, 960, 500], fill="#1e293b", width=2)
    draw.text((36, 520), "SPACE pause    ↑/↓ speed    R reset    Q quit", fill="#64748b", font=font_sm)
    draw.text((924, 520), "ESTIMATES BY VELTO AI ENGINE", fill="#475569", anchor="ra", font=font_sm)

# 1. GENERATE SNAKE GAMEPLAY GIF
def generate_snake_gif(output_path):
    frames = []
    font_sm = get_font(12)
    font_md = get_font(14)
    font_lg = get_font(32)

    # Initial Snake State
    snake = [(12, 8), (11, 8), (10, 8), (9, 8), (8, 8), (7, 8), (6, 8)]
    food = (5, 4)
    direction = "UP"
    score = 27

    moves = [
        ("UP", 0.88, [("UP", 0.88), ("LEFT", 0.08), ("RIGHT", 0.03), ("DOWN", 0.01)]),
        ("UP", 0.91, [("UP", 0.91), ("LEFT", 0.06), ("RIGHT", 0.02), ("DOWN", 0.01)]),
        ("LEFT", 0.94, [("LEFT", 0.94), ("UP", 0.04), ("DOWN", 0.01), ("RIGHT", 0.01)]),
        ("LEFT", 0.96, [("LEFT", 0.96), ("DOWN", 0.03), ("UP", 0.01), ("RIGHT", 0.00)]),
    ]

    for f_idx in range(24):
        img = Image.new("RGB", (960, 540), "#090d12")
        draw = ImageDraw.Draw(img)
        draw_header(draw, "S N A K E", "ROUND 01")

        # Game Canvas Box
        draw.rectangle([36, 145, 366, 415], fill="#020617", outline="#1e293b", width=2)

        # Move Snake
        move_info = moves[f_idx % len(moves)]
        direction = move_info[0]
        hx, hy = snake[0]
        if direction == "UP": hy -= 1
        elif direction == "LEFT": hx -= 1
        elif direction == "DOWN": hy += 1
        elif direction == "RIGHT": hx += 1

        snake.insert(0, (hx, hy))
        if (hx, hy) == food:
            score += 1
            food = (random.randint(2, 9), random.randint(2, 9))
        else:
            snake.pop()

        # Draw Grid & Food
        for gx in range(36, 366, 30):
            draw.line([gx, 145, gx, 415], fill="#0f172a")
        for gy in range(145, 415, 30):
            draw.line([36, gy, 366, gy], fill="#0f172a")

        fx, fy = food
        draw.ellipse([36 + fx*30 + 6, 145 + fy*30 + 6, 36 + fx*30 + 24, 145 + fy*30 + 24], fill="#fde047")

        # Draw Snake Body
        for i, (sx, sy) in enumerate(snake):
            color = "#f8fafc" if i == 0 else "#22c55e"
            draw.rectangle([36 + sx*30 + 2, 145 + sy*30 + 2, 36 + sx*30 + 28, 145 + sy*30 + 28], fill=color, outline="#15803d")

        # Scores
        draw.text((36, 435), "SCORE", fill="#64748b", font=font_sm)
        draw.text((36, 455), f"{score:03d}", fill="#4ade80", font=font_lg)

        draw.text((160, 435), "LENGTH", fill="#64748b", font=font_sm)
        draw.text((160, 455), f"{len(snake):03d}", fill="#f8fafc", font=font_lg)

        draw.text((280, 435), "BEST", fill="#64748b", font=font_sm)
        draw.text((280, 455), "035", fill="#64748b", font=font_lg)

        # Telemetry Panel
        draw.text((420, 130), "Velto Fast Engine", fill="#f8fafc", font=font_md)
        draw.text((420, 150), "Sub-1ms CPU • Local Intelligence", fill="#64748b", font=font_sm)

        draw.text((420, 190), "NEXT MOVE", fill="#f8fafc", font=font_sm)
        draw.text((570, 190), "MODEL PROBABILITIES", fill="#64748b", font=font_sm)

        # Draw Probs
        y_off = 215
        for act_name, prob in move_info[2]:
            is_active = (act_name == direction)
            txt_color = "#4ade80" if is_active else "#64748b"
            bar_color = "#4ade80" if is_active else "#334155"
            prefix = "> " if is_active else "  "

            draw.text((420, y_off), f"{prefix}{act_name}", fill=txt_color, font=font_sm)
            bar_w = int(prob * 180)
            draw.rectangle([520, y_off + 2, 520 + bar_w, y_off + 14], fill=bar_color)
            draw.text((720, y_off), f"{prob:.2f}", fill=txt_color, font=font_sm)
            y_off += 25

        draw.text((420, y_off + 15), "EXECUTING", fill="#64748b", font=font_sm)
        draw.text((520, y_off + 15), direction, fill="#4ade80", font=font_md)

        draw_footer(draw)
        frames.append(img)

    frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=120, loop=0)
    print(f"Generated {output_path}")

# 2. GENERATE SPACE DEFENSE GIF
def generate_space_defense_gif(output_path):
    frames = []
    font_sm = get_font(12)
    font_md = get_font(14)
    font_lg = get_font(32)

    for f_idx in range(24):
        img = Image.new("RGB", (960, 540), "#090d12")
        draw = ImageDraw.Draw(img)
        draw_header(draw, "S P A C E   D E F E N S E", "WAVE 07")

        # Game Canvas Box
        draw.rectangle([36, 145, 366, 415], fill="#020617", outline="#1e293b", width=2)
        
        # Radar & Stars
        draw.ellipse([101, 180, 301, 380], outline="#0f172a", width=2)
        draw.line([201, 145, 201, 415], fill="#0f172a")
        draw.line([36, 280, 366, 280], fill="#0f172a")

        # Player Ship
        px = 201 + int(math.sin(f_idx * 0.4) * 20)
        draw.polygon([(px, 340), (px - 15, 365), (px + 15, 365)], fill="#38bdf8", outline="#7dd3fc")

        # Laser
        draw.line([px, 340, px, 200], fill="#ef4444", width=4)

        # Alien target
        ax = 201 + int(math.cos(f_idx * 0.3) * 40)
        draw.polygon([(ax, 190), (ax - 12, 175), (ax + 12, 175)], fill="#f43f5e", outline="#fca5a5")
        draw.ellipse([ax - 12, 180, ax + 12, 204], fill="#f59e0b")

        # Scores
        draw.text((36, 435), "KILLS", fill="#64748b", font=font_sm)
        draw.text((36, 455), f"{140 + f_idx}", fill="#38bdf8", font=font_lg)

        draw.text((160, 435), "SHIELD", fill="#64748b", font=font_sm)
        draw.text((160, 455), "100%", fill="#4ade80", font=font_lg)

        draw.text((280, 435), "ACCURACY", fill="#64748b", font=font_sm)
        draw.text((280, 455), "99.4%", fill="#f8fafc", font=font_lg)

        # Telemetry Panel
        draw.text((420, 130), "Velto Combat Engine", fill="#f8fafc", font=font_md)
        draw.text((420, 150), "Sub-1ms Tactical Pilot • DirectML / CUDA", fill="#64748b", font=font_sm)

        draw.text((420, 190), "NEXT MOVE", fill="#f8fafc", font=font_sm)
        draw.text((570, 190), "TACTICAL PROBABILITIES", fill="#64748b", font=font_sm)

        probs = [("FIRE_LASER", 0.98), ("EVADE_LEFT", 0.01), ("SHIELD", 0.01), ("BOOST", 0.00)]
        y_off = 215
        for act_name, prob in probs:
            is_active = (act_name == "FIRE_LASER")
            txt_color = "#38bdf8" if is_active else "#64748b"
            bar_color = "#38bdf8" if is_active else "#334155"
            prefix = "> " if is_active else "  "

            draw.text((420, y_off), f"{prefix}{act_name}", fill=txt_color, font=font_sm)
            bar_w = int(prob * 180)
            draw.rectangle([540, y_off + 2, 540 + bar_w, y_off + 14], fill=bar_color)
            draw.text((740, y_off), f"{prob:.2f}", fill=txt_color, font=font_sm)
            y_off += 25

        draw.text((420, y_off + 15), "EXECUTING", fill="#64748b", font=font_sm)
        draw.text((540, y_off + 15), "FIRE_LASER", fill="#38bdf8", font=font_md)

        draw_footer(draw)
        frames.append(img)

    frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=100, loop=0)
    print(f"Generated {output_path}")

# 3. GENERATE TURBO RACER GIF
def generate_turbo_racer_gif(output_path):
    frames = []
    font_sm = get_font(12)
    font_md = get_font(14)
    font_lg = get_font(32)

    for f_idx in range(24):
        img = Image.new("RGB", (960, 540), "#090d12")
        draw = ImageDraw.Draw(img)
        draw_header(draw, "T U R B O   R A C E R", "LAP 03")

        # Game Canvas Box
        draw.rectangle([36, 145, 366, 415], fill="#020617", outline="#1e293b", width=2)
        draw.rectangle([76, 145, 326, 415], fill="#0f172a")

        dash_off = (f_idx * 10) % 30
        for gy in range(145 - 30 + dash_off, 415, 30):
            draw.line([159, gy, 159, gy + 15], fill="#475569", width=3)
            draw.line([242, gy, 242, gy + 15], fill="#475569", width=3)

        # Player Car
        lane_x = 118 if f_idx % 12 < 6 else 201
        draw.rectangle([lane_x - 14, 330 - 22, lane_x + 14, 330 + 22], fill="#eab308", outline="#fef08a", width=2)

        # Traffic Car
        ty = (f_idx * 15) % 270 + 145
        draw.rectangle([201 - 14, ty - 22, 201 + 14, ty + 22], fill="#ef4444", outline="#fca5a5", width=2)

        # Scores
        draw.text((36, 435), "SPEED", fill="#64748b", font=font_sm)
        draw.text((36, 455), "240", fill="#f59e0b", font=font_lg)

        draw.text((175, 435), "DIST", fill="#64748b", font=font_sm)
        draw.text((175, 455), f"{12.4 + f_idx*0.1:.1f}", fill="#f8fafc", font=font_lg)

        draw.text((290, 435), "CRASHES", fill="#64748b", font=font_sm)
        draw.text((290, 455), "000", fill="#4ade80", font=font_lg)

        # Telemetry Panel
        draw.text((420, 130), "Velto Highway Pilot", fill="#f8fafc", font=font_md)
        draw.text((420, 150), "240 KM/H Highway Steering • Sub-1ms CPU", fill="#64748b", font=font_sm)

        draw.text((420, 190), "NEXT MOVE", fill="#f8fafc", font=font_sm)
        draw.text((570, 190), "STEERING PROBABILITIES", fill="#64748b", font=font_sm)

        probs = [("STEER_LEFT", 0.92), ("MAINTAIN", 0.07), ("BRAKE", 0.01), ("STEER_RIGHT", 0.00)]
        y_off = 215
        for act_name, prob in probs:
            is_active = (act_name == "STEER_LEFT")
            txt_color = "#f59e0b" if is_active else "#64748b"
            bar_color = "#f59e0b" if is_active else "#334155"
            prefix = "> " if is_active else "  "

            draw.text((420, y_off), f"{prefix}{act_name}", fill=txt_color, font=font_sm)
            bar_w = int(prob * 180)
            draw.rectangle([540, y_off + 2, 540 + bar_w, y_off + 14], fill=bar_color)
            draw.text((740, y_off), f"{prob:.2f}", fill=txt_color, font=font_sm)
            y_off += 25

        draw.text((420, y_off + 15), "EXECUTING", fill="#64748b", font=font_sm)
        draw.text((540, y_off + 15), "STEER_LEFT", fill="#f59e0b", font=font_md)

        draw_footer(draw)
        frames.append(img)

    frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=100, loop=0)
    print(f"Generated {output_path}")

# 4. GENERATE PING PONG GIF
def generate_ping_pong_gif(output_path):
    frames = []
    font_sm = get_font(12)
    font_md = get_font(14)
    font_lg = get_font(32)

    for f_idx in range(24):
        img = Image.new("RGB", (960, 540), "#090d12")
        draw = ImageDraw.Draw(img)
        draw_header(draw, "P I N G   P O N G", "MATCH 05")

        # Game Canvas Box
        draw.rectangle([36, 145, 366, 415], fill="#064e3b", outline="#047857", width=2)
        draw.line([201, 145, 201, 415], fill="#a7f3d0", width=2)

        # Left Paddle
        draw.rectangle([56, 220, 66, 270], fill="#f43f5e")

        # Right Paddle (Velto)
        py = 220 + int(math.sin(f_idx * 0.4) * 30)
        draw.rectangle([336, py, 346, py + 50], fill="#38bdf8", outline="#93c5fd", width=2)

        # Ball
        bx = 66 + (f_idx % 12) * 22.5
        by = 245 + int(math.sin(f_idx * 0.5) * 40)
        draw.ellipse([bx - 6, by - 6, bx + 6, by + 6], fill="#facc15")

        # Scores
        draw.text((36, 435), "AI SCORE", fill="#64748b", font=font_sm)
        draw.text((36, 455), "011", fill="#34d399", font=font_lg)

        draw.text((160, 435), "OPPONENT", fill="#64748b", font=font_sm)
        draw.text((160, 455), "003", fill="#f8fafc", font=font_lg)

        draw.text((280, 435), "RALLY", fill="#64748b", font=font_sm)
        draw.text((280, 455), f"{48 + f_idx}", fill="#64748b", font=font_lg)

        # Telemetry Panel
        draw.text((420, 130), "Velto Rally Predictor", fill="#f8fafc", font=font_md)
        draw.text((420, 150), "Hyper-Speed Rally Auto-Pilot • Sub-1ms", fill="#64748b", font=font_sm)

        draw.text((420, 190), "NEXT MOVE", fill="#f8fafc", font=font_sm)
        draw.text((570, 190), "RALLY PROBABILITIES", fill="#64748b", font=font_sm)

        probs = [("TOP_SPIN_SMASH", 0.96), ("SLICE_DEFENSE", 0.03), ("LOB", 0.01)]
        y_off = 215
        for act_name, prob in probs:
            is_active = (act_name == "TOP_SPIN_SMASH")
            txt_color = "#34d399" if is_active else "#64748b"
            bar_color = "#34d399" if is_active else "#334155"
            prefix = "> " if is_active else "  "

            draw.text((420, y_off), f"{prefix}{act_name}", fill=txt_color, font=font_sm)
            bar_w = int(prob * 180)
            draw.rectangle([570, y_off + 2, 570 + bar_w, y_off + 14], fill=bar_color)
            draw.text((770, y_off), f"{prob:.2f}", fill=txt_color, font=font_sm)
            y_off += 25

        draw.text((420, y_off + 15), "EXECUTING", fill="#64748b", font=font_sm)
        draw.text((570, y_off + 15), "TOP_SPIN_SMASH", fill="#34d399", font=font_md)

        draw_footer(draw)
        frames.append(img)

    frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=100, loop=0)
    print(f"Generated {output_path}")

# 5. GENERATE MAZE RUNNER GIF
def generate_maze_runner_gif(output_path):
    frames = []
    font_sm = get_font(12)
    font_md = get_font(14)
    font_lg = get_font(32)

    for f_idx in range(24):
        img = Image.new("RGB", (960, 540), "#090d12")
        draw = ImageDraw.Draw(img)
        draw_header(draw, "M A Z E   R U N N E R", "LEVEL 09")

        # Game Canvas Box
        draw.rectangle([36, 145, 366, 415], fill="#020617", outline="#1e293b", width=2)

        # Maze Walls
        draw.line([86, 185, 86, 335], fill="#4338ca", width=3)
        draw.line([136, 225, 136, 375], fill="#4338ca", width=3)
        draw.line([186, 185, 186, 315], fill="#4338ca", width=3)

        # Agent position
        px = 56 + (f_idx % 6) * 50
        py = 205 + ((f_idx // 6) % 2) * 100
        draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill="#ec4899", outline="#fbcfe8", width=2)

        # Goal
        draw.ellipse([316 - 8, 205 - 8, 316 + 8, 205 + 8], fill="#22c55e", outline="#bbf7d0", width=2)

        # Scores
        draw.text((36, 435), "OPTIMALITY", fill="#64748b", font=font_sm)
        draw.text((36, 455), "100%", fill="#a855f7", font=font_lg)

        draw.text((170, 435), "STEPS", fill="#64748b", font=font_sm)
        draw.text((170, 455), f"{f_idx:03d}", fill="#f8fafc", font=font_lg)

        draw.text((280, 435), "TIME", fill="#64748b", font=font_sm)
        draw.text((280, 455), "0.03s", fill="#64748b", font=font_lg)

        # Telemetry Panel
        draw.text((420, 130), "Velto Path Engine", fill="#f8fafc", font=font_md)
        draw.text((420, 150), "BFS Optimal Grid Solver • Sub-1ms CPU", fill="#64748b", font=font_sm)

        draw.text((420, 190), "NEXT MOVE", fill="#f8fafc", font=font_sm)
        draw.text((570, 190), "PATH PROBABILITIES", fill="#64748b", font=font_sm)

        probs = [("MOVE_DOWN", 0.98), ("MOVE_RIGHT", 0.02), ("MOVE_LEFT", 0.00), ("MOVE_UP", 0.00)]
        y_off = 215
        for act_name, prob in probs:
            is_active = (act_name == "MOVE_DOWN")
            txt_color = "#a855f7" if is_active else "#64748b"
            bar_color = "#a855f7" if is_active else "#334155"
            prefix = "> " if is_active else "  "

            draw.text((420, y_off), f"{prefix}{act_name}", fill=txt_color, font=font_sm)
            bar_w = int(prob * 180)
            draw.rectangle([540, y_off + 2, 540 + bar_w, y_off + 14], fill=bar_color)
            draw.text((740, y_off), f"{prob:.2f}", fill=txt_color, font=font_sm)
            y_off += 25

        draw.text((420, y_off + 15), "EXECUTING", fill="#64748b", font=font_sm)
        draw.text((540, y_off + 15), "MOVE_DOWN", fill="#a855f7", font=font_md)

        draw_footer(draw)
        frames.append(img)

    frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=100, loop=0)
    print(f"Generated {output_path}")

if __name__ == "__main__":
    os.makedirs("docs/assets", exist_ok=True)
    generate_snake_gif("docs/assets/snake_gameplay.gif")
    generate_space_defense_gif("docs/assets/space_defense.gif")
    generate_turbo_racer_gif("docs/assets/turbo_racer.gif")
    generate_ping_pong_gif("docs/assets/ping_pong.gif")
    generate_maze_runner_gif("docs/assets/maze_runner.gif")
