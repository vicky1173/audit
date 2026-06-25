"""Generate placeholder company logo."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"


def create_logo():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    width, height = 400, 120
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Gradient-like background shape
    draw.rounded_rectangle([0, 10, width, height - 10], radius=16, fill=(30, 58, 95, 255))

    # Diamond icon
    cx, cy = 55, height // 2
    diamond = [(cx, cy - 30), (cx + 28, cy), (cx, cy + 30), (cx - 28, cy)]
    draw.polygon(diamond, fill=(59, 130, 246, 255))
    draw.polygon(
        [(cx, cy - 18), (cx + 16, cy), (cx, cy + 18), (cx - 16, cy)],
        fill=(139, 92, 246, 255),
    )

    try:
        font_lg = ImageFont.truetype("arial.ttf", 28)
        font_sm = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font_lg = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    draw.text((100, 35), "AUDIT INTELLIGENCE", fill=(255, 255, 255, 255), font=font_lg)
    draw.text((100, 72), "SUITE", fill=(147, 197, 253, 255), font=font_lg)

    img.save(LOGO_PATH, "PNG")
    print(f"Logo created: {LOGO_PATH}")


if __name__ == "__main__":
    create_logo()
