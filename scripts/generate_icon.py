import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

def create_app_icon():
    os.makedirs("assets", exist_ok=True)
    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. macOS Squircle Background with Gradient
    # Squircle bounding box (with macOS margins)
    margin = 80
    box = [margin, margin, size - margin, size - margin]
    radius = 210

    # Draw gradient inside rounded rectangle
    base_mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(base_mask)
    mask_draw.rounded_rectangle(box, radius=radius, fill=255)

    gradient = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gradient)

    # Vertical gradient: Deep Blue -> Vibrant Violet / Apple Music Pink-Purple
    top_color = (15, 23, 42)      # Deep Slate Navy
    bottom_color = (99, 102, 241) # Vibrant Indigo

    for y in range(box[1], box[3]):
        ratio = (y - box[1]) / (box[3] - box[1])
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        g_draw.line([(box[0], y), (box[2], y)], fill=(r, g, b, 255))

    img.paste(gradient, (0, 0), base_mask)

    # 2. Subtle Border Highlight
    border_draw = ImageDraw.Draw(img)
    border_draw.rounded_rectangle(box, radius=radius, outline=(255, 255, 255, 45), width=4)

    # 3. Draw Stylized Sound Wave / Music Note & Arrow
    # Center audio wave bars
    center_x = size // 2
    center_y = size // 2 - 20

    # Draw modern equalizer / audio wave bars
    bar_heights = [120, 220, 360, 480, 340, 240, 140]
    bar_width = 38
    spacing = 30
    total_w = len(bar_heights) * bar_width + (len(bar_heights) - 1) * spacing
    start_x = center_x - total_w // 2

    # Accent color: Cyan to White
    for i, h in enumerate(bar_heights):
        x0 = start_x + i * (bar_width + spacing)
        y0 = center_y - h // 2
        x1 = x0 + bar_width
        y1 = center_y + h // 2

        # Color transition across bars
        alpha = 230 + (i % 2) * 25
        fill_color = (56, 189, 248, alpha) if i in (2, 3, 4) else (255, 255, 255, 220)
        border_draw.rounded_rectangle([x0, y0, x1, y1], radius=19, fill=fill_color)

    # 4. Bottom Badge Label: "FLAC -> ALAC"
    badge_w = 420
    badge_h = 80
    badge_x0 = center_x - badge_w // 2
    badge_y0 = size - margin - 150
    badge_box = [badge_x0, badge_y0, badge_x0 + badge_w, badge_y0 + badge_h]

    # Glassmorphism badge background
    border_draw.rounded_rectangle(badge_box, radius=40, fill=(0, 0, 0, 110), outline=(255, 255, 255, 60), width=3)

    # Text
    try:
        font = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 40)
    except Exception:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 38)
        except Exception:
            font = ImageFont.load_default()

    text = "FLAC ➔ ALAC"
    bbox = border_draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    border_draw.text((center_x - tw // 2, badge_y0 + (badge_h - th) // 2 - 4), text, fill=(255, 255, 255, 240), font=font)

    # Save PNG
    png_path = "assets/icon.png"
    img.save(png_path, "PNG")
    print(f"Created {png_path}")

    # Generate macOS .icns via iconutil
    iconset_dir = "assets/icon.iconset"
    os.makedirs(iconset_dir, exist_ok=True)

    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]

    for s, name in sizes:
        resized = img.resize((s, s), Image.Resampling.LANCZOS)
        resized.save(os.path.join(iconset_dir, name))

    subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", "assets/icon.icns"], check=True)
    shutil.rmtree(iconset_dir)
    print("Created assets/icon.icns successfully!")

if __name__ == "__main__":
    import shutil
    create_app_icon()
