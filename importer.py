# =================================================================================
# importer.py
# Implementa el patrón Factory Method para la importación de datos.
# =================================================================================

import pandas as pd
import os
from abc import ABC, abstractmethod
import logging


class Material:
    """Representa un material o componente importado."""

    def __init__(self, codigo, descripcion):
        self.codigo = codigo
        self.descripcion = descripcion


class IMaterialImporter(ABC):
    """
    Interfaz abstracta para los importadores de materiales.
    Define el contrato que todas las implementaciones deben seguir.
    """

    @abstractmethod
    def import_materials(self, file_path):
        """Lee un archivo y retorna una lista de objetos Material."""
        pass


class ExcelMaterialImporter(IMaterialImporter):
    """
    Importador concreto para archivos Excel (.xlsx).
    Utiliza la librería pandas para un manejo eficiente de los datos.
    """

    def import_materials(self, file_path):
        """
        Lee los materiales desde un archivo Excel.
        Se espera que el archivo contenga las columnas 'codigo' y 'descripcion'.
        """
        logging.info(f"Importando materiales desde el archivo Excel: {file_path}")
        materials = []
        try:
            df = pd.read_excel(file_path, engine='openpyxl')

            # Convertir los nombres de columnas a minúsculas para un manejo flexible
            df.columns = df.columns.str.lower()

            # Si no se encuentran las columnas, lanzar una excepción
            if 'codigo' not in df.columns or 'descripcion' not in df.columns:
                raise ValueError("El archivo Excel debe contener las columnas 'codigo' y 'descripcion'.")

            # Rellenar valores nulos para evitar errores
            df = df.fillna('')

            for index, row in df.iterrows():
                # Asegurarse de que el código no está vacío
                if row['codigo'].strip():
                    materials.append(Material(
                        codigo=str(row['codigo']).strip(),
                        descripcion=str(row['descripcion']).strip()
                    ))

            logging.info(f"Importados {len(materials)} materiales desde {file_path}.")
            return materials

        except FileNotFoundError:
            logging.error(f"El archivo no se encontró en la ruta: {file_path}")
            return None
        except ValueError as ve:
            logging.error(f"Error en el formato del archivo: {ve}")
            return None
        except Exception as e:
            logging.critical(f"Error inesperado al leer el archivo Excel: {e}", exc_info=True)
            return None


class MaterialImporterFactory:
    """
    Clase factoría que decide qué importador crear basado en la extensión del archivo.
    """

    def create_importer(self, file_extension):
        """
        Retorna una instancia del importador apropiado para la extensión dada.
        """
        extension = file_extension.lower()
        if extension == '.xlsx' or extension == '.xls':
            return ExcelMaterialImporter()
        # Puedes añadir más casos en el futuro, como:
        # elif extension == '.csv':
        #     return CsvMaterialImporter()
        else:
            raise ValueError(f"Formato de archivo '{extension}' no soportado.")