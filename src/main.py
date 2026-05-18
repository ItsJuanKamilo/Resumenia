import os
import requests
import time
import sys
from google import genai
from PIL import Image, ImageDraw

# --- CONFIGURACIÓN ---
GITHUB_USER = "ItsJuanKamilo"
REPO_NAME = "Resumenia"
IMAGE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/public/post_dia.jpg"

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
IG_USER_ID = os.getenv("IG_ACCOUNT_ID")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN")

def generar_y_guardar():
    print("🤖 Consultando a Gemini 3 Flash Preview...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = ("Resume las 3 noticias de tecnología más importantes de hoy en Chile y el mundo. "
              "Formato: Una frase corta por noticia con emojis. Tono profesional.")
    
    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    texto = response.text
    print("Contenido generado por Gemini.")

    if not os.path.exists('public'): os.makedirs('public')
    img = Image.new('RGB', (1080, 1080), color=(18, 18, 18))
    d = ImageDraw.Draw(img)
    d.text((80, 100), "RESUMEN TECH CHILE", fill=(0, 255, 150))
    d.multiline_text((80, 250), texto, fill=(255, 255, 255), spacing=20)
    img.save("public/post_dia.jpg", quality=95)
    print("Imagen generada correctamente en public/post_dia.jpg")
    # Guardamos el resumen en un archivo temporal para el caption después
    with open("public/caption.txt", "w", encoding="utf-8") as f:
        f.write(texto)

def publicar_en_instagram():
    print(f"🚀 Intentando publicar imagen desde: {IMAGE_URL}")
    
    # Leemos el caption que guardamos antes
    with open("public/caption.txt", "r", encoding="utf-8") as f:
        resumen = f.read()

    url_base = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    payload = {
        'image_url': IMAGE_URL,
        'caption': f"Resumen Tech Santiago 🤖 #IA #Chile #Tech\n\n{resumen}",
        'access_token': IG_TOKEN
    }
    
    res = requests.post(url_base, data=payload)
    if res.status_code != 200:
        print("Error de Meta (Contenedor):", res.json())
        sys.exit(1)

    creation_id = res.json().get('id')
    time.sleep(10) # Pausa técnica de seguridad
    
    url_pub = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish"
    requests.post(url_pub, data={'creation_id': creation_id, 'access_token': IG_TOKEN})
    print("¡POST PUBLICADO EN INSTAGRAM!")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if mode == "generate":
        generar_y_guardar()
    elif mode == "publish":
        publicar_en_instagram()
    else:
        generar_y_guardar()
        # En local esto fallará por la URL de GitHub Pages, por eso usamos el modo separado en Actions
