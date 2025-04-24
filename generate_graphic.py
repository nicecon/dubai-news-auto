from PIL import Image, ImageDraw, ImageFont
import os

# Texte (Beispiel)
headline = "Dubais Emirates wird zur ersten\nAutismus-zertifizierten Airline"
body = "Die Fluggesellschaft wurde nach intensiver Zusammenarbeit mit der IBCCES ausgezeichnet."

# Farben & Pfade
background_color = "#f4f1ee"  # Farbe aus deinem Upload
logo_path = "logo.svg"
output_path = "news/graphics/news_post.png"

# Bild erstellen
img = Image.new("RGB", (1080, 1080), background_color)
draw = ImageDraw.Draw(img)

# Fonts (müssen lokal sein oder später ins Repo)
headline_font = ImageFont.truetype("fonts/Montserrat-SemiBold.ttf", 60)
body_font = ImageFont.truetype("fonts/Montserrat-Light.ttf", 36)

# Textpositionen
draw.text((60, 80), headline, font=headline_font, fill="black", align="left")
draw.text((60, 360), body, font=body_font, fill="black", align="left")

# Logo einfügen
if os.path.exists(logo_path):
    from cairosvg import svg2png
    svg2png(url=logo_path, write_to="temp_logo.png")
    logo = Image.open("temp_logo.png").convert("RGBA")
    logo = logo.resize((200, 200))
    img.paste(logo, (60, 800), logo)

# Speichern
os.makedirs("news/graphics", exist_ok=True)
img.save(output_path)
print(f"✅ Grafik gespeichert unter {output_path}")
