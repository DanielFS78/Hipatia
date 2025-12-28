# repositories/product_repository.py
"""
Repositorio para la gestión de productos.
Mantiene compatibilidad exacta con los métodos existentes en database_manager.py
"""

from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy import or_
from sqlalchemy.orm import joinedload # <-- AÑADE ESTA LÍNEA
from sqlalchemy.exc import IntegrityError

from .base import BaseRepository
from ..models import Producto, Subfabricacion, ProcesoMecanico
from core.dtos import ProductDTO, SubfabricacionDTO, ProcesoMecanicoDTO, MaterialDTO

class ProductRepository(BaseRepository):
    """
    Repositorio para la gestión de productos.
    Replica exactamente la interfaz de los métodos de productos en database_manager.py
    """

    def _get_default_error_value(self):
        """Retorna lista vacía por defecto para consultas, False para operaciones."""
        return []

    def get_all_products(self) -> List[ProductDTO]:
        """
        Obtiene la lista completa de todos los productos.
        Mantiene compatibilidad con: database_manager.get_all_products()

        Returns:
            Lista de objetos ProductDTO
        """

        def _operation(session):
            productos = session.query(Producto).order_by(Producto.codigo).all()
            return [
                ProductDTO(
                    codigo=p.codigo,
                    descripcion=p.descripcion,
                    departamento=p.departamento,
                    tipo_trabajador=p.tipo_trabajador,
                    donde=p.donde or "",
                    tiene_subfabricaciones=p.tiene_subfabricaciones,
                    tiempo_optimo=p.tiempo_optimo or 0.0
                ) for p in productos
            ]

        return self.safe_execute(_operation) or []

    def search_products(self, query: str) -> List[ProductDTO]:
        """
        Busca productos por código o descripción.
        Mantiene compatibilidad con: database_manager.search_products()

        Args:
            query: Término de búsqueda

        Returns:
            Lista de objetos ProductDTO
        """
        if not query:
            return self.get_all_products()

        if len(query) < 2:
            return []

        def _operation(session):
            productos = session.query(Producto).filter(
                or_(
                    Producto.codigo.like(f"%{query}%"),
                    Producto.descripcion.like(f"%{query}%")
                )
            ).all()
            return [
                ProductDTO(
                    codigo=p.codigo,
                    descripcion=p.descripcion,
                    departamento=p.departamento,
                    tipo_trabajador=p.tipo_trabajador,
                    donde=p.donde or "",
                    tiene_subfabricaciones=p.tiene_subfabricaciones,
                    tiempo_optimo=p.tiempo_optimo or 0.0
                ) for p in productos
            ]

        return self.safe_execute(_operation) or []

    def get_latest_products(self, limit: int = 10) -> List[ProductDTO]:
        """
        Obtiene los últimos productos añadidos.
        Mantiene compatibilidad con: database_manager.get_latest_products()

        Args:
            limit: Número máximo de productos a devolver

        Returns:
            Lista de objetos ProductDTO
        """

        def _operation(session):
            # Usamos rowid para simular el comportamiento de SQLite
            productos = session.query(Producto) \
                .order_by(Producto.codigo.desc()) \
                .limit(limit).all()
            return [
                ProductDTO(
                    codigo=p.codigo,
                    descripcion=p.descripcion,
                    departamento=p.departamento,
                    tipo_trabajador=p.tipo_trabajador,
                    donde=p.donde or "",
                    tiene_subfabricaciones=p.tiene_subfabricaciones,
                    tiempo_optimo=p.tiempo_optimo or 0.0
                ) for p in productos
            ]

        return self.safe_execute(_operation) or []

    def get_product_details(self, codigo: str) -> Tuple[Optional[ProductDTO], List[SubfabricacionDTO], List[ProcesoMecanicoDTO]]:
        """
        Obtiene todos los detalles de un producto por su código.
        Mantiene compatibilidad con: database_manager.get_product_details()

        Args:
            codigo: Código del producto

        Returns:
            Tupla de (ProductDTO, List[SubfabricacionDTO], List[ProcesoMecanicoDTO])
        """

        def _operation(session):
            producto = session.query(Producto).filter_by(codigo=codigo).first()
            if not producto:
                return None, [], []

            # Convertir producto a DTO
            producto_data = ProductDTO(
                codigo=producto.codigo,
                descripcion=producto.descripcion,
                departamento=producto.departamento,
                tipo_trabajador=producto.tipo_trabajador,
                donde=producto.donde or "",
                tiene_subfabricaciones=producto.tiene_subfabricaciones,
                tiempo_optimo=producto.tiempo_optimo or 0.0
            )

            # Obtener subfabricaciones
            subfabs = session.query(Subfabricacion) \
                .filter_by(producto_codigo=codigo) \
                .all()
            subfabricaciones_data = []
            for sub in subfabs:
                subfabricaciones_data.append(SubfabricacionDTO(
                    id=sub.id,
                    producto_codigo=sub.producto_codigo,
                    descripcion=sub.descripcion,
                    tiempo=sub.tiempo,
                    tipo_trabajador=sub.tipo_trabajador,
                    maquina_id=sub.maquina_id
                ))

            # Obtener procesos mecánicos
            procesos = session.query(ProcesoMecanico) \
                .filter_by(producto_codigo=codigo) \
                .all()
            procesos_data = []
            for proceso in procesos:
                procesos_data.append(ProcesoMecanicoDTO(
                    id=proceso.id,
                    producto_codigo=proceso.producto_codigo,
                    nombre=proceso.nombre,
                    descripcion=proceso.descripcion,
                    tiempo=proceso.tiempo,
                    tipo_trabajador=proceso.tipo_trabajador
                ))

            return producto_data, subfabricaciones_data, procesos_data

        result = self.safe_execute(_operation)
        if not result:
            return None, [], []
        return result

    def add_product(self, data: Dict[str, Any], subfabricaciones: Optional[List[Dict]] = None) -> bool:
        """
        Añade un nuevo producto y sus subfabricaciones si las tiene.
        VERSIÓN MEJORADA con validación de maquina_id más limpia.
        """

        def _operation(session):
            producto = Producto(
                codigo=data["codigo"],
                descripcion=data["descripcion"],
                departamento=data["departamento"],
                tipo_trabajador=data["tipo_trabajador"],
                donde=data.get("donde"),
                tiene_subfabricaciones=data["tiene_subfabricaciones"],
                tiempo_optimo=data.get("tiempo_optimo")
            )
            session.add(producto)

            if data["tiene_subfabricaciones"] and subfabricaciones:
                for sub in subfabricaciones:
                    maquina_id = sub.get("maquina_id")

                    # Normalizar maquina_id a un entero o None
                    try:
                        maquina_id_final = int(maquina_id) if maquina_id not in [None, ""] else None
                    except (ValueError, TypeError):
                        self.logger.warning(
                            f"Valor de maquina_id inválido ('{maquina_id}') para la subfabricación '{sub['descripcion']}'. Se asignará como NULO.")
                        maquina_id_final = None

                    subfab = Subfabricacion(
                        producto_codigo=data["codigo"],
                        descripcion=sub["descripcion"],
                        tiempo=sub["tiempo"],
                        tipo_trabajador=sub["tipo_trabajador"],
                        maquina_id=maquina_id_final
                    )
                    session.add(subfab)

            procesos_mecanicos = data.get("procesos_mecanicos", [])
            if procesos_mecanicos:
                for proceso in procesos_mecanicos:
                    proc = ProcesoMecanico(
                        producto_codigo=data["codigo"],
                        nombre=proceso["nombre"],
                        descripcion=proceso["descripcion"],
                        tiempo=proceso["tiempo"],
                        tipo_trabajador=proceso["tipo_trabajador"]
                    )
                    session.add(proc)

            self.logger.info(f"Producto '{data['codigo']}' añadido/actualizado en la sesión.")
            return True

        return self.safe_execute(_operation) or False

    def update_product(self, codigo_original: str, data: Dict[str, Any],
                       subfabricaciones: Optional[List[Dict]] = None) -> bool:
        """
        Actualiza un producto existente y sus subfabricaciones.
        Mantiene compatibilidad con: database_manager.update_product()

        Args:
            codigo_original: Código original del producto
            data: Nuevos datos del producto
            subfabricaciones: Lista de subfabricaciones actualizadas

        Returns:
            True si se actualizó correctamente, False en caso contrario
        """

        def _operation(session):
            # Buscar producto
            producto = session.query(Producto).filter_by(codigo=codigo_original).first()
            if not producto:
                return False

            # Actualizar producto
            producto.codigo = data["codigo"]
            producto.descripcion = data["descripcion"]
            producto.departamento = data["departamento"]
            producto.tipo_trabajador = data["tipo_trabajador"]
            producto.donde = data.get("donde")
            producto.tiene_subfabricaciones = data["tiene_subfabricaciones"]
            producto.tiempo_optimo = data.get("tiempo_optimo")

            # Eliminar subfabricaciones y procesos mecánicos existentes
            session.query(Subfabricacion) \
                .filter_by(producto_codigo=codigo_original) \
                .delete()
            session.query(ProcesoMecanico) \
                .filter_by(producto_codigo=codigo_original) \
                .delete()

            # Añadir subfabricaciones actualizadas
            if data["tiene_subfabricaciones"] and subfabricaciones:
                for sub in subfabricaciones:
                    subfab = Subfabricacion(
                        producto_codigo=data["codigo"],
                        descripcion=sub["descripcion"],
                        tiempo=sub["tiempo"],
                        tipo_trabajador=sub["tipo_trabajador"],
                        maquina_id=sub.get("maquina_id")
                    )
                    session.add(subfab)

            # Añadir procesos mecánicos actualizados
            procesos_mecanicos = data.get("procesos_mecanicos", [])
            if procesos_mecanicos:
                for proceso in procesos_mecanicos:
                    proc = ProcesoMecanico(
                        producto_codigo=data["codigo"],
                        nombre=proceso["nombre"],
                        descripcion=proceso["descripcion"],
                        tiempo=proceso["tiempo"],
                        tipo_trabajador=proceso["tipo_trabajador"]
                    )
                    session.add(proc)

            self.logger.info(f"Producto '{codigo_original}' actualizado a '{data['codigo']}'.")
            return True

        return self.safe_execute(_operation) or False

    def delete_product(self, codigo: str) -> bool:
        """
        Elimina un producto de la base de datos.
        Mantiene compatibilidad con: database_manager.delete_product()

        Args:
            codigo: Código del producto a eliminar

        Returns:
            True si se eliminó correctamente, False en caso contrario
        """

        def _operation(session):
            producto = session.query(Producto).filter_by(codigo=codigo).first()
            if not producto:
                return False

            session.delete(producto)
            self.logger.info(f"Producto '{codigo}' eliminado con éxito.")
            return True

        return self.safe_execute(_operation) or False

    def get_materials_for_product(self, codigo: str) -> List[MaterialDTO]:
        """
        Obtiene los materiales asociados a un producto específico.

        Args:
            codigo: Código del producto

        Returns:
            Lista de objetos MaterialDTO
        """

        def _operation(session):
            producto = session.query(Producto).options(
                joinedload(Producto.materiales)
            ).filter_by(codigo=codigo).first()

            if not producto:
                return []

            return [
                MaterialDTO(
                    id=m.id,
                    codigo_componente=m.codigo_componente,
                    descripcion_componente=m.descripcion_componente
                ) for m in producto.materiales
            ]

        return self.safe_execute(_operation) or []