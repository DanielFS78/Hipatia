# -*- coding: utf-8 -*-
"""
A3RPExcelAdapter: Adaptador para importar estructuras BOM desde archivos Excel de A3RP.
=======================================================================================
Implementa el puerto `IBOMImporter` leyendo archivos `.xlsx` mediante `pandas`.
Reconstruye el árbol de lista de materiales (BOM) analizando los niveles de indentación
y las dependencias implícitas en el formato exportado por el ERP A3RP.
"""

import math
from typing import Dict, Optional, Any
import pandas as pd

from core.import_manager.ports import IBOMImporter
from core.import_manager.dto import BOMNodeDTO


class A3RPExcelAdapter(IBOMImporter):
    """
    Adaptador concreto para leer estructuras de producto desde archivos Excel (.xlsx).
    
    Analiza la estructura jerárquica exportada por A3RP, reconstruyendo el árbol
    BOM (Bill of Materials) basándose en la columna 'Nivel'.
    
    Atributos de columna esperados:
        Nivel: Profundidad (0=Raíz).
        Componente: Código único.
        Denominación: Descripción.
        Tipo: 'Compuesto' o 'Simple'.
        Cantidad: Unidades para el padre.
    """
    
    def parse_file(self, file_path: str, **kwargs: Any) -> BOMNodeDTO:
        """
        Lee el archivo Excel y devuelve el nodo raíz del árbol BOM.
        
        Args:
            file_path: Ruta absoluta al archivo .xlsx.
            **kwargs: Argumentos adicionales (por ejemplo, sheet_name).
            
        Returns:
            BOMNodeDTO: Estructura jerárquica con el nodo raíz y sus hijos anidados.
            
        Raises:
            ValueError: Si no se encuentra un nodo raíz (Nivel 0) o si el formato es inválido.
            FileNotFoundError: Si el archivo no existe.
        """
        sheet_name = kwargs.get('sheet_name', 0)
        
        try:
            # Leer el excel, asumiendo que la primera fila con datos es la cabecera real
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as e:
            raise IOError(f"Error al leer el archivo Excel '{file_path}': {e}")

        # Diccionario para rastrear el último nodo procesado por nivel
        # Esto permite asignar correctamente los hijos a sus padres en un recorrido secuencial
        ultimo_nodo_por_nivel: Dict[int, BOMNodeDTO] = {}
        raiz_bom: Optional[BOMNodeDTO] = None
        
        # Validar columnas mínimas requeridas. A3RP suele tener 'Nivel' y 'Componente'
        columnas_lower = [str(c).lower().strip() for c in df.columns]
        if 'nivel' not in columnas_lower or 'componente' not in columnas_lower:
            raise ValueError("El archivo no contiene las columnas obligatorias 'Nivel' y 'Componente'.")

        # Mapeo flexible de nombres de columnas
        col_map = {
            'nivel': next((c for c in df.columns if str(c).lower().strip() == 'nivel'), 'Nivel'),
            'componente': next((c for c in df.columns if str(c).lower().strip() == 'componente'), 'Componente'),
            'denominacion': next((c for c in df.columns if 'denominaci' in str(c).lower()), 'Denominación'),
            'tipo': next((c for c in df.columns if str(c).lower().strip() == 'tipo'), 'Tipo'),
            'cantidad': next((c for c in df.columns if str(c).lower().strip() == 'cantidad'), 'Cantidad'),
            'capitulo': next((c for c in df.columns if 'capitulo' in str(c).lower() or 'capítulo' in str(c).lower()), 'Capítulo')
        }

        # Procesar secuencialmente las filas
        # El DataFrame devuelto por to_dict records asegura que iteramos en orden de lectura
        for index, row in df.iterrows():
            # Limpiar valor de nivel
            raw_nivel = row.get(col_map['nivel'])
            
            # Ignorar filas vacías o donde el nivel no sea numérico
            if pd.isna(raw_nivel):
                continue
                
            try:
                nivel_actual = int(float(str(raw_nivel)))
            except ValueError:
                continue # Fila de metadatos o basura

            codigo = str(row.get(col_map['componente'], '')).strip()
            if not codigo or codigo.lower() == 'nan':
                continue # Sin código no es un componente válido
                
            denominacion = str(row.get(col_map['denominacion'], '')).strip()
            if denominacion.lower() == 'nan':
                 denominacion = ''
            
            tipo = str(row.get(col_map['tipo'], '')).strip().upper()
            es_compuesto = (tipo == 'COMPUESTO')
            
            # Extraer y normalizar cantidad
            raw_cant = row.get(col_map['cantidad'], 0.0)
            try:
                if pd.isna(raw_cant):
                    cantidad = 0.0
                elif isinstance(raw_cant, str):
                    cantidad = float(str(raw_cant).replace(',', '.'))
                else:
                    cantidad = float(raw_cant)
            except ValueError:
                cantidad = 0.0
                
            capitulo = str(row.get(col_map['capitulo'], '')).strip()
            if capitulo.lower() == 'nan':
                capitulo = ''

            # Crear el Data Transfer Object para este nodo
            nodo = BOMNodeDTO(
                nivel=nivel_actual,
                capitulo=capitulo,
                codigo_componente=codigo,
                denominacion=denominacion,
                es_subfabricacion=es_compuesto,
                cantidad=cantidad
            )

            # Actualizar el rastreador de padres
            ultimo_nodo_por_nivel[nivel_actual] = nodo

            if nivel_actual == 0:
                if raiz_bom is None:
                     raiz_bom = nodo # Seleccionamos el primer nivel 0 como raíz
            else:
                # El padre de un componente nivel N es el último componente visto en el nivel N-1
                padre = ultimo_nodo_por_nivel.get(nivel_actual - 1)
                if padre:
                    padre.hijos.append(nodo)
                # Si no hay padre registrado, es un nodo huérfano (posible exportación parcial)
                # Se descarta implícitamente del árbol principal, pero queda registrado en ultimo_nodo_por_nivel.

        if raiz_bom is None:
            raise ValueError("No se pudo extraer el producto raíz (Nivel 0) del archivo Excel.")

        return raiz_bom
