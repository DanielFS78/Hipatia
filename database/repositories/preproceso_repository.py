# repositories/preproceso_repository.py
"""
Repositorio para la gestión 100% SQLAlchemy de Preprocesos y Fabricaciones.
"""
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

from .base import BaseRepository
from ..models import Preproceso, Fabricacion, Material
from core.dtos import PreprocesoDTO, FabricacionDTO, MaterialDTO, FabricacionProductoDTO, ComponenteDTO


class PreprocesoRepository(BaseRepository):
    """
    Gestiona las operaciones CRUD para los modelos Preproceso y Fabricacion
    utilizando exclusivamente SQLAlchemy.
    """

    def get_all_preprocesos(self) -> List[PreprocesoDTO]:
        """Obtiene todos los preprocesos con sus materiales como DTOs."""

        def _operation(session):
            preprocesos_obj = session.query(Preproceso).options(
                joinedload(Preproceso.materiales)
            ).order_by(Preproceso.nombre).all()

            results = []
            for p in preprocesos_obj:
                componentes = [
                    ComponenteDTO(id=c.id, descripcion=c.descripcion_componente) 
                    for c in p.materiales
                ]
                dto = PreprocesoDTO(
                    id=p.id,
                    nombre=p.nombre,
                    descripcion=p.descripcion,
                    tiempo=p.tiempo,
                    componentes=componentes
                )
                results.append(dto)
            return results

        return self.safe_execute(_operation) or []

    def get_all_fabricaciones(self) -> List[FabricacionDTO]:
        """
        Obtiene todas las fabricaciones de la base de datos como DTOs.
        """
        def _operation(session):
            fabricaciones = session.query(Fabricacion).order_by(Fabricacion.id.desc()).all()
            
            results = []
            for f in fabricaciones:
                results.append(FabricacionDTO(
                    id=f.id,
                    codigo=f.codigo,
                    descripcion=f.descripcion
                ))
            return results

        return self.safe_execute(_operation) or []

    def get_products_for_fabricacion(self, fabricacion_id: int) -> List[FabricacionProductoDTO]:
        """
        Obtiene todos los productos asociados a una fabricación, incluyendo
        la cantidad de cada uno, consultando la tabla de enlace.

        Args:
            fabricacion_id: ID de la fabricación.

        Returns:
            Lista de FabricacionProductoDTO (producto_codigo, cantidad).
        """

        def _operation(session):
            from sqlalchemy import text  # Necesario para ejecutar SQL directo

            # Nota: Usamos SQL directo porque 'fabricacion_productos' no está
            # directamente mapeada como relación en el modelo Fabricacion.
            # Podríamos mapearla, pero esto mantiene la compatibilidad simple.
            sql_query = text("""
                SELECT producto_codigo, cantidad
                FROM fabricacion_productos
                WHERE fabricacion_id = :fab_id
                ORDER BY producto_codigo
            """)

            result = session.execute(sql_query, {"fab_id": fabricacion_id}).fetchall()

            # fetchall() devuelve una lista de objetos Row, los convertimos a DTOs
            return [
                FabricacionProductoDTO(producto_codigo=row[0], cantidad=row[1]) 
                for row in result
            ]

        return self.safe_execute(_operation) or []

    def get_preproceso_components(self, preproceso_id: int) -> List[ComponenteDTO]:
        """
        Obtiene los componentes (materiales) asociados a un preproceso específico.
        Mantiene compatibilidad con database_manager.get_preproceso_components().

        Args:
            preproceso_id: ID del preproceso.

        Returns:
            Lista de ComponenteDTO (id, descripcion).
            La descripción usada es 'descripcion_componente' del modelo Material.
        """

        def _operation(session):
            # Usamos joinedload para cargar eficientemente los materiales asociados
            preproceso = session.query(Preproceso).options(
                joinedload(Preproceso.materiales)  # Carga la relación 'materiales'
            ).filter_by(id=preproceso_id).first()

            if not preproceso:
                self.logger.warning(f"No se encontró preproceso con ID {preproceso_id}")
                return []  # Devuelve lista vacía si no se encuentra

            # Extraer los datos de los materiales en el formato de DTO esperado
            # Ordenamos por descripción para mantener consistencia con el método legacy
            componentes = sorted(
                [ComponenteDTO(id=mat.id, descripcion=mat.descripcion_componente) for mat in preproceso.materiales],
                key=lambda x: x.descripcion  # Ordenar por descripción
            )

            return componentes

        # Devolver la lista o una lista vacía en caso de error
        return self.safe_execute(_operation) or []

    def add_product_to_fabricacion(self, fabricacion_id: int, producto_codigo: str, cantidad: int = 1) -> bool:
        """
        Añade un producto a una fabricación o actualiza su cantidad si ya existe.
        Interactúa directamente con la tabla de enlace 'fabricacion_productos'.

        Args:
            fabricacion_id: ID de la fabricación.
            producto_codigo: Código del producto a añadir.
            cantidad: Cantidad del producto (por defecto 1).

        Returns:
            True si la operación fue exitosa, False en caso contrario.
        """

        def _operation(session):
            from sqlalchemy import text  # Para ejecutar SQL directo (INSERT OR REPLACE)
            from sqlalchemy.exc import IntegrityError  # Para manejar posibles errores FK

            try:
                # Usamos INSERT OR REPLACE para simplificar: si ya existe la combinación
                # fabricacion_id/producto_codigo, actualiza la cantidad; si no, la inserta.
                # Nota: Esto asume que SQLite está configurado para soportar INSERT OR REPLACE.
                sql_insert_or_replace = text("""
                    INSERT OR REPLACE INTO fabricacion_productos
                    (fabricacion_id, producto_codigo, cantidad)
                    VALUES (:fab_id, :prod_code, :qty)
                """)

                session.execute(sql_insert_or_replace, {
                    "fab_id": fabricacion_id,
                    "prod_code": producto_codigo,
                    "qty": cantidad
                })
                self.logger.info(
                    f"Producto '{producto_codigo}' (x{cantidad}) añadido/actualizado en fabricación ID {fabricacion_id}")
                return True
            except IntegrityError as e:
                # Esto podría ocurrir si el fabricacion_id o producto_codigo no existen
                # en sus respectivas tablas principales (violación de Foreign Key).
                session.rollback()  # Importante deshacer cualquier cambio parcial
                self.logger.error(
                    f"Error de integridad al añadir producto a fabricación: {e}. ¿Existen la fabricación y el producto?")
                return False
            except Exception as e:
                session.rollback()  # Deshacer en caso de cualquier otro error
                self.logger.error(f"Error inesperado añadiendo producto a fabricación: {e}")
                return False

        # safe_execute manejará el commit final si _operation retorna True
        return self.safe_execute(_operation) or False

    def set_products_for_fabricacion(self, fabricacion_id: int, products: list) -> bool:
        """
        Establece los productos de una fabricación, reemplazando los anteriores.

        Args:
            fabricacion_id: ID de la fabricación.
            products: Lista de tuplas (producto_codigo, cantidad).

        Returns:
            True si la operación fue exitosa, False en caso contrario.
        """

        def _operation(session):
            from sqlalchemy import text

            try:
                # Primero eliminar productos existentes
                delete_sql = text("DELETE FROM fabricacion_productos WHERE fabricacion_id = :fab_id")
                session.execute(delete_sql, {"fab_id": fabricacion_id})

                # Insertar los nuevos productos
                if products:
                    insert_sql = text("""
                        INSERT INTO fabricacion_productos (fabricacion_id, producto_codigo, cantidad)
                        VALUES (:fab_id, :prod_code, :qty)
                    """)
                    for prod_code, qty in products:
                        session.execute(insert_sql, {
                            "fab_id": fabricacion_id,
                            "prod_code": prod_code,
                            "qty": qty
                        })

                self.logger.info(f"Productos de fabricación ID {fabricacion_id} actualizados: {len(products)} productos")
                return True
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error estableciendo productos para fabricación: {e}")
                return False

        return self.safe_execute(_operation) or False

    def get_fabricacion_by_codigo(self, codigo: str) -> Optional[FabricacionDTO]:
        """
        Busca y devuelve una única Orden de Fabricación por su código exacto como DTO.
        """

        def _operation(session, **kwargs):
            fab = session.query(Fabricacion).filter(
                Fabricacion.codigo == codigo
            ).first()
            
            if fab:
                return FabricacionDTO(
                    id=fab.id,
                    codigo=fab.codigo,
                    descripcion=fab.descripcion
                )
            return None

        return self.safe_execute(_operation)

    def create_preproceso(self, data: dict) -> bool:
        """Crea un nuevo preproceso y lo asocia con sus materiales."""

        def _operation(session):
            nuevo_preproceso = Preproceso(
                nombre=data['nombre'],
                descripcion=data['descripcion'],
                tiempo=data['tiempo']
            )
            if data.get('componentes_ids'):
                materiales = session.query(Material).filter(Material.id.in_(data['componentes_ids'])).all()
                nuevo_preproceso.materiales = materiales

            session.add(nuevo_preproceso)
            return True

        return self.safe_execute(_operation) or False

    def update_preproceso(self, preproceso_id: int, data: dict) -> bool:
        """Actualiza un preproceso existente."""

        def _operation(session):
            preproceso = session.query(Preproceso).filter_by(id=preproceso_id).first()
            if not preproceso: return False

            preproceso.nombre = data['nombre']
            preproceso.descripcion = data['descripcion']
            preproceso.tiempo = data['tiempo']

            if 'componentes_ids' in data:
                materiales = session.query(Material).filter(Material.id.in_(data['componentes_ids'])).all()
                preproceso.materiales = materiales

            return True

        return self.safe_execute(_operation) or False

    def delete_preproceso(self, preproceso_id: int) -> bool:
        """Elimina un preproceso y sus relaciones."""

        def _operation(session):
            preproceso = session.query(Preproceso).filter_by(id=preproceso_id).first()
            if preproceso:
                session.delete(preproceso)
                return True
            return False

        return self.safe_execute(_operation) or False

    # --- Métodos CRUD para Fabricaciones ---

    def search_fabricaciones(self, query: str) -> List[FabricacionDTO]:
        """Busca fabricaciones por código o descripción y devuelve DTOs."""

        def _operation(session):
            results = session.query(Fabricacion).filter(
                or_(
                    Fabricacion.codigo.ilike(f"%{query}%"),
                    Fabricacion.descripcion.ilike(f"%{query}%")
                )
            ).order_by(Fabricacion.id.desc()).all()
            
            return [FabricacionDTO(id=f.id, codigo=f.codigo, descripcion=f.descripcion) for f in results]

        return self.safe_execute(_operation) or []

    # EN: repositories/preproceso_repository.py

    def get_fabricacion_by_id(self, fabricacion_id: int) -> Optional[FabricacionDTO]:
        """Obtiene una fabricación con sus preprocesos y devuelve un DTO."""

        def _operation(session):
            fabricacion = session.query(Fabricacion).options(
                joinedload(Fabricacion.preprocesos)
            ).filter_by(id=fabricacion_id).first()

            if fabricacion:
                preprocesos = [
                    PreprocesoDTO(
                        id=p.id, 
                        nombre=p.nombre, 
                        descripcion=p.descripcion, 
                        tiempo=p.tiempo, 
                        componentes=[] # No cargamos componentes profundamente aquí por ahora
                    ) 
                    for p in fabricacion.preprocesos
                ]
                return FabricacionDTO(
                    id=fabricacion.id,
                    codigo=fabricacion.codigo,
                    descripcion=fabricacion.descripcion,
                    preprocesos=preprocesos
                )
            return None

        return self.safe_execute(_operation)

    def create_fabricacion_with_preprocesos(self, data: Dict[str, Any]) -> bool:
        """Crea una fabricación y le asigna sus preprocesos en una transacción."""

        def _operation(session):
            nueva_fabricacion = Fabricacion(
                codigo=data['codigo'],
                descripcion=data['descripcion']
            )
            if data.get('preprocesos_ids'):
                preprocesos = session.query(Preproceso).filter(Preproceso.id.in_(data['preprocesos_ids'])).all()
                nueva_fabricacion.preprocesos = preprocesos

            session.add(nueva_fabricacion)
            return True

        return self.safe_execute(_operation) or False

    def update_fabricacion_and_preprocesos(self, fabricacion_id: int, data: Dict[str, Any],
                                           preproceso_ids: Optional[List[int]]) -> bool:
        """Actualiza los datos de una fabricación y, opcionalmente, su lista de preprocesos."""

        def _operation(session):
            fabricacion = session.query(Fabricacion).filter_by(id=fabricacion_id).first()
            if not fabricacion: return False

            # Actualizar datos básicos
            fabricacion.codigo = data['codigo']
            fabricacion.descripcion = data['descripcion']

            # Actualizar preprocesos solo si se proporciona una nueva lista
            if preproceso_ids is not None:
                nuevos_preprocesos = session.query(Preproceso).filter(Preproceso.id.in_(preproceso_ids)).all()
                fabricacion.preprocesos = nuevos_preprocesos

            return True

        return self.safe_execute(_operation) or False

    def delete_fabricacion(self, fabricacion_id: int) -> bool:
        """
        Elimina una fabricación de la base de datos, limpiando primero
        explícitamente sus relaciones para manejar datos inconsistentes.
        """

        def _operation(session):
            # Importamos la tabla de enlace directamente desde los modelos
            from ..models import fabricacion_preproceso_link

            # Buscamos la fabricación que queremos eliminar
            fabricacion = session.query(Fabricacion).filter_by(id=fabricacion_id).first()

            if fabricacion:
                # --- INICIO DE LA CORRECCIÓN ---
                # Paso 1: Borrado "manual" y seguro de todas las relaciones en la tabla de enlace.
                # Esto es más robusto que `fabricacion.preprocesos.clear()` y soluciona
                # el problema con los datos antiguos.
                session.execute(
                    fabricacion_preproceso_link.delete().where(
                        fabricacion_preproceso_link.c.fabricacion_id == fabricacion_id
                    )
                )

                # Paso 2: Ahora que las relaciones están limpias, eliminamos el objeto principal.
                session.delete(fabricacion)
                return True
            return False

        return self.safe_execute(_operation) or False

    def get_latest_fabricaciones(self, limit: int = 5) -> List[FabricacionDTO]:
        """Obtiene las últimas fabricaciones añadidas."""
        def _operation(session):
            fabricaciones = session.query(Fabricacion).order_by(Fabricacion.id.desc()).limit(limit).all()
            return [FabricacionDTO(id=f.id, codigo=f.codigo, descripcion=f.descripcion) for f in fabricaciones]
        
        return self.safe_execute(_operation) or []

    def get_preprocesos_by_fabricacion(self, fabricacion_id: int) -> List[PreprocesoDTO]:
        """
        Obtiene los preprocesos de una fabricación.
        Retorna lista de PreprocesoDTO.
        """
        def _operation(session):
            fabricacion = session.query(Fabricacion).options(joinedload(Fabricacion.preprocesos)).filter_by(id=fabricacion_id).first()
            if fabricacion:
                return [
                    PreprocesoDTO(
                        id=p.id, 
                        nombre=p.nombre, 
                        descripcion=p.descripcion,
                        tiempo=p.tiempo, # Added missing field
                        componentes=[]
                    ) for p in fabricacion.preprocesos
                ]
            return []
        
        return self.safe_execute(_operation) or []

    def update_fabricacion_preprocesos(self, fabricacion_id: int, preproceso_ids: List[int]) -> bool:
        """Actualiza solamente la lista de preprocesos de una fabricación."""
        def _operation(session):
            fabricacion = session.query(Fabricacion).filter_by(id=fabricacion_id).first()
            if not fabricacion: return False
            
            nuevos_preprocesos = session.query(Preproceso).filter(Preproceso.id.in_(preproceso_ids)).all()
            fabricacion.preprocesos = nuevos_preprocesos
            return True

        return self.safe_execute(_operation) or False