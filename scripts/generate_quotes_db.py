
import json
import os
import requests
import logging
import random

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_FILE = "resources/quotes.json"

# Fuentes de frases en JSON (Raw URLs) - EN ESPAÑOL
SOURCES = [
    {
        "url": "https://gist.githubusercontent.com/amr89-dev/3e3af34adb75ad2b2d6d4fe0a4dc2e61/raw/quotes_es.json",
        "key_quote": "quote",
        "key_author": "author"
    }
]

# Frases de respaldo por si fallan las descargas (Seed data)
BACKUP_QUOTES = [
    {"quote": "La vida es aquello que te va sucediendo mientras te empeñas en hacer otros planes.", "author": "John Lennon"},
    {"quote": "El único modo de hacer un gran trabajo es amar lo que haces.", "author": "Steve Jobs"},
    {"quote": "No cuentes los días, haz que los días cuenten.", "author": "Muhammad Ali"},
    {"quote": "La inteligencia es la habilidad de adaptarse al cambio.", "author": "Stephen Hawking"},
    {"quote": "La creatividad es la inteligencia divirtiéndose.", "author": "Albert Einstein"}
]

def fetch_quotes():
    """
    Descarga frases de múltiples fuentes JSON.
    """
    all_quotes = []
    
    for source in SOURCES:
        try:
            logger.info(f"Descargando de: {source['url']}...")
            response = requests.get(source['url'], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                count = 0
                for item in data:
                    q = item.get(source['key_quote'])
                    a = item.get(source['key_author'])
                    
                    if q and a:
                        all_quotes.append({"quote": q, "author": a})
                        count += 1
                logger.info(f"Importadas {count} frases.")
            else:
                logger.warning(f"Error {response.status_code} descargando {source['url']}")
                
        except Exception as e:
            logger.error(f"Error procesando {source['url']}: {e}")

    return all_quotes

def generate_database():
    """
    Función principal para generar la base de datos.
    """
    logger.info("Iniciando generación de base de datos de frases...")
    
    quotes = fetch_quotes()
    
    if not quotes:
        logger.warning("No se pudieron descargar frases. Usando backup local.")
        quotes = BACKUP_QUOTES
    else:
        # Añadir backup también para enriquecer
        quotes.extend(BACKUP_QUOTES)

    # Eliminar duplicados básicos
    unique_quotes = {q['quote']: q for q in quotes}.values()
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
