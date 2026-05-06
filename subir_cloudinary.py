import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

carpeta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img')

imagenes = [
    'ayuntamiento1.jpeg',
    'ayuntamiento2.jpeg',
    'ayuntamiento3.jpeg',
    'ayuntamiento4.jpeg',
    'ayunttamiento6.jpeg',
    'ayuntamiento7.jpeg',
]

for img in imagenes:
    ruta = os.path.join(carpeta, img)
    if not os.path.exists(ruta):
        print('NO ENCONTRADO: ' + ruta)
        continue
    nombre = img.split('.')[0]
    result = cloudinary.uploader.upload(
        ruta,
        public_id='slider/' + nombre,
        overwrite=True
    )
    print(img + ' -> ' + result['secure_url'])