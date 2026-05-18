import os
import requests
import time
import sys
import textwrap
from google import genai
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# --- CONFIGURACIÓN DE RUTAS ---
GITHUB_USER = "ItsJuanKamilo"
REPO_NAME = "Resumenia"
IMAGE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/public/post_dia.jpg"

# Credenciales de entorno
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY") # Necesitarás el secreto PEXELS_API_KEY
IG_USER_ID = os.getenv("IG_ACCOUNT_ID")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN")

def obtener_datos_pexels_estrictos():
    print("🤖 Consultando a Gemini...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = (
        "Actúa como un experto en tecnología. Resume las 3 noticias más impactantes de hoy "
        "en Chile y el mundo. Usa 1 emoji por noticia. Sé directo y profesional. "
        "Formato estricto: Una frase ultra-corta por noticia (máx 100 caracteres).\n"
        "No uses negritas (asteriscos).\n"
        "AL FINAL, añade una línea que diga 'KEYWORD:' seguido de una sola palabra en inglés "
        "para buscar una imagen de fondo relacionada (ejemplo: 'robotics', 'space', 'chip')."
    )
    
    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    texto_raw = response.text
    texto_limpio = texto_raw.replace("**", "").replace("*", "").strip()
    
    # Separamos el resumen de la palabra clave
    if "KEYWORD:" in texto_limpio:
        partes = texto_limpio.split("KEYWORD:")
        resumen_texto = partes[0].strip()
        keyword = partes[1].strip()
    else:
        resumen_texto = texto_limpio
        keyword = "technology"
        
    # Separamos las notícias para Pillow
    noticias = [n.strip() for n in resumen_texto.split('\n') if n.strip()]
    while len(noticias) < 3: noticias.append("Actualizando últimas noticias...")
        
    print(f"Contenido generado. Palabra clave: '{keyword}'")
    return noticias[:3], keyword

def descargar_imagen_fondo(keyword):
    print(f"📸 Buscando imagen de fondo para '{keyword}' en Pexels...")
    url = f"https://api.pexels.com/v1/search?query={keyword}&per_page=1&orientation=landscape"
    headers = {"Authorization": PEXELS_KEY}
    
    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        if not data.get('photos'):
            print("⚠️ Pexels no encontró fotos. Usando fondo oscuro.")
            return None
            
        img_url = data['photos'][0]['src']['medium']
        img_data = requests.get(img_url).content
        with open("src/header_img.jpg", "wb") as f:
            f.write(img_data)
        return "src/header_img.jpg"
    except Exception as e:
        print(f"⚠️ Error en Pexels: {e}. Usando fondo oscuro.")
        return None

