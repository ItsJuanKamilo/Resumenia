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
# Esta URL debe ser pública. Asegúrate de tener GitHub Pages activado en la rama main
IMAGE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/public/post_dia.jpg"

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY") # Secret PEXELS_API_KEY requerido
IG_USER_ID = os.getenv("IG_ACCOUNT_ID")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN") # Debe ser el de 60 días

def obtener_datos():
    print("🤖 Consultando a Gemini...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = (
        "Resume las 3 noticias de tecnología más importantes de hoy en Chile y el mundo. "
        "Sé directo. Máximo 130 caracteres por noticia. No uses asteriscos.\n"
        "AL FINAL añade una línea que diga 'KEYWORD:' y una palabra en inglés para la foto de fondo."
    )
    
    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    raw = response.text.replace("**", "").replace("*", "").strip()
    
    if "KEYWORD:" in raw:
        resumen, kw = raw.split("KEYWORD:")
        return resumen.strip().split('\n')[:3], kw.strip()
    return raw.split('\n')[:3], "technology"

def descargar_foto(keyword):
    print(f"📸 Buscando foto en Pexels para: {keyword}")
    url = f"https://api.pexels.com/v1/search?query={keyword}&per_page=1&orientation=landscape"
    headers = {"Authorization": PEXELS_KEY}
    try:
        res = requests.get(url, headers=headers).json()
        if not res.get('photos'):
            print("⚠️ Pexels no encontró fotos. Usando fondo oscuro por defecto.")
            return None
        img_url = res['photos'][0]['src']['large2x']
        return Image.open(requests.get(img_url, stream=True).raw)
    except Exception as e:
        print(f"⚠️ Error en Pexels: {e}. Usando fondo oscuro por defecto.")
        return None

def crear_imagen(noticias, foto_pexels):
    print("🎨 Aplicando diseño sobre template.png (Imagen Total y Texto Corregido)...")
    
    try:
        base = Image.open("src/template.png").convert("RGBA")
    except:
        print("❌ Error: No se encontró src/template.png en la carpeta /src.")
        sys.exit(1)

    font_path = "src/Roboto.ttf"
    if not os.path.exists(font_path): font_path = "src/roboto.ttf"
    try:
        font = ImageFont.truetype(font_path, 42)
    except:
        font = ImageFont.load_default()

    if foto_pexels:
        # --- NUEVO ENFOQUE: IMAGEN TOTAL EN EL FONDO BLANCO (Full Bleed) ---
        # El área blanca útil de tu plantilla es aprox 1080x410.
        target_width = 1080
        target_height = 410 # Altura estimada del bloque blanco antes del rojo
        target_ratio = target_width / target_height

        orig_width, orig_height = foto_pexels.size
        orig_ratio = orig_width / orig_height

        if orig_ratio > target_ratio:
            # La imagen de stock es más ancha: ajustamos por altura y recortamos ancho
            new_height = target_height
            new_width = int(new_height * orig_ratio)
            foto_resized = foto_pexels.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # Recortamos para centrar horizontalmente
            left = (new_width - target_width) / 2
            foto_final = foto_resized.crop((left, 0, left + target_width, target_height))
        else:
            # La imagen de stock es más alta: ajustamos por ancho y recortamos alto
            new_width = target_width
            new_height = int(new_width / orig_ratio)
            foto_resized = foto_pexels.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # Recortamos para centrar verticalmente
            top = (new_height - target_height) / 2
            foto_final = foto_resized.crop((0, top, target_width, top + target_height))

        # Filtro sutil para oscurecer el stock y que el template resalte
        enhancer = ImageEnhance.Brightness(foto_final)
        foto_final = enhancer.enhance(0.9)

        # Pegamos en la esquina superior izquierda (0,0) cubriendo todo el blanco
        base.paste(foto_final, (0, 0))
        print("✅ Imagen de Pexels aplicada a sangre (full bleed) cubriendo el fondo blanco.")

    d = ImageDraw.Draw(base)
    
    # --- POSICIONAMIENTO CORREGIDO MANTENIDO ---
    # Bajamos el inicio a 580 para limpiar el título "NOTICIAS" del template
    y_start = 580 
    x_margin = 85
    espacio_entre_items = 240 

    for noticia in noticias:
        if not noticia.strip(): continue
        # textwrap para que no se pase de los 1080px de ancho
        lines = textwrap.wrap(noticia, width=42)
        y_text = y_start
        for line in lines:
            d.text((x_margin, y_text), line, font=font, fill=(255, 255, 255))
            y_text += 55 # Salto de línea
        y_start += espacio_entre_items

    # IMPORTANTE: Convertir a RGB para evitar error de transparencia en JPEG
    final = base.convert("RGB")
    if not os.path.exists('public'): os.makedirs('public')
    final.save("public/post_dia.jpg", "JPEG", quality=95)
    print("✅ Imagen generada PERFECTAMENTE POSICIONADA y con fondo total en public/post_dia.jpg")

def publicar_en_instagram():
    print("🚀 Iniciando proceso de publicación en Meta API...")
    
    if not os.path.exists("public/caption.txt"):
        print("❌ Error: No existe el caption. Genera la imagen primero.")
        return

    with open("public/caption.txt", "r", encoding="utf-8") as f:
        caption_text = f.read()

    # 1. Crear el contenedor del post
    url_base = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    payload = {
        'image_url': IMAGE_URL,
        'caption': f"Resumen Tech de hoy 🤖\n\n{caption_text}\n\n#Chile #IA #Resumenia",
        'access_token': IG_TOKEN
    }
    
    r = requests.post(url_base, data=payload)
    res_data = r.json()
    
    if r.status_code != 200:
        print(f"❌ Error al crear contenedor de Meta: {res_data}")
        sys.exit(1)

    creation_id = res_data.get('id')
    print(f"📦 Contenedor creado con éxito. ID: {creation_id}")

    # Esperar a que Instagram procese la imagen de la URL (Subimos a 30s por seguridad)
    print("⏳ Esperando a que Instagram procese la imagen...")
    time.sleep(30)

    # 2. Publicar el contenedor
    url_pub = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish"
    r_pub = requests.post(url_pub, data={
        'creation_id': creation_id,
        'access_token': IG_TOKEN
    })
    
    if r_pub.status_code == 200:
        print("🎉 ¡TODO LISTO! Post Portrait publicado exitosamente en Instagram.")
    else:
        print(f"❌ Error al publicar en Instagram: {r_pub.json()}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "generate"
    
    if mode == "generate":
        # Aseguramos limpieza antes de generar
        if os.path.exists("public/post_dia.jpg"): os.remove("public/post_dia.jpg")
        noticias, kw = obtener_datos()
        foto = descargar_foto(kw)
        crear_imagen(noticias, foto)
        with open("public/caption.txt", "w", encoding="utf-8") as f:
            f.write("\n\n".join(noticias))
    elif mode == "publish":
        publicar_en_instagram()
