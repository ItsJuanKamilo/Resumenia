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

# Credenciales de entorno (Asegúrate de tener el TOKEN de 60 días)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY") 
IG_USER_ID = os.getenv("IG_ACCOUNT_ID")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN")

def obtener_datos():
    print("🤖 Consultando a Gemini...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = (
        "Resume las 3 noticias de tecnología más importantes de hoy en Chile y el mundo. "
        "Sé directo y profesional. Máximo 120 caracteres por noticia. "
        "IMPORTANTE: No uses números, ni viñetas, ni asteriscos. Solo el texto.\n"
        "AL FINAL añade una línea: 'KEYWORD:' y una palabra en inglés para la foto relacionada."
    )
    
    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    raw = response.text.replace("**", "").replace("*", "").strip()
    
    if "KEYWORD:" in raw:
        resumen, kw = raw.split("KEYWORD:")
        # Limpiamos posibles números residuales por si Gemini se equivoca
        lineas = [l.strip() for l in resumen.strip().split('\n') if l.strip()]
        return lineas[:3], kw.strip()
    return raw.split('\n')[:3], "technology"

def descargar_foto(keyword):
    print(f"📸 Buscando foto para '{keyword}' en Pexels...")
    url = f"https://api.pexels.com/v1/search?query={keyword}&per_page=1&orientation=landscape"
    headers = {"Authorization": PEXELS_KEY}
    try:
        res = requests.get(url, headers=headers).json()
        if not res.get('photos'):
            print("⚠️ Pexels no encontró fotos. Usando fondo oscuro.")
            return None
        img_url = res['photos'][0]['src']['large2x']
        return Image.open(requests.get(img_url, stream=True).raw)
    except Exception as e:
        print(f"⚠️ Error en Pexels: {e}. Usando fondo oscuro.")
        return None

def crear_imagen(noticias, foto_pexels):
    print("🎨 Ajustando diseño final (Centrado, compacto y reposicionado)...")
    
    # 1. Cargar Plantilla (src/template.png)
    try:
        base = Image.open("src/template.png").convert("RGBA")
        if base.size != (1080, 1350):
            print("⚠️ Nota: 'src/template.png' no es 1080x1350, redimensionando...")
            base = base.resize((1080, 1350))
    except FileNotFoundError:
        print("❌ Error: No se encontró 'src/template.png' en la carpeta /src.")
        sys.exit(1)

    # 2. INTENTO ROBUSTO DE CARGA DE FUENTE ROBOTO (Case-sensitive Linux)
    font_path = "src/Roboto.ttf"
    if not os.path.exists(font_path): font_path = "src/roboto.ttf"
    try:
        font = ImageFont.truetype(font_path, 42)
    except:
        print(f"⚠️ Error cargando {font_path}. Usando default.")
        font = ImageFont.load_default()

    # --- AJUSTE DE IMAGEN HEADER PARA CUBRIR ESPACIO BLANCO ---
    if foto_pexels:
        # Aumentamos la altura de 415 a 430 para que choque con el rojo
        target_w, target_h = 1080, 430 
        
        # Redimensionar y recortar (Crop center) para full bleed
        orig_w, orig_h = foto_pexels.size
        ratio = max(target_w/orig_w, target_h/orig_h)
        new_size = (int(orig_w*ratio), int(orig_h*ratio))
        foto_res = foto_pexels.resize(new_size, Image.Resampling.LANCZOS)
        
        left = (new_size[0] - target_w)/2
        top = (new_size[1] - target_h)/2
        foto_final = foto_res.crop((left, top, left + target_w, top + target_h))
        
        # Pegar en el tope exacto (0,0) cubriendo el blanco
        base.paste(foto_final, (0, 0))
        print("✅ Imagen de header aplicada a sangre cubriendo el fondo blanco.")

    d = ImageDraw.Draw(base)

    # --- AJUSTES DE POSICIONAMIENTO Y CENTRADO ---
    # Coordenada Y de inicio del texto: Bajamos más para no tocar "NOTICIAS" (de 620 a 680)
    y_start = 680 
    # Ancho máximo en caracteres por línea para centrado
    ancho_max = 45 

    print("Centrando y estampando noticias compactas...")
    for noticia in noticias:
        # Quitamos números residuales al inicio ("1. Noticia" -> "Noticia")
        noticia = noticia.lstrip('0123456789. ')
        
        if not noticia.strip(): continue
        
        #textwrap para que no se pase del ancho de la plantilla
        lines = textwrap.wrap(noticia, width=ancho_max)
        
        # Dibujar cada línea centrada horizontalmente (Math de píxeles)
        y_text = y_start
        for line in lines:
            bbox = d.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            # d.text((X, Y)) -> X = 540 (mitad de 1080) - mitad del ancho del texto
            d.text((540 - w/2, y_text), line, font=font, fill=(245, 245, 245))
            y_text += 50 # Separación entre LÍNEAS de la misma noticia (Reducida)
            
        y_start += 50 # Separación entre BLOQUES de noticias (Reducida drásticamente)

    # 3. Guardado: Convertir RGBA a RGB obligatoriamente para salvar como JPG
    final = base.convert("RGB")
    if not os.path.exists('public'): os.makedirs('public')
    final.save("public/post_dia.jpg", "JPEG", quality=100)
    
    # Guardar noticias para el caption
    with open("public/caption.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(noticias))
        
    print("✅ Imagen estética generada correctamente sobre plantilla.")

def publicar_en_instagram():
    # ... (Misma función de publicación que ya tienes configurada con el token) ...
    print("🚀 Publicando...")
    if not os.path.exists("public/caption.txt"): return
    with open("public/caption.txt", "r", encoding="utf-8") as f:
        caption = f.read()

    url_base = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    payload = {
        'image_url': IMAGE_URL,
        'caption': f"Resumen Tech Santiago 🤖\n\n{caption}\n\n#Chile #IA #Tech #Santiago #Resumenia",
        'access_token': IG_TOKEN # Debe ser el TOKEN extendido de 60 días
    }
    
    res = requests.post(url_base, data=payload)
    
    if res.status_code == 200:
        c_id = res.json().get('id')
        print(f"📦 Contenedor creado (ID: {c_id}). Esperando procesamiento...")
        # Pausa técnica de seguridad (Aumentada a 30s)
        time.sleep(30) 
        
        url_pub = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish"
        r_pub = requests.post(url_pub, data={'creation_id': c_id, 'access_token': IG_TOKEN})
        
        if r_pub.status_code == 200:
            print("🎉 ¡TODO LISTO! Post Portrait publicado exitosamente en Instagram.")
        else:
            print(f"❌ Error Meta (Publicación): {r_pub.json()}")
    else:
        print(f"❌ Error Meta (Contenedor): {res.json()}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "generate"
    
    if mode == "generate":
        # Aseguramos limpieza antes de generar
        if os.path.exists("public/post_dia.jpg"): os.remove("public/post_dia.jpg")
        
        noticias, kw = obtener_datos()
        foto = descargar_foto(kw)
        crear_imagen(noticias, foto)
    elif mode == "publish":
        publicar_en_instagram()
