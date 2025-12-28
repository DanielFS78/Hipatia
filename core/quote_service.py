
import json
import logging
import random
import os
import wikipedia
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class QuoteService:
    """
    Servicio para mostrar frases célebres y enriquecerlas con datos de Wikipedia.
    """
    def __init__(self, resource_path="resources/quotes.json"):
        self.logger = logging.getLogger("EvolucionTiemposApp")
        self.resource_path = resource_path
        self.quotes = []
        self._load_quotes()
        
        # Configurar idioma de wikipedia una vez
        try:
            wikipedia.set_lang("es")
        except:
            self.logger.warning("No se pudo configurar idioma español para Wikipedia.")

        # Caché simple en memoria para no repetir llamadas a Wikipedia en la misma sesión
        self.author_cache = {}

    def _load_quotes(self):
        """Carga las frases del JSON local."""
        try:
            if not os.path.exists(self.resource_path):
                self.logger.error(f"Archivo de frases no encontrado: {self.resource_path}")
                return

            with open(self.resource_path, 'r', encoding='utf-8') as f:
                self.quotes = json.load(f)
            
            self.logger.info(f"Cargadas {len(self.quotes)} frases célebres.")
        except Exception as e:
            self.logger.error(f"Error cargando frases: {e}")

    def get_random_quote(self):
        """Devuelve un diccionario con 'quote' y 'author'."""
        if not self.quotes:
            return {
                "quote": "La única forma de hacer un gran trabajo es amar lo que haces.",
                "author": "Steve Jobs"
            }
        return random.choice(self.quotes)

    def get_author_info(self, author_name):
        """
        Busca información del autor en Wikipedia (Bio + Imagen).
        Devuelve un diccionario o None si falla.
        """
        # 1. Verificar caché
        if author_name in self.author_cache:
            return self.author_cache[author_name]

        # 2. Buscar en Wikipedia (en un hilo separado idealmente, pero aquí sincrónico por simplicidad inicial
        #    aunque se llamará desde un QThread en la UI para no bloquear)
        try:
            # Buscar página
            results = wikipedia.search(author_name)
            if not results:
                return None
            
            # Tomar el primer resultado
            page = wikipedia.page(results[0], auto_suggest=False)
            
            # Obtener resumen (primera frase/párrafo)
            summary = page.summary.split('.')[0] + "."
            if len(summary) > 200:
                summary = summary[:197] + "..."

            # Obtener imagen (buscar la primera imagen que parezca un retrato)
            image_url = None
            if page.images:
                # Filtrar iconos, svgs, y buscar preferentemente .jpg o .png
                valid_images = [
                    img for img in page.images 
                    if not img.endswith('.svg') 
                    and 'icon' not in img.lower()
                    and 'logo' not in img.lower()
                    and 'flag' not in img.lower()
                    and 'map' not in img.lower()
                    and (img.lower().endswith('.jpg') or img.lower().endswith('.jpeg') or img.lower().endswith('.png'))
                ]
                if valid_images:
                    # Preferir imágenes que contengan el nombre del autor o palabras clave
                    name_part = author_name.split()[-1].lower()  # Apellido
                    portrait_candidates = [img for img in valid_images if name_part in img.lower() or 'portrait' in img.lower()]
                    image_url = portrait_candidates[0] if portrait_candidates else valid_images[0]

            info = {
                "summary": summary,
                "image_url": image_url
            }
            
            # Guardar en caché
            self.author_cache[author_name] = info
            return info

        except Exception as e:
            self.logger.warning(f"Error obteniendo info de Wikipedia para {author_name}: {e}")
            return None
