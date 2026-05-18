import os
import requests
import time
import sys
import textwrap
from google import genai
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURACIÓN DE RUTAS ---
GITHUB_USER = "ItsJuanKamilo"
REPO_NAME = "Resumenia"
IMAGE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/public/post_dia.jpg"

# Credenciales de entorno
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
IG_USER_ID = os.getenv("IG_ACCOUNT_ID")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN")

def generar_y_guardar():
    print("🤖 Consultando a Gemini 3 Flash Preview...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = (
        "Actúa como un experto en tecnología. Resume las 3 noticias más impactantes de hoy "
        "en Chile y el mundo. Usa 1 emoji por noticia. Sé directo y profesional. "
        "No uses negritas (asteriscos)."
    )
    
    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    texto_raw = response.text
    # Limpiamos asteriscos por si acaso Gemini los usa
    texto_limpio = texto_raw.replace("**", "").replace("*", "").strip()
    
    print("Contenido generado y limpio.")

    # --- DISEÑO EXÓTICO CON PILLOW ---
    width, height = 1080, 1080
    # Fondo: Negro Azulado Profundo (Muy elegante)
    img = Image.new('RGB', (width, height), color=(10, 12, 16))
    d = ImageDraw.Draw(img)

    # Intentar cargar fuente Roboto
    font_path = "src/Roboto.ttf"
    try:
        font_titulo = ImageFont.truetype(font_path, 80)
        font_cuerpo = ImageFont.truetype(font_path, 42)
        font_footer = ImageFont.truetype(font_path, 30)
    except:
        print("⚠️ No se halló Roboto.ttf en /src, usando fuente default.")
        font_titulo = font_cuerpo = font_footer = ImageFont.load_default()

    # 1. Elemento decorativo: Barra lateral neón
    d.rectangle([0, 0, 15, 1080], fill=(0, 255, 150))
    
    # 2. Título principal
    d.text((80, 100), "RESUMEN", font=font_titulo, fill=(255, 255, 255))
    d.text((80, 180), "TECH CHILE", font=font_titulo, fill=(0, 255, 150))

    # 3. Dibujar Noticias con ajuste de línea (Wrapping)
    y_position = 350
    noticias = texto_limpio.split('\n')
    
    for noticia in noticias:
        if not noticia.strip(): continue
        
        # Ajustamos el texto a un ancho de 40 caracteres
        wrapped_lines = textwrap.wrap(noticia, width=40)
        
        # Dibujar un pequeño indicador neón por noticia
        d.ellipse([60, y_position + 10, 75, y_position + 25], fill=(0, 255, 150))
        
        for line in wrapped_lines:
            d.text((100, y_position), line, font=font_cuerpo, fill=(230, 230, 230))
            y_position += 55
            
        y_position += 40 # Espacio entre bloques de noticias

    # 4. Footer con marca
    d.rectangle([15, 980, 1080, 1080], fill=(18, 20, 26))
    fecha_hoy = time.strftime('%d / %m / %Y')
    d.text((80, 1015), f"📅 {fecha_hoy} | Powered by Gemini 3", font=font_footer, fill=(120, 120, 120))
    d.text((880, 1015), "@resumenia", font=font_footer, fill=(0, 255, 150))

    # Guardado
    if not os.path.exists('public'): os.makedirs('public')
    img.save("public/post_dia.jpg", quality=100, subsampling=0)
    
    # Guardar texto para el pie de foto de Instagram
    with open("public/caption.txt", "w", encoding="utf-8") as f:
        f.write(texto_limpio)
        
    print("✅ Imagen exótica generada en public/post_dia.jpg")

def publicar_en_instagram():
    print(f"🚀 Iniciando publicación en Instagram...")
    
    if not os.path.exists("public/caption.txt"):
        print("❌ Error: No existe el archivo de caption.")
        return

    with open("public/caption.txt", "r", encoding="utf-8") as f:
        resumen = f.read()

    url_base = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    payload = {
        'image_url': IMAGE_URL,
        'caption': f"Resumen Tech de hoy 🤖\n\n{resumen}\n\n#Chile #Tech #IA #Santiago",
        'access_token': IG_TOKEN
    }
    
    res = requests.post(url_base, data=payload)
    if res.status_code != 200:
        print("❌ Error de Meta (Contenedor):", res.json())
        sys.exit(1)

    creation_id = res.json().get('id')
    print(f"📦 Contenedor creado (ID: {creation_id}).")
    
    # Pausa de seguridad antes de publicar
    time.sleep(10)
    
    url_pub = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish"
    r_pub = requests.post(url_pub, data={'creation_id': creation_id, 'access_token': IG_TOKEN})
    
    if r_pub.status_code == 200:
        print("🎉 ¡TODO LISTO! Post publicado en Instagram.")
    else:
        print("❌ Error al publicar:", r_pub.json())

if __name__ == "__main__":
    # Si no hay argumentos, genera por defecto
    arg = sys.argv[1] if len(sys.argv) > 1 else "generate"
    
    if arg == "generate":
        generar_y_guardar()
    elif arg == "publish":
        publicar_en_instagram()
