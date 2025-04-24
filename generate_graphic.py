from PIL import Image, ImageDraw, ImageFont
import cairosvg
from io import BytesIO
import os

# Konfiguration
WIDTH, HEIGHT = 1080, 1080
BACKGROUND_COLOR = "#dfddd8"
TITLE_FONT_PATH = "fonts/Montserrat-SemiBold.ttf"
TEXT_FONT_PATH = "fonts/Montserrat-Light.ttf"
LOGO_PATH = "logo.svg"
OUTPUT_PATH = "graphics/news_post.png"

def render_svg_to_pil(svg_path, width):
    png_data = cairosvg.svg2png(url=svg_path, output_width=width)
    return Image.open(BytesIO(png_data)).convert("RGBA")

def create_graphic(title, text):
    # Hintergrund erstellen
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    # Logo
    logo = render_svg_to_pil(LOGO_PATH, width=200)
    image.paste(logo, (40, 40), mask=logo)

    # Fonts laden
    title_font = ImageFont.truetype(TITLE_FONT_PATH, 60)
    text_font = ImageFont.truetype(TEXT_FONT_PATH, 36)

    # Titel
    draw.text((40, 280), title, font=title_font, fill="black")

    # Text (mehrzeilig automatisch umbrechen)
    def draw_multiline(draw, text, font, x, y, max_width, line_spacing):
        lines = []
        words = text.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if draw.textlength(test_line, font=font) <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        lines.append(line)
        for i, l in enumerate(lines):
            draw.text((x, y + i * line_spacing), l, font=font, fill="black")

    draw_multiline(draw, text, text_font, x=40, y=380, max_width=1000, line_spacing=48)

    # Speichern
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    image.save(OUTPUT_PATH)
    print(f"✅ Grafik gespeichert unter {OUTPUT_PATH}")

# Beispielausführung
if __name__ == "__main__":
    create_graphic(
        title="BREAKING: Emirates erhält Autismus-Zertifizierung",
        text="Die Fluggesellschaft Emirates wurde als weltweit erste Airline für Autismusfreundlichkeit zertifiziert."
    )
