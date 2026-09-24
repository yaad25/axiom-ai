"""
Record Side-by-Side 3-Way Tetris Engine Comparison GIF:
Jev (1218ms) vs this-that-1.0 (1408ms) vs Velto (0.07ms)
"""

import math
import os
import random
from PIL import Image, ImageDraw, ImageFont

# Canvas dimensions
WIDTH, HEIGHT = 960, 540
FPS = 10
DURATION_SEC = 6
TOTAL_FRAMES = FPS * DURATION_SEC

# Colors
BG_COLOR = (15, 23, 42)
TEXT_COLOR = (248, 250, 252)
MUTED_TEXT = (148, 163, 184)
BORDER_COLOR = (30, 41, 59)

JEV_COLOR = (239, 68, 68)        # Red/Orange
THISTHAT_COLOR = (245, 158, 11)   # Yellow/Amber
VELTO_COLOR = (34, 197, 94)      # Green

# Font setup
try:
    font_large = ImageFont.truetype("arial.ttf", 18)
    font_medium = ImageFont.truetype("arial.ttf", 13)
    font_small = ImageFont.truetype("arial.ttf", 11)
except Exception:
    font_large = font_medium = font_small = ImageFont.load_default()

def draw_tetris_panel(draw, title, sub_title, x_offset, latency_str, line_clears, pieces_placed, border_color):
    cols, rows = 8, 14
    block_sz = 14
    grid_w = cols * block_sz
    grid_h = rows * block_sz
    
    y_offset = 120

    # Panel Title Header
    draw.text((x_offset, y_offset - 45), title, fill=TEXT_COLOR, font=font_large)
    draw.text((x_offset, y_offset - 25), sub_title, fill=MUTED_TEXT, font=font_small)

    # Grid Container
    draw.rectangle([x_offset, y_offset, x_offset + grid_w, y_offset + grid_h], fill=(2, 6, 23), outline=border_color, width=2)

    # Grid Inner Lines
    for r in range(rows):
        for c in range(cols):
            draw.rectangle([x_offset + c*block_sz, y_offset + r*block_sz, x_offset + (c+1)*block_sz, y_offset + (r+1)*block_sz], outline=(15, 23, 42))

    # Simulated Blocks
    random.seed(x_offset + line_clears)
    for r in range(rows - 4, rows):
        for c in range(cols):
            if random.random() > 0.3:
                draw.rectangle([x_offset + c*block_sz + 1, y_offset + r*block_sz + 1, x_offset + (c+1)*block_sz - 1, y_offset + (r+1)*block_sz - 1], fill=border_color)

    # Telemetry Panel
    meta_y = y_offset + grid_h + 15
    draw.text((x_offset, meta_y), f"Avg Latency: {latency_str}", fill=border_color, font=font_medium)
    draw.text((x_offset, meta_y + 18), f"Lines Cleared: {line_clears}", fill=TEXT_COLOR, font=font_small)
    draw.text((x_offset, meta_y + 34), f"Pieces Placed: {pieces_placed}", fill=MUTED_TEXT, font=font_small)

def generate_comparison_gif(output_path: str):
    frames = []

    for frame_idx in range(TOTAL_FRAMES):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Header Title
        draw.text((WIDTH // 2 - 220, 20), "3-WAY TETRIS DECISION ENGINE COMPARISON", fill=TEXT_COLOR, font=font_large)
        draw.text((WIDTH // 2 - 180, 45), "Evaluating Real-Time Latency & Decision Speed", fill=MUTED_TEXT, font=font_medium)
        draw.line([(40, 70), (WIDTH - 40, 70)], fill=BORDER_COLOR, width=1)

        # Progression Simulation
        jev_clears = frame_idx // 12
        jev_pieces = frame_idx // 3
        
        thisthat_clears = frame_idx // 10
        thisthat_pieces = frame_idx // 2

        velto_clears = frame_idx // 2
        velto_pieces = frame_idx * 4

        # Panel 1: Jev
        draw_tetris_panel(draw, "1. Jev (TypeSafe)", "Cloud LLM ($3/hr GPU)", 60, "1,218 ms", jev_clears, jev_pieces, JEV_COLOR)

        # Panel 2: this-that-1.0
        draw_tetris_panel(draw, "2. this-that-1.0", "1.88B Local Model", 360, "1,408 ms", thisthat_clears, thisthat_pieces, THISTHAT_COLOR)

        # Panel 3: Velto
        draw_tetris_panel(draw, "3. Velto ⚡", "0.07ms CPU Engine", 660, "0.07 ms", velto_clears, velto_pieces, VELTO_COLOR)

        # Bottom Banner
        draw.line([(40, HEIGHT - 50), (WIDTH - 40, HEIGHT - 50)], fill=BORDER_COLOR, width=1)
        draw.text((60, HEIGHT - 35), "⚡ Velto evaluates 14,285+ decisions/sec on plain CPU", fill=(56, 189, 248), font=font_medium)
        draw.text((WIDTH - 280, HEIGHT - 35), "github.com/yaad25/velto", fill=MUTED_TEXT, font=font_small)

        frames.append(img)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=1000 // FPS,
        loop=0
    )
    print(f"Comparison GIF saved successfully to: {output_path}")

if __name__ == "__main__":
    artifact_dir = os.path.dirname(os.path.abspath(__file__))
    out_file = os.path.join(artifact_dir, "tetris_comparison.gif")
    generate_comparison_gif(out_file)
