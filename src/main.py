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

def generar_datos_estrictos():
    print("🤖 Consultando a Gemini...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    # Nuevo Prompt estricto para noticias cortas (máx 120 caracteres)
    prompt = (
        "Resume las 3 noticias de tecnología más importantes de hoy en Chile y el mundo. "
        "Formato estricto: Una frase ultra-corta por noticia con un emoji. Máximo 120 caracteres por noticia. "
        "Separa cada noticia por un solo salto de línea. No uses asteriscos ni negritas."
    )
    
    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    texto_raw = response.text
    texto_limpio = texto_raw.replace("**", "").replace("*", "").strip()
    
    # Separamos las noticias en una lista. Gemini debería darnos exactamente 3 líneas.
    noticias_lista = [n.strip() for n in texto_limpio.split('\n') if n.strip()]
    # Nos aseguramos de tener al menos 3 elementos para evitar errores en Pillow
    while len(noticias_lista) < 3:
        noticias_lista.append("Actualizando últimas noticias...")
        
    print("Contenido generado y dividido.")
    return noticias_lista[:3] # Retornamos exactamente las primeras 3

def crear_imagen(noticias_3_items):
    print("🎨 Diseñando sobre tu template de boxes...")
    # 1. Abrimos tu plantilla (1080x1350)
    try:
        img = Image.open("src/template.png")
    except FileNotFoundError:
        print("❌ Error: No se encontró 'src/template.png' en la carpeta /src.")
        exit(1)
        
    d = ImageDraw.Draw(img)

    # 2. INTENTO ROBUSTO DE CARGA DE FUENTE ROBOTO (Linux case-sensitive)
    font_path = "src/Roboto.ttf"
    # Si no la encuentra como Roboto.ttf, probamos roboto.ttf (minúscula)
    if not os.path.exists(font_path):
        font_path = "src/roboto.ttf"

    try:
        # Usamos tamaños distintos según el área
        font_fecha = ImageFont.truetype(font_path, 35) # Pequeña para arriba
        font_noticia = ImageFont.truetype(font_path, 45) # Mediana para las cajitas
    except Exception as e:
        print(f"⚠️ Error cargando Roboto.ttf ({e}). Usando default.")
        font_fecha = font_noticia = ImageFont.load_default()

    # --- MATH DE PÍXELES: COORDENADAS EXACTAS ---

    # Color de texto (Usaremos blanco grisáceo para buen contraste contra verde)
    color_texto = (245, 245, 245)

    # 3. Estampar Fecha en la cajita superior (aprox. 540 centro X, 95 centro Y)
    fecha_hoy = time.strftime('%d / %m / %Y')
    # Calculamos ancho para centrar
    bbox_f = d.textbbox((0, 0), fecha_hoy, font=font_fecha)
    f_w, f_h = bbox_f[2] - bbox_f[0], bbox_f[3] - bbox_f[1]
    d.text((540 - f_w/2, 95 - f_h/2), fecha_hoy, font=font_fecha, fill=color_texto)

    # 4. Estampar las 3 Noticias en sus cajitas verdes
    # Coordenadas calculadas basadas en tu diseño:
    coords_y = [260, 580, 900] # Punto de inicio Y de cada cajita verde
    
    for i in range(3):
        noticia = noticias_3_items[i]
        x_start = 100 # Margen izquierdo
        y_start = coords_y[i]
        
        #textwrap para que no se pase del ancho de la cajita verde
        #Ancho máximo aproximado en caracteres para que quepa en el rectángulo
        wrapped_lines = textwrap.wrap(noticia, width=42) 
        
        # Dibujamos cada línea de la noticia
        for line in wrapped_lines:
            d.text((x_start, y_start), line, font=font_noticia, fill=color_texto)
            y_start += (font_noticia.size + 15) # Salto de línea

    # Guardado
    if not os.path.exists('public'): os.makedirs('public')
    img.save("public/post_dia.jpg", quality=100, subsampling=0)
    
    # Unimos las noticias para el caption de Instagram
    full_caption = "\n\n".join(noticias_3_items)
    with open("public/caption.txt", "w", encoding="utf-8") as f:
        f.write(full_caption)
        
    print("✅ Imagen exótica generada correctamente sobre cajitas verdes.")

def publicar_en_instagram():
    # ... (Esta función sigue igual, no cambia nada) ...
    print(f"🚀 Iniciando publicación en Instagram...")
    if not os.path.exists("public/caption.txt"):
        print("❌ Error: No existe el archivo de caption.")
        return
    with open("public/caption.txt", "r", encoding="utf-8") as f:
        resumen = f.read()
    url_base = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    payload = {
        'image_url': IMAGE_URL,
        'caption': f"Noticias Tech de hoy 🤖\n\n{resumen}\n\n#Chile #Tech #IA #Santiago",
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
        tres_noticias = generar_datos_estrictos()
        crear_imagen(tres_noticias)
    elif arg == "publish":
        publicar_en_instagram()
