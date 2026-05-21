import os
import requests
import time
import sys
import textwrap
from google import genai
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import random
from google.genai import types
import datetime

# --- CONFIGURACIÓN ---
GITHUB_USER = "ItsJuanKamilo"
REPO_NAME = "Resumenia"
IMAGE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/public/post_dia.jpg"

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY") 
IG_USER_ID = os.getenv("IG_ACCOUNT_ID")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN")

def obtener_datos():
    print("🌐 Consultando a Gemini con Google Search (Chile + Mundo)...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    fecha_actual = datetime.datetime.now().strftime('%d de %B de %Y')
    
    # 1. System Instruction: Aquí van las reglas de comportamiento y formato
    instrucciones_sistema = (
        "Eres un editor senior de tecnología. Tu objetivo es redactar un resumen "
        "basado ESTRICTAMENTE en los resultados de búsqueda de hoy.\n"
        "REGLAS DE ORO:\n"
        "- No inventes noticias ni mezcles conceptos antiguos.\n"
        "- Máximo 110 caracteres por noticia.\n"
        "- Sin números, ni guiones, ni asteriscos.\n"
        "- Solo texto plano, una noticia por línea.\n"
        "- MANTÉN EL ENFOQUE: Inteligencia Artificial, hardware o lanzamientos tech en Chile y el mundo.\n"
        "- AL FINAL añade una línea exacta: 'KEYWORD:' seguida de una palabra clave en inglés para buscar una foto."
    )
    
    # 2. Configuración: Activación de búsqueda simplificada y temperatura baja
    config_ia = types.GenerateContentConfig(
        system_instruction=instrucciones_sistema,
        tools=[{"google_search": {}}], # Sintaxis más estable para activar la búsqueda
        temperature=0.2 # Fundamental para que no invente noticias
    )

    # 3. El Prompt: Una orden de búsqueda directa y natural
    prompt = (
        f"Hoy es {fecha_actual}. Busca en Google las 3 noticias de tecnología "
        "e Inteligencia Artificial más impactantes publicadas en las últimas 24 horas "
        "en Chile y a nivel mundial. Devuélveme el resumen siguiendo tus instrucciones de formato."
    )
    
    # 4. Ejecución (Usando un modelo optimizado para búsqueda)
    response = client.models.generate_content(
        model="gemini-2.5-flash", # Asegúrate de usar un modelo estable reciente
        contents=prompt,
        config=config_ia
    )
    
    raw = response.text.replace("**", "").replace("*", "").strip()
    
    if "KEYWORD:" in raw:
        resumen, kw = raw.split("KEYWORD:")
        lineas = [l.strip() for l in resumen.strip().split('\n') if len(l.strip()) > 10]
        return lineas[:3], kw.strip()
    
    return raw.split('\n')[:3], "artificial intelligence"

def descargar_foto(keyword):
    # ELEGIMOS UNA PÁGINA AL AZAR (del 1 al 5)
    pagina_aleatoria = random.randint(1, 5)
    print(f"📸 Buscando '{keyword}' en la página {pagina_aleatoria} de Pexels...")
    
    # Pedimos 80 fotos (el máximo) de esa página aleatoria
    url = f"https://api.pexels.com/v1/search?query={keyword}&per_page=80&page={pagina_aleatoria}&orientation=landscape"
    headers = {"Authorization": PEXELS_KEY}
    
    try:
        res = requests.get(url, headers=headers).json()
        if not res.get('photos'):
            # Si no hay fotos en esa página, reintentamos en la página 1
            res = requests.get(url.replace(f"page={pagina_aleatoria}", "page=1"), headers=headers).json()
            if not res.get('photos'): return None
        
        # Elegimos 1 entre las 80 disponibles
        foto_final = random.choice(res['photos'])
        print(f"✅ Foto seleccionada de un pool de {len(res['photos'])} imágenes.")
        
        img_url = foto_final['src']['large2x']
        return Image.open(requests.get(img_url, stream=True).raw)
    except Exception as e:
        print(f"⚠️ Error de variedad: {e}")
        return None

def crear_imagen(noticias, foto_pexels):
    print("🎨 Ajustando diseño: Imagen extendida y texto reposicionado...")
    
    try:
        base = Image.open("src/template.png").convert("RGBA")
    except:
        print("❌ Error: No se encontró src/template.png")
        sys.exit(1)

    if foto_pexels:
        # Aumentamos a 480 para asegurar que la foto baje y tape el blanco totalmente
        target_w, target_h = 1080, 480 
        
        orig_w, orig_h = foto_pexels.size
        ratio = max(target_w/orig_w, target_h/orig_h)
        new_size = (int(orig_w*ratio), int(orig_h*ratio))
        foto_res = foto_pexels.resize(new_size, Image.Resampling.LANCZOS)
        
        left = (new_size[0] - target_w)/2
        top = (new_size[1] - target_h)/2
        foto_final = foto_res.crop((left, top, left + target_w, top + target_h))
        
        # Pegar en el tope (0,0)
        base.paste(foto_final, (0, 0))

    d = ImageDraw.Draw(base)
    font_path = "src/Roboto.ttf"
    if not os.path.exists(font_path): font_path = "src/roboto.ttf"
    try:
        # Reducimos un pelín la fuente a 38 para más elegancia
        font = ImageFont.truetype(font_path, 38)
    except:
        font = ImageFont.load_default()

    # --- POSICIONAMIENTO CORREGIDO ---
    y_actual = 660 # Bajamos el inicio para no tocar "NOTICIAS"
    ancho_max = 44 # Un poco más de ancho por línea

    for noticia in noticias:
        # Limpieza de basura al inicio
        noticia = noticia.lstrip('0123456789. -')
        if not noticia.strip(): continue
        
        lines = textwrap.wrap(noticia, width=ancho_max)
        
        for line in lines:
            bbox = d.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            # Centrado horizontal
            d.text((540 - w/2, y_actual), line, font=font, fill=(245, 245, 245))
            y_actual += 45 # Espacio entre líneas (Compacto)
            
        y_actual += 40 # Espacio entre noticias (Compacto)

    # 3. Guardar como RGB
    final = base.convert("RGB")
    if not os.path.exists('public'): os.makedirs('public')
    final.save("public/post_dia.jpg", "JPEG", quality=98)
    print("✅ Imagen generada con proporciones corregidas.")

def publicar_en_instagram():
    print("🚀 Publicando...")
    if not os.path.exists("public/caption.txt"): return
    with open("public/caption.txt", "r", encoding="utf-8") as f:
        caption = f.read()

    url_base = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    payload = {
        'image_url': IMAGE_URL,
        'caption': f"Resumen Tech de hoy 🤖\n\n{caption}\n\n#Chile #IA #Resumenia #Tech",
        'access_token': IG_TOKEN
    }
    
    r = requests.post(url_base, data=payload)
    if r.status_code == 200:
        c_id = r.json().get('id')
        time.sleep(30)
        requests.post(f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish", 
                      data={'creation_id': c_id, 'access_token': IG_TOKEN})
        print("🎉 ¡POST PUBLICADO!")
    else:
        print(f"❌ Error Meta: {r.json()}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "generate"
    if mode == "generate":
        noticias, kw = obtener_datos()
        foto = descargar_foto(kw)
        crear_imagen(noticias, foto)
        with open("public/caption.txt", "w", encoding="utf-8") as f:
            f.write("\n\n".join(noticias))
    elif mode == "publish":
        publicar_en_instagram()
