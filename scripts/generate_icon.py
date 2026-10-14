import os
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_app_icon():
    os.makedirs("assets", exist_ok=True)
    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # 1. macOS Squircle Geometry (Apple standard 1024x1024 template: margin 80, radius 220)
    margin = 80
    box = [margin, margin, size - margin, size - margin]
    radius = 220

    # Base mask for the rounded squircle
    base_mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(base_mask)
    mask_draw.rounded_rectangle(box, radius=radius, fill=255)

    # 2. Rich Multi-stop Gradient Background (Apple Music Coral Red -> Violet -> Deep Indigo)
    gradient = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gradient)

    c1 = (250, 45, 85)   # Apple Pink/Red #FA2D55
    c2 = (147, 51, 234)  # Rich Violet #9333EA
    c3 = (30, 27, 75)    # Midnight Navy #1E1B4B

    height = box[3] - box[1]
    for y in range(box[1], box[3]):
        ratio = (y - box[1]) / height
        if ratio < 0.5:
            r = ratio * 2
            red = int(c1[0] + (c2[0] - c1[0]) * r)
            green = int(c1[1] + (c2[1] - c1[1]) * r)
            blue = int(c1[2] + (c2[2] - c1[2]) * r)
        else:
            r = (ratio - 0.5) * 2
            red = int(c2[0] + (c3[0] - c2[0]) * r)
            green = int(c2[1] + (c3[1] - c2[1]) * r)
            blue = int(c2[2] + (c3[2] - c2[2]) * r)
        g_draw.line([(box[0], y), (box[2], y)], fill=(red, green, blue, 255))

    img.paste(gradient, (0, 0), base_mask)

    # 3. Soft Drop Shadow for Inner Elements
    shadow_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_layer)

    # 4. Sound Wave Bars
    center_x = size // 2
    center_y = size // 2 - 30

    bar_heights = [140, 260, 420, 540, 390, 280, 160]
    bar_width = 44
    spacing = 34
    total_w = len(bar_heights) * bar_width + (len(bar_heights) - 1) * spacing
    start_x = center_x - total_w // 2

    # Draw bars with slight shadow
    for i, h in enumerate(bar_heights):
        x0 = start_x + i * (bar_width + spacing)
        y0 = center_y - h // 2
        x1 = x0 + bar_width
        y1 = center_y + h // 2

        # Shadow
        s_draw.rounded_rectangle([x0, y0 + 10, x1, y1 + 10], radius=22, fill=(0, 0, 0, 90))

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(12))
    img.alpha_composite(shadow_layer)

    # Foreground Draw
    fg_draw = ImageDraw.Draw(img)

    for i, h in enumerate(bar_heights):
        x0 = start_x + i * (bar_width + spacing)
        y0 = center_y - h // 2
        x1 = x0 + bar_width
        y1 = center_y + h // 2

        # Center bar accent
        if i in (2, 3, 4):
            fill_color = (255, 255, 255, 255)
        else:
            fill_color = (255, 255, 255, 210)

        fg_draw.rounded_rectangle([x0, y0, x1, y1], radius=22, fill=fill_color)

    # 5. Bottom Modern Badge: "FLAC ➜ ALAC"
    badge_w = 440
    badge_h = 86
    badge_x0 = center_x - badge_w // 2
    badge_y0 = size - margin - 170
    badge_box = [badge_x0, badge_y0, badge_x0 + badge_w, badge_y0 + badge_h]

    # Glassmorphic Badge Background
    fg_draw.rounded_rectangle(badge_box, radius=43, fill=(0, 0, 0, 140), outline=(255, 255, 255, 75), width=3)

    # Badge Typography
    font_path = "/System/Library/Fonts/SFCompact.ttf"
    if not os.path.exists(font_path):
        font_path = "/System/Library/Fonts/Helvetica.ttc"

    try:
        font = ImageFont.truetype(font_path, 34)
    except Exception:
        font = ImageFont.load_default()

    # Draw Text Parts manually to guarantee clean rendering across all fonts
    left_text = "FLAC"
    right_text = "ALAC"

    left_bbox = fg_draw.textbbox((0, 0), left_text, font=font)
    right_bbox = fg_draw.textbbox((0, 0), right_text, font=font)

    left_w = left_bbox[2] - left_bbox[0]
    right_w = right_bbox[2] - right_bbox[0]
    arrow_w = 36
    inner_spacing = 24

    total_content_w = left_w + inner_spacing + arrow_w + inner_spacing + right_w
    cur_x = center_x - total_content_w // 2
    text_y = badge_y0 + (badge_h - (left_bbox[3] - left_bbox[1])) // 2 - 2

    # Draw FLAC
    fg_draw.text((cur_x, text_y), left_text, fill=(255, 255, 255, 255), font=font)
    cur_x += left_w + inner_spacing

    # Draw clean vector arrow
    arrow_cy = badge_y0 + badge_h // 2
    arrow_x0 = cur_x
    arrow_x1 = cur_x + arrow_w
    fg_draw.line([(arrow_x0, arrow_cy), (arrow_x1 - 4, arrow_cy)], fill=(56, 189, 248, 255), width=5)
    fg_draw.polygon([
        (arrow_x1, arrow_cy),
        (arrow_x1 - 10, arrow_cy - 8),
        (arrow_x1 - 10, arrow_cy + 8)
    ], fill=(56, 189, 248, 255))
    cur_x += arrow_w + inner_spacing

    # Draw ALAC
    fg_draw.text((cur_x, text_y), right_text, fill=(56, 189, 248, 255), font=font)

    # 6. Sleek Border Highlight
    border_draw = ImageDraw.Draw(img)
    border_draw.rounded_rectangle(box, radius=radius, outline=(255, 255, 255, 50), width=4)

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
    import shutil
    shutil.rmtree(iconset_dir)
    print("Created assets/icon.icns successfully!")

if __name__ == "__main__":
    create_app_icon()
