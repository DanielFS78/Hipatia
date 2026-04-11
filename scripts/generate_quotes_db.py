
"""
Nombre del Módulo: scripts.generate_quotes_db

Descripción: Script ejecutable (`generate_quotes_db`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import json
import os
import logging
import random
import urllib.request


"""Genera una base de datos local de frases (quotes) en `resources/quotes.json`.

El script intenta descargar quotes desde una(s) URL(s) remotas y, si falla,
recupera un backup local embebido.
"""

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_FILE = "resources/quotes.json"

# Fuentes de frases en JSON (Raw URLs) - EN ESPAÑOL
SOURCES: list[dict[str, str]] = [
    {
        "url": "https://gist.githubusercontent.com/amr89-dev/3e3af34adb75ad2b2d6d4fe0a4dc2e61/raw/quotes_es.json",
        "key_quote": "quote",
        "key_author": "author"
    }
]

# Frases de respaldo por si fallan las descargas (Seed data)
BACKUP_QUOTES: list[dict[str, str]] = [
    {"quote": "La vida es aquello que te va sucediendo mientras te empeñas en hacer otros planes.", "author": "John Lennon"},
    {"quote": "El único modo de hacer un gran trabajo es amar lo que haces.", "author": "Steve Jobs"},
    {"quote": "No cuentes los días, haz que los días cuenten.", "author": "Muhammad Ali"},
    {"quote": "La inteligencia es la habilidad de adaptarse al cambio.", "author": "Stephen Hawking"},
    {"quote": "La creatividad es la inteligencia divirtiéndose.", "author": "Albert Einstein"}
]

def fetch_quotes() -> list[dict[str, str]]:
    """Descarga frases de múltiples fuentes JSON."""
    all_quotes: list[dict[str, str]] = []
    
    for source in SOURCES:
        url: str = source["url"]
        key_quote: str = source["key_quote"]
        key_author: str = source["key_author"]
        try:
            logger.info(f"Descargando de: {url}...")
            with urllib.request.urlopen(url, timeout=10) as response:
                raw = response.read()

            parsed = json.loads(raw.decode("utf-8"))
            if isinstance(parsed, list):
                count = 0
                for item in parsed:
                    if not isinstance(item, dict):
                        continue
                    q = item.get(key_quote)
                    a = item.get(key_author)
                    if isinstance(q, str) and isinstance(a, str):
                        all_quotes.append({"quote": q, "author": a})
                        count += 1
                logger.info(f"Importadas {count} frases.")
            else:
                logger.warning(f"Respuesta inesperada descargando {url}: no es una lista JSON.")
                
        except Exception as e:
            logger.error(f"Error procesando {url}: {e}")

    return all_quotes

def generate_database() -> None:
    """Genera el fichero JSON final con las frases."""
    logger.info("Iniciando generación de base de datos de frases...")
    
    quotes = fetch_quotes()
    
    if not quotes:
        logger.warning("No se pudieron descargar frases. Usando backup local.")
        quotes = BACKUP_QUOTES
    else:
        # Añadir backup también para enriquecer
        quotes.extend(BACKUP_QUOTES)

    # Eliminar duplicados básicos
    unique_quotes = {q["quote"]: q for q in quotes}.values()
    final_list = list(unique_quotes)
    
    # Mezclar
    random.shuffle(final_list)
    
    # Asegurar directorio
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Guardar
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
        
    logger.info(f"==========================================")
    logger.info(f"Base de datos generada exitosamente.")
    logger.info(f"Total de frases: {len(final_list)}")
    logger.info(f"Archivo guardado en: {OUTPUT_FILE}")
    logger.info(f"==========================================")

if __name__ == "__main__":
    generate_database()
