# -*- coding: utf-8 -*-
"""
Nombre del Módulo: a3rp_csv_adapter
Descripción: Lee exportaciones CSV de A3RP (con cabecera Nivel/Componente) y arma el mismo
             árbol ``BOMNodeDTO`` que el adaptador Excel, para entornos sin .xlsx.
"""

import csv
from typing import Dict, Optional
from core.import_manager.ports import IBOMImporter
from core.import_manager.dto import BOMNodeDTO

class A3RPCSVAdapter(IBOMImporter):
    def parse_file(self, file_path: str, encoding: str = 'latin1', delimiter: str = ';') -> BOMNodeDTO:
        # Puntero para saber quién es el padre actual de cada nivel
        ultimo_nodo_por_nivel: Dict[int, BOMNodeDTO] = {}
        raiz_bom: Optional[BOMNodeDTO] = None

        with open(file_path, mode='r', encoding=encoding) as f:
            # Sencilla limpieza inicial: buscar la primera fila que parezca el cabecero
            # A3RP a veces mete filas de metadatos arriba.
            lines = f.readlines()
            header_index = -1
            for i, line in enumerate(lines):
                if 'Nivel' in line and 'Componente' in line:
                    header_index = i
                    break
            
            if header_index == -1:
                raise ValueError("No se pudo encontrar la fila de cabecera (Nivel, Componente) en el CSV.")

            # Reiniciar lectura desde el header
            import io
            reader = csv.DictReader(io.StringIO("".join(lines[header_index:])), delimiter=delimiter)
            
            for row in reader:
                # Robustez: A3RP a veces mete filas de metadatos o vacías arriba/abajo
                # Buscamos filas balanceadas con 'Nivel' (entero)
                nivel_raw = row.get('Nivel')
                if not nivel_raw or not nivel_raw.strip().isdigit():
                    continue
                    
                nivel_actual: int = int(nivel_raw.strip())
                tipo_raw = (row.get('Tipo') or '').strip().upper()
                es_compuesto: bool = tipo_raw == 'COMPUESTO'
                
                # Gestión flexible de cantidades (A3RP usa decimales con coma en España)
                cant_raw = (row.get('Cantidad') or '0.0').strip().replace(',', '.')
                try:
                    cantidad = float(cant_raw)
                except ValueError:
                    cantidad = 0.0
                
                # Crear el nodo actual
                nodo = BOMNodeDTO(
                    nivel=nivel_actual,
                    capitulo=(row.get('Capítulo') or '').strip(),
                    codigo_componente=(row.get('Componente') or '').strip(),
                    denominacion=(row.get('Denominación') or '').strip(),
                    es_subfabricacion=es_compuesto,
                    cantidad=cantidad
                )

                # Registrar este nodo en el diccionario de punteros
                ultimo_nodo_por_nivel[nivel_actual] = nodo

                if nivel_actual == 0:
                    # Es el producto final maestro (ej. Teléfono Completo)
                    raiz_bom = nodo
                else:
                    # Si soy nivel 3, mi padre directo es el último nivel 2 que se leyó
                    padre = ultimo_nodo_por_nivel.get(nivel_actual - 1)
                    if padre:
                        padre.hijos.append(nodo)
                    # Si no hay padre, es un huérfano (posible exportación parcial o error en CSV)
                        
        if not raiz_bom:
            raise ValueError("No se pudo encontrar la raíz del árbol BOM (Nivel 0) en el archivo.")
            
        return raiz_bom
