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
        "Resume las 3 noticias de tecnología más importantes de hoy en Chile y el mundo. "
        "Sé directo y profesional. Máximo 120 caracteres por noticia. "
        "IMPORTANTE: No uses números, ni viñetas, ni asteriscos. Solo el texto.\n"
        "AL FINAL añade una línea: 'KEYWORD:' y una palabra en inglés para la foto."
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
    print(f"📸 Buscando foto: {keyword}")
    url = f"https://api.pexels.com/v1/search?query={keyword}&per_page=1&orientation=landscape"
    headers = {"Authorization": PEXELS_KEY}
    try:
        res = requests.get(url, headers=headers).json()
        img_url = res['photos'][0]['src']['large2x']
        return Image.open(requests.get(img_url, stream=True).raw)
    except:
        return None

def crear_imagen(noticias, foto_pexels):
    print("🎨 Aplicando diseño final (Texto centrado y sin números)...")
    
    try:
        base = Image.open("src/template.png").convert("RGBA")
    except:
        print("❌ Error: No se encontró src/template.png")
        sys.exit(1)

    if foto_pexels:
        # Ajustamos para que cubra TODO el espacio blanco (1080x415 aprox)
        target_w, target_h = 1080, 415 
        
        # Redimensionar y recortar (Crop center)
        orig_w, orig_h = foto_pexels.size
        ratio = max(target_w/orig_w, target_h/orig_h)
        new_size = (int(orig_w*ratio), int(orig_h*ratio))
        foto_res = foto_pexels.resize(new_size, Image.Resampling.LANCZOS)
        
        left = (new_size[0] - target_w)/2
        top = (new_size[1] - target_h)/2
        foto_final = foto_res.crop((left, top, left + target_w, top + target_h))
        
        # Pegar en el tope exacto
        base.paste(foto_final, (0, 0))

    d = ImageDraw.Draw(base)
    font_path = "src/Roboto.ttf"
    if not os.path.exists(font_path): font_path = "src/roboto.ttf"
    try:
        font = ImageFont.truetype(font_path, 42)
    except:
        font = ImageFont.load_default()

    # --- POSICIONAMIENTO Y CENTRADO ---
    y_start = 620 # Bajamos más para no tocar "NOTICIAS"
    ancho_max = 45 # Caracteres por línea

    for noticia in noticias:
        # Quitamos números al inicio por si acaso (ej: "1. Noticia" -> "Noticia")
        noticia = noticia.lstrip('0123456789. ')
        
        if not noticia.strip(): continue
        
        lines = textwrap.wrap(noticia, width=ancho_max)
        
        # Dibujar cada línea centrada
        for line in lines:
            bbox = d.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            # 540 es la mitad de 1080
            d.text((540 - w/2, y_start), line, font=font, fill=(255, 255, 255))
            y_start += 55
            
        y_start += 120 # Espacio entre noticias

    final = base.convert("RGB")
    if not os.path.exists('public'): os.makedirs('public')
    final.save("public/post_dia.jpg", "JPEG", quality=95)
    print("✅ Imagen generada con éxito.")

def publicar_en_instagram():
    print("🚀 Publicando...")
    if not os.path.exists("public/caption.txt"): return
    with open("public/caption.txt", "r", encoding="utf-8") as f:
        caption = f.read()

    url_base = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    payload = {
        'image_url': IMAGE_URL,
        'caption': f"Resumen Tech de hoy 🤖\n\n{caption}\n\n#Chile #IA #Resumenia",
        'access_token': IG_TOKEN
    }
    
    r = requests.post(url_base, data=payload)
    if r.status_code == 200:
        c_id = r.json().get('id')
        time.sleep(30)
        requests.post(f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish", 
                      data={'creation_id': c_id, 'access_token': IG_TOKEN})
        print("🎉 ¡PUBLICADO!")
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
