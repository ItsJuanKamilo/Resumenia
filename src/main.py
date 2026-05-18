import os
import requests
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
IG_USER_ID = os.getenv("IG_ACCOUNT_ID")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN")

def generar_contenido():
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    # Aquí es donde le pasas la noticia o el tema
    prompt = "Escribe un resumen de 3 puntos clave sobre el clima en Santiago hoy para un post de Instagram. Sé breve y usa emojis."
    
    response = model.generate_content(prompt)
    return response.text

def crear_imagen(texto):
    # Crea una imagen base o usa background.jpg
    img = Image.new('RGB', (1080, 1080), color=(20, 20, 20))
    d = ImageDraw.Draw(img)
    
    # Nota: En GitHub Actions necesitarás cargar una fuente .ttf
    # Por ahora usamos la default para testear
    d.text((100, 400), texto, fill=(255, 255, 255))
    
    os.makedirs("public", exist_ok=True)
    img.save("public/post_dia.jpg")
    print("Imagen guardada en public/post_dia.jpg")

def publicar_instagram(image_url, caption):
    # Paso 1: Crear contenedor
    url_container = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': IG_TOKEN
    }
    r = requests.post(url_container, data=payload)
    creation_id = r.json().get('id')
    
    # Paso 2: Publicar
    if creation_id:
        url_publish = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish"
        requests.post(url_publish, data={'creation_id': creation_id, 'access_token': IG_TOKEN})
        print("¡Post publicado con éxito!")

# Flujo principal para el test
if __name__ == "__main__":
    # 1. IA genera texto
    resumen = generar_contenido()
    # 2. Creamos la imagen física
    crear_imagen(resumen)
    # 3. La URL será: https://tu-usuario.github.io/tu-repo/post_dia.jpg
    # (Esto lo activaremos en GitHub Pages)
