# -*- coding: utf-8 -*-
"""
BOMImportService: Servicio de dominio para importar estructuras supervisadas.
=============================================================================
Toma el árbol `BOMNodeDTO` (ya supervisado por el usuario en la UI) y
se coordina con `ProductService` para inyectar estos nodos en la base de datos,
creando o actualizando los productos según sea necesario.
"""

import logging
from typing import Set, Any, Dict
from core.import_manager.dto import BOMNodeDTO

class BOMImportService:
    """
    Servicio encargado de importar un árbol BOM a la base de datos de Hipatia.
    """
    
    def __init__(self, product_service: Any) -> None:
        """
        Inicializa el servicio de importación.
        
        Args:
            product_service: Interfaz o instancia capaz de crear/actualizar productos
                             y manejar subfabricaciones (por e.g., ProductService o ProductManager).
        """
        self.logger = logging.getLogger("EvolucionTiemposApp")
        self.product_service = product_service
        
    def import_bom_tree(self, root_node: BOMNodeDTO) -> Dict[str, int]:
        """
        Recorre el árbol BOM recursivamente y procesa la inserción o actualización
        de productos y sus relaciones de subfabricación.
        
        Sólo procesa subfabricaciones si `nodo.es_subfabricacion` es True.
        
        Args:
            root_node: El nodo raíz supervisado.
            
        Returns:
            Dict con estadísticas de importación (ej. {'creados': X, 'actualizados': Y}).
        """
        stats = {'creados': 0, 'actualizados': 0, 'errores': 0}
        procesados: Set[str] = set()
        
        self._process_node(root_node, stats, procesados)
        self.logger.info(f"Importación BOM completada. Estadísticas: {stats}")
        
        return stats

    def _process_node(self, node: BOMNodeDTO, stats: Dict[str, int], procesados: Set[str]) -> None:
        """
        Proceso recursivo interno para manejar cada nodo y sus hijos.
        
        Asegura la creación del producto, procesa sus dependencias (hijos) y 
        evita ciclos infinitos mediante el conjunto 'procesados'.

        Args:
            node: Nodo actual a procesar.
            stats: Diccionario de estadísticas para acumular resultados.
            procesados: Conjunto de códigos ya visitados para evitar ciclos.
        """
        if not node.codigo_componente:
             return
             
        if node.codigo_componente in procesados:
            self.logger.warning(f"Ciclo detectado o componente repetido en árbol: {node.codigo_componente}")
            return
            
        procesados.add(node.codigo_componente)
        
        # 1. Asegurar que el producto existe en Base de Datos
        self._ensure_product_exists(node, stats)
        
        # 2. Preparar lista de subfabricaciones (hijos marcados para importar)
        sub_fabricaciones_data = []
        
        for hijo in node.hijos:
            # Recursivamente procesar a los hijos primero
            self._process_node(hijo, stats, procesados)
            
            # Si consideramos a este hijo como subfabricación (según la UI)
            if hijo.es_subfabricacion:
                sub_fabricaciones_data.append({
                    "id": hijo.codigo_componente,
                    "descripcion": hijo.denominacion,
                    "tiempo": 0.0, 
                    "tipo_trabajador": "1", 
                    "cantidad": hijo.cantidad
                })
        
        # 3. Vincular subfabricaciones al padre si corresponde
        if sub_fabricaciones_data and node.es_subfabricacion:
            self._update_product_dependencies(node, sub_fabricaciones_data, stats)


    def _ensure_product_exists(self, node: BOMNodeDTO, stats: Dict[str, int]) -> None:
        """Verifica si el producto existe. Si no, lo crea de forma básica."""
        codigo = node.codigo_componente
        try:
             existing = self.product_service.get_product_by_code(codigo)
             
             if not existing:
                 new_data = {
                     "codigo": codigo,
                     "descripcion": node.denominacion or f"Producto IMPORTADO {codigo}",
                     "departamento": "Montaje" if node.es_subfabricacion else "Mecánica", 
                     "donde": "Importado Automáticamente",
                     "tiene_subfabricaciones": 1 if node.es_subfabricacion and node.hijos else 0,
                     "tiempo_optimo": 0.01, # 0.01 para evitar validación INVALID_TIME si el mínimo es > 0
                     "tipo_trabajador": "1"
                 }
                 result = self.product_service.add_product(new_data, [])
                 if result == "SUCCESS":
                     stats['creados'] += 1
                 else:
                     self.logger.error(f"Fallo creando componente {codigo}: {result}")
                     stats['errores'] += 1
             else:
                 stats['actualizados'] += 1
                 
        except Exception as e:
             self.logger.error(f"Excepción verificando producto {codigo}: {e}")
             stats['errores'] += 1

    def _update_product_dependencies(self, node: BOMNodeDTO, sub_fabricaciones: list[Dict[str, Any]], stats: Dict[str, int]) -> None:
        """Actualiza el registro del producto padre con la nueva lista de hijos."""
        try:
            details = self.product_service.get_product_details(node.codigo_componente)
            if not details or not details.producto:
                return
                
            prod_data = {
                "codigo": details.producto.codigo,
                "descripcion": node.denominacion or details.producto.descripcion, 
                "departamento": details.producto.departamento,
                "donde": details.producto.donde,
                "tiene_subfabricaciones": 1,
                "tiempo_optimo": details.producto.tiempo_optimo,
                "tipo_trabajador": details.producto.tipo_trabajador
            }
            
            if not self.product_service.update_product(node.codigo_componente, prod_data, sub_fabricaciones):
                 stats['errores'] += 1
        except Exception as e:
            self.logger.error(f"Error actualizando dependencias de {node.codigo_componente}: {e}")
            stats['errores'] += 1
