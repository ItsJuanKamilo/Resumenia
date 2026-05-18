import os
import requests
import time
import sys
import textwrap
from google import genai
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# --- CONFIGURACIÓN ---
GITHUB_USER = "ItsJuanKamilo"
REPO_NAME = "Resumenia"
IMAGE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/public/post_dia.jpg"

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY") 
IG_USER_ID = os.getenv("IG_ACCOUNT_ID")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN")

def obtener_datos():
    print("🤖 Consultando a Gemini...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = (
        "Resume las 3 noticias de tecnología más importantes de hoy. "
        "Sé directo. Máximo 130 caracteres por noticia. No uses asteriscos.\n"
        "AL FINAL añade 'KEYWORD:' y una palabra en inglés para la foto."
    )
    
    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    raw = response.text.replace("**", "").replace("*", "").strip()
    
    if "KEYWORD:" in raw:
        resumen, kw = raw.split("KEYWORD:")
        return resumen.strip().split('\n')[:3], kw.strip()
    return raw.split('\n')[:3], "technology"

def descargar_foto(keyword):
    print(f"📸 Buscando foto: {keyword}")
    url = f"https://api.pexels.com/v1/search?query={keyword}&per_page=1&orientation=landscape"
    headers = {"Authorization": PEXELS_KEY}
    try:
        res = requests.get(url, headers=headers).json()
        img_url = res['photos'][0]['src']['large']
        return Image.open(requests.get(img_url, stream=True).raw)
    except:
        return None

def crear_imagen(noticias, foto_pexels):
    print("🎨 Aplicando diseño sobre template.png...")
    
    # 1. Cargar Plantilla
    try:
        base = Image.open("src/template.png").convert("RGBA")
    except:
        print("❌ Error: No se encontró src/template.png")
        return

    # 2. Cargar Fuente
    font_path = "src/Roboto.ttf"
    if not os.path.exists(font_path): font_path = "src/roboto.ttf"
    try:
        font = ImageFont.truetype(font_path, 42)
    except:
        font = ImageFont.load_default()

    # --- POSICIONAMIENTO ---

    # A. Encajar imagen en el espacio blanco (superior)
    if foto_pexels:
        # Definimos un margen para que no toque los bordes del blanco
        # Espacio blanco aprox: 1080x410
        foto_resized = foto_pexels.resize((980, 320), Image.Resampling.LANCZOS)
        # Pegar centrada en el área blanca (x=50, y=45)
        base.paste(foto_resized, (50, 45))

    d = ImageDraw.Draw(base)
    
    # B. Posicionar Noticias en el bloque rojo
    # El bloque rojo útil para texto empieza en Y=520 tras el título "NOTICIAS"
    y_start = 520
    x_margin = 85
    espacio_entre_items = 240 # Espacio vertical para cada noticia

    for noticia in noticias:
        if not noticia.strip(): continue
        
        # Ajuste de línea automático (Ancho de la parte roja)
        lines = textwrap.wrap(noticia, width=42)
        
        y_text = y_start
        for line in lines:
            d.text((x_margin, y_text), line, font=font, fill=(255, 255, 255))
            y_text += 55 # Salto de línea
            
        y_start += espacio_entre_items

    # 3. Guardar (Convertir a RGB para evitar error de transparencia)
    final = base.convert("RGB")
    if not os.path.exists('public'): os.makedirs('public')
    final.save("public/post_dia.jpg", "JPEG", quality=95)
    print("✅ Imagen generada perfectamente.")

def publicar():
    # Mantenemos tu lógica de publicación...
    print("🚀 Publicando en Instagram...")
    # (Aquí va el resto de tu código de publicación que ya funciona)

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "generate"
    if arg == "generate":
        items, kw = obtener_datos()
        foto = descargar_foto(kw)
        crear_imagen(items, foto)
        with open("public/caption.txt", "w", encoding="utf-8") as f:
            f.write("\n\n".join(items))
    elif arg == "publish":
        publicar()