def crear_imagen_final(noticias_3_items, header_path):
    print("🎨 Generando diseño completo...")
    # 1. Crear Lienzo en blanco Portrait (1080x1350)
    # RGBA para transparencias iniciales, convertiremos al final.
    canvas = Image.new("RGBA", (1080, 1350), (10, 12, 16, 255))
    d = ImageDraw.Draw(canvas)

    # 2. INTENTO ROBUSTO DE CARGA DE FUENTE ROBOTO (Linux case-sensitive)
    font_path = "src/Roboto.ttf"
    if not os.path.exists(font_path): font_path = "src/roboto.ttf"

    try:
        font_header_txt = ImageFont.truetype(font_path, 35) # Cajita fecha
        font_box_txt = ImageFont.truetype(font_path, 42) # Cajitas noticias
    except Exception as e:
        print(f"⚠️ Error cargando Roboto.ttf ({e}). Usando default (feo).")
        font_header_txt = font_box_txt = ImageFont.load_default()

    color_texto = (245, 245, 245) # Blanco grisáceo

    # 3. Dibujar Casilla de Fecha (Coordenadas de tu diseño)
    d.rectangle([415, 60, 665, 130], fill=(20, 22, 28, 255), outline=(0, 255, 150, 255), width=2)
    fecha_hoy = time.strftime('%d / %m / %Y')
    bbox_f = d.textbbox((0, 0), fecha_hoy, font=font_header_txt)
    f_w, f_h = bbox_f[2] - bbox_f[0], bbox_f[3] - bbox_f[1]
    d.text((540 - f_w/2, 95 - f_h/2), fecha_hoy, font=font_header_txt, fill=color_texto)

    # 4. Insertar Imagen de Pexels (En la parte de arriba)
    # Definimos el área Y=150 a Y=250 (entre fecha y primera caja)
    if header_path:
        header_img = Image.open(header_path).convert("RGBA")
        # Redimensionamos la imagen de stock
        header_img = header_img.resize((1000, 100), Image.Resampling.LANCZOS)
        # Filtro sutil para que no brille tanto
        enhancer = ImageEnhance.Brightness(header_img)
        header_img = enhancer.enhance(0.7)
        # La pegamos centrada
        canvas.paste(header_img, (40, 150)) 
    else:
        d.rectangle([40, 150, 1040, 250], fill=(20, 22, 28, 255), outline=(0, 255, 150, 100), width=1)
        d.text((540, 200), "TECHNOLOGY NEWS CHILE", font=font_header_txt, fill=(0, 255, 150, 150), anchor="mm")

    # 5. Dibujar las 3 Cajitas Verdes (Exactly like your design)
    # Coordenadas Y de inicio: [260, 580, 900]
    # y_position es donde EMPIEZA el texto en cada caja
    y_box_starts = [260, 580, 900]
    
    for i in range(3):
        noticia = noticias_3_items[i]
        box_y = y_box_starts[i]
        
        # Dibujar rectángulo verde
        d.rectangle([80, box_y, 1000, box_y + 180], fill=(18, 48, 38, 255), outline=(0, 255, 150, 255), width=2)
        
        # Estampar texto dentro del rectángulo con Textwrap
        x_text = 110 # Margen izquierdo
        y_text = box_y + 30 # Punto de inicio del texto dentro de la caja
        
        #textwrap para que no se pase del ancho de la cajita verde (~40 chars)
        wrapped_lines = textwrap.wrap(noticia, width=42) 
        
        for line in wrapped_lines:
            # Dibujamos el texto (Punto de inicio y salto de línea)
            d.text((x_text, y_text), line, font=font_box_txt, fill=color_texto)
            y_text += (font_box_txt.size + 15) # Salto de línea

    # 6. Dibujar Footer (@resumenia bottom)
    d.text((950, 1310), "@resumenia", font=font_header_txt, fill=(0, 255, 150, 200), anchor="rm")

    # --- ARREGLO ERROR 'KeyError: RGBA' al salvar JPEG ---
    # Convertimos de RGBA (transparencia) a RGB (fondo sólido)
    img_final = canvas.convert("RGB")
    
    if not os.path.exists('public'): os.makedirs('public')
    img_final.save("public/post_dia.jpg", "JPEG", quality=100)
    
    # Unimos las noticias para el caption de Instagram
    full_caption = "\n\n".join(noticias_3_items)
    with open("public/caption.txt", "w", encoding="utf-8") as f:
        f.write(full_caption)
        
    print("✅ Imagen exótica generada exitosamente.")

def publicar_en_instagram():
    # ... (Esta función sigue igual, solo necesita el token nuevo de 60 días) ...
    print(f"🚀 Iniciando publicación en Instagram...")
    if not os.path.exists("public/caption.txt"):
        print("❌ Error: No existe el archivo de caption.")
        return
    with open("public/caption.txt", "r", encoding="utf-8") as f:
        resumen = f.read()
    url_base = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    payload = {
        'image_url': IMAGE_URL,
        'caption': f"Noticias Tech 🤖\n\n{resumen}\n\n#Chile #IA #Santiago",
        'access_token': IG_TOKEN
    }
    res = requests.post(url_base, data=payload)
    if res.status_code != 200:
        print("❌ Error:", res.json())
        sys.exit(1)
    creation_id = res.json().get('id')
    time.sleep(15)
    url_pub = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish"
    requests.post(url_pub, data={'creation_id': creation_id, 'access_token': IG_TOKEN})
    print("🎉 ¡TODO LISTO! Post Portrait publicado.")

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "generate"
    
    if arg == "generate":
        tres_noticias, keyword = obtener_datos_pexels_estrictos()
        header_path = descargar_imagen_fondo(keyword)
        crear_imagen_final(tres_noticias, header_path)
    elif arg == "publish":
        publicar_en_instagram()
