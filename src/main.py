import os
import requests
from google import genai
from PIL import Image, ImageDraw
import time

# --- CONFIGURACIÓN ---
GITHUB_USER = "ItsJuanKamilo"
REPO_NAME = "Resumenia"
# Esta URL debe ser exacta para que Meta la encuentre
IMAGE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/public/post_dia.jpg"

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
IG_USER_ID = os.getenv("IG_ACCOUNT_ID")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN")

def generar_contenido():
    print("🤖 Consultando a Gemini 3 Flash Preview...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = (
        "Resume las 3 noticias de tecnología más importantes de hoy en Chile y el mundo. "
        "Formato: Una frase corta por noticia. Usa emojis. Tono profesional."
    )
    
    # CAMBIO AQUÍ: Agregamos el sufijo -preview
    response = client.models.generate_content(
        model="gemini-3-flash-preview", 
        contents=prompt
    )
    return response.text

def crear_imagen(texto):
    # Aseguramos que la carpeta public exista antes de guardar
    if not os.path.exists('public'): 
        os.makedirs('public')
        
    img = Image.new('RGB', (1080, 1080), color=(15, 15, 15))
    d = ImageDraw.Draw(img)
    
    # Un diseño ultra simple para el test
    d.text((100, 300), "RESUMEN IA CHILE", fill=(0, 255, 150))
    d.text((100, 450), texto, fill=(255, 255, 255))
    
    img.save("public/post_dia.jpg", quality=95)
    print("Imagen generada correctamente en public/post_dia.jpg")

def publicar_en_instagram(caption):
    # Paso 1: Crear contenedor
    print(f"Intentando publicar imagen desde: {IMAGE_URL}")
    url_base = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    payload = {
        'image_url': IMAGE_URL,
        'caption': caption,
        'access_token': IG_TOKEN
    }
    
    res = requests.post(url_base, data=payload)
    if res.status_code != 200:
        print("Error de Meta (Contenedor):", res.json())
        return

    creation_id = res.json().get('id')
    print(f"Contenedor creado con ID: {creation_id}. Esperando procesamiento...")
    
    # Esperamos un poco más (20 seg) para que Meta procese la imagen de GitHub Pages
    time.sleep(20)
    
    # Paso 2: Publicar
    url_pub = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish"
    res_pub = requests.post(url_pub, data={'creation_id': creation_id, 'access_token': IG_TOKEN})
    
    if res_pub.status_code == 200:
        print("¡POST PUBLICADO EN INSTAGRAM!")
    else:
        print("Error al publicar:", res_pub.json())

if __name__ == "__main__":
    try:
        print("Iniciando bot...")
        resumen = generar_contenido()
        print("Contenido generado por Gemini.")
        crear_imagen(resumen)
        
        # Solo publica si estamos en el entorno de GitHub
        if os.getenv("GITHUB_ACTIONS"):
            publicar_en_instagram(f"Resumen Tech Santiago 🤖 #IA #Chile #Tech\n\n{resumen}")
    except Exception as e:
        print(f"Error en la ejecución: {e}")
        # Forzamos el fallo del script para que GitHub Action nos avise
        exit(1)
