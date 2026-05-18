import os
import requests
from google import genai
from PIL import Image, ImageDraw
import time

# --- CONFIGURACIÓN ---
GITHUB_USER = "ItsJuanKamilo"
REPO_NAME = "Resumenia"
IMAGE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/public/post_dia.jpg"

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
IG_USER_ID = os.getenv("IG_ACCOUNT_ID")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN")

def generar_contenido():
    # Usando el nuevo cliente oficial
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = "Resume las 3 noticias de tecnología más importantes de hoy en Santiago de Chile. Formato: Una frase corta por noticia con emojis."
    
    response = client.models.generate_content(
        model="gemini-1.5-flash", 
        contents=prompt
    )
    return response.text

def crear_imagen(texto):
    img = Image.new('RGB', (1080, 1080), color=(15, 15, 15))
    d = ImageDraw.Draw(img)
    
    # Texto básico para el test
    d.text((100, 300), "RESUMEN IA CHILE", fill=(0, 255, 150))
    d.text((100, 450), texto, fill=(255, 255, 255))
    
    if not os.path.exists('public'): os.makedirs('public')
    img.save("public/post_dia.jpg", quality=95)

def publicar_en_instagram(caption):
    url_base = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    payload = {
        'image_url': IMAGE_URL,
        'caption': caption,
        'access_token': IG_TOKEN
    }
    
    res = requests.post(url_base, data=payload)
    if res.status_code != 200:
        print("Error Meta:", res.json())
        return

    creation_id = res.json().get('id')
    time.sleep(15) # Damos tiempo a Meta para procesar
    
    url_pub = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish"
    requests.post(url_pub, data={'creation_id': creation_id, 'access_token': IG_TOKEN})
    print("¡Post publicado con éxito!")

if __name__ == "__main__":
    try:
        resumen = generar_contenido()
        crear_imagen(resumen)
        if os.getenv("GITHUB_ACTIONS"):
            publicar_en_instagram(f"Resumen diario 🤖 #Chile #IA\n\n{resumen}")
    except Exception as e:
        print(f"Error en la ejecución: {e}")
