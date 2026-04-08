
"""
Lógica o utilidades del núcleo (`quote_service`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

import json
import logging
import random
import os
import wikipedia
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Any

from core.dtos import QuoteDTO, AuthorInfoDTO
from core.utils.helpers import resource_path

# Mismo núcleo que `scripts/generate_quotes_db.py` (BACKUP_QUOTES) si falta el JSON en disco.
_FALLBACK_QUOTES: list[dict[str, str]] = [
    {"quote": "La vida es aquello que te va sucediendo mientras te empeñas en hacer otros planes.", "author": "John Lennon"},
    {"quote": "El único modo de hacer un gran trabajo es amar lo que haces.", "author": "Steve Jobs"},
    {"quote": "No cuentes los días, haz que los días cuenten.", "author": "Muhammad Ali"},
    {"quote": "La inteligencia es la habilidad de adaptarse al cambio.", "author": "Stephen Hawking"},
    {"quote": "La creatividad es la inteligencia divirtiéndose.", "author": "Albert Einstein"},
]


class QuoteService:
    """
    Servicio para mostrar frases célebres y enriquecerlas con datos de Wikipedia.
    """
    def __init__(self, quotes_json_path: str | None = None) -> None:
        self.logger = logging.getLogger("EvolucionTiemposApp")
        self.resource_path = quotes_json_path or resource_path("resources/quotes.json")
        self.quotes: List[QuoteDTO] = []
        self._load_quotes()
        
        # Configurar idioma de wikipedia una vez
        try:
            wikipedia.set_lang("es")
        except Exception:
            self.logger.warning("No se pudo configurar idioma español para Wikipedia.")

        # Caché simple en memoria para no repetir llamadas a Wikipedia en la misma sesión
        self.author_cache: Dict[str, AuthorInfoDTO] = {}

    def _load_quotes(self) -> None:
        """Carga las frases del JSON local (`resources/quotes.json`); si no existe, usa frases integradas."""
        try:
            if not os.path.exists(self.resource_path):
                self.logger.info(
                    "Archivo de frases no encontrado en %s; usando frases integradas. "
                    "Para ampliar la colección, ejecute: python3 scripts/generate_quotes_db.py",
                    self.resource_path,
                )
                self.quotes = [
                    QuoteDTO(quote=q["quote"], author=q["author"]) for q in _FALLBACK_QUOTES
                ]
                return

            with open(self.resource_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("El JSON de frases debe ser una lista de objetos {quote, author}.")
            self.quotes = [QuoteDTO(quote=q["quote"], author=q["author"]) for q in data]

            self.logger.info("Cargadas %s frases célebres desde %s.", len(self.quotes), self.resource_path)
        except Exception as e:
            self.logger.error("Error cargando frases: %s", e)
            self.quotes = [
                QuoteDTO(quote=q["quote"], author=q["author"]) for q in _FALLBACK_QUOTES
            ]
            self.logger.info("Se usarán %s frases integradas como respaldo.", len(self.quotes))

    def get_random_quote(self) -> QuoteDTO:
        """
        Devuelve una frase aleatoria.
        
        Returns:
            Instancia de QuoteDTO con la frase y el autor.
        """
        if not self.quotes:
            return QuoteDTO(
                quote="La única forma de hacer un gran trabajo es amar lo que haces.",
                author="Steve Jobs"
            )
        return random.choice(self.quotes)

    def get_author_info(self, author_name: str) -> Optional[AuthorInfoDTO]:
        """
        Busca información del autor en Wikipedia (Bio + Imagen).
        
        Args:
            author_name: Nombre del autor a buscar.
            
        Returns:
            AuthorInfoDTO con el resumen e imagen, o None si no se encuentra.
        """
        # 1. Verificar caché
        if author_name in self.author_cache:
            return self.author_cache[author_name]

        # 2. Buscar en Wikipedia
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
            image_url: Optional[str] = None
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

            info = AuthorInfoDTO(
                summary=summary,
                image_url=image_url
            )
            
            # Guardar en caché
            self.author_cache[author_name] = info
            return info

        except Exception as e:
            self.logger.warning(f"Error obteniendo info de Wikipedia para {author_name}: {e}")
            return None
