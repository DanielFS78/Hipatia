# -*- coding: utf-8 -*-
"""
Nombre del Módulo: bom_import_service
Descripción: Servicio de dominio que persiste un BOM A3RP tras la supervisión en UI.
             Lee ``BOMNodeDTO`` con ``import_selected`` e ``import_role``, exige un único
             producto final, actualiza el registro en ``productos`` y crea/vincula
             subfabricaciones, procesos mecánicos y materiales al código final.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Set

from core.import_manager.dto import BOMImportRole, BOMNodeDTO


class BOMImportService:
    """
    Orquesta la escritura en BD a partir del árbol supervisado en ``BOMImportPreviewDialog``.

    No crea productos de catálogo para subfabricaciones: estas van a la tabla
    ``subfabricaciones`` del producto final. El tiempo óptimo del producto se incrementa
    con la suma de tiempos de procesos mecánicos realmente nuevos respecto al estado previo.
    """

    _PROC_MIN_TIME = 0.01

    def __init__(self, product_service: Any) -> None:
        """
        Args:
            product_service: Fachada/servicio con CRUD de productos y, si aplica,
                ``add_material`` / ``link_material_to_product`` / ``get_materials_for_product``.
        """
        self.logger = logging.getLogger("EvolucionTiemposApp")
        self.product_service = product_service

    def import_bom_tree(self, root_node: BOMNodeDTO) -> Dict[str, int]:
        """
        Importa únicamente nodos con ``import_selected=True`` y ``import_role`` definido.

        Requiere exactamente un nodo ``BOMImportRole.FINAL_PRODUCT`` entre los seleccionados.

        Args:
            root_node: Raíz del árbol (se recorre en profundidad).

        Returns:
            Diccionario de contadores: ``creados``, ``actualizados``, ``errores``,
            ``subfabricaciones_vinculadas``, ``procesos_mecanicos``, ``componentes``.
        """
        stats: Dict[str, int] = {
            "creados": 0,
            "actualizados": 0,
            "errores": 0,
            "subfabricaciones_vinculadas": 0,
            "procesos_mecanicos": 0,
            "componentes": 0,
        }
        selected = self._collect_selected(root_node)
        finals = [n for n in selected if n.import_role == BOMImportRole.FINAL_PRODUCT]
        if len(finals) != 1:
            self.logger.error(
                "Importación BOM: se requiere exactamente un Producto final entre las filas marcadas."
            )
            stats["errores"] += 1
            return stats

        final_node = finals[0]
        final_code = final_node.codigo_componente
        if not final_code:
            stats["errores"] += 1
            return stats

        sub_nodes = [n for n in selected if n.import_role == BOMImportRole.SUBFABRICATION]
        proc_nodes = [n for n in selected if n.import_role == BOMImportRole.MECHANICAL_PROCESS]
        comp_nodes = [n for n in selected if n.import_role == BOMImportRole.COMPONENT]

        # Solo el producto final es fila en ``productos``. Las subfabricaciones van a
        # ``subfabricaciones`` del padre, no como productos de catálogo.
        self._ensure_main_product(final_node, bool(sub_nodes), stats)

        details = self.product_service.get_product_details(final_code)
        if not details or not details.producto:
            self.logger.error("Importación BOM: no se pudieron leer detalles del producto final %s.", final_code)
            stats["errores"] += 1
            return stats

        sub_rows = [self._sub_row_from_node(n) for n in sub_nodes]
        merged_subs = self._merge_subfabricaciones(details.subfabricaciones, sub_rows)

        new_proc_dicts = [self._proceso_dict_from_node(n) for n in proc_nodes]
        old_proc_names = {
            str(getattr(p, "nombre", "") or "").strip().lower()
            for p in (details.procesos_mecanicos or [])
        }
        procs_really_new = [
            p for p in new_proc_dicts if p["nombre"].strip().lower() not in old_proc_names
        ]
        merged_procs = self._merge_procesos(details.procesos_mecanicos, new_proc_dicts)

        prod_data: Dict[str, Any] = {
            "codigo": details.producto.codigo,
            "descripcion": final_node.denominacion or details.producto.descripcion,
            "departamento": details.producto.departamento,
            "donde": details.producto.donde or "Importado A3RP",
            "tiene_subfabricaciones": 1 if merged_subs else 0,
            "tiempo_optimo": float(details.producto.tiempo_optimo or 0.0),
            "tipo_trabajador": int(details.producto.tipo_trabajador or 1),
            "procesos_mecanicos": merged_procs,
        }
        if procs_really_new:
            prod_data["tiempo_optimo"] += sum(float(p["tiempo"]) for p in procs_really_new)

        if self.product_service.update_product(final_code, prod_data, merged_subs):
            stats["actualizados"] += 1
            stats["subfabricaciones_vinculadas"] = len(sub_rows)
            stats["procesos_mecanicos"] = len(procs_really_new)
        else:
            stats["errores"] += 1
            return stats

        for n in comp_nodes:
            self._link_component(final_code, n, stats)

        self.logger.info("Importación BOM completada. Estadísticas: %s", stats)
        return stats

    def _collect_selected(self, node: BOMNodeDTO) -> List[BOMNodeDTO]:
        """
        Recorre el árbol y devuelve nodos marcados con código y rol válidos (sin duplicar por ``id``).

        Args:
            node: Nodo raíz desde el que iniciar el DFS.

        Returns:
            Lista plana de nodos elegibles para importación.
        """
        out: List[BOMNodeDTO] = []
        visited: Set[int] = set()

        def walk(n: BOMNodeDTO) -> None:
            nid = id(n)
            if nid in visited:
                return
            visited.add(nid)
            if n.import_selected and n.codigo_componente and n.import_role is not None:
                out.append(n)
            for h in n.hijos:
                walk(h)

        walk(node)
        return out

    def _ensure_main_product(self, node: BOMNodeDTO, has_subfabs: bool, stats: Dict[str, int]) -> None:
        """
        Garantiza que exista la fila de producto final antes de fusionar detalles.

        Args:
            node: Nodo producto final.
            has_subfabs: Si hay subfabricaciones seleccionadas (afecta departamento y flag).
            stats: Contadores mutables (creación vs error).
        """
        codigo = node.codigo_componente
        try:
            existing = self.product_service.get_product_by_code(codigo)
            if existing:
                stats["actualizados"] += 1
                return
            new_data = {
                "codigo": codigo,
                "descripcion": node.denominacion or f"Producto IMPORTADO {codigo}",
                "departamento": "Montaje" if has_subfabs else "Mecánica",
                "donde": "Importado A3RP",
                "tiene_subfabricaciones": 1 if has_subfabs else 0,
                "tiempo_optimo": self._PROC_MIN_TIME,
                "tipo_trabajador": 1,
            }
            result = self.product_service.add_product(new_data, [])
            if result == "SUCCESS":
                stats["creados"] += 1
            else:
                self.logger.error("Fallo creando producto final %s: %s", codigo, result)
                stats["errores"] += 1
        except Exception as e:
            self.logger.error("Excepción creando producto final %s: %s", codigo, e)
            stats["errores"] += 1

    @staticmethod
    def _sub_row_from_node(n: BOMNodeDTO) -> Dict[str, Any]:
        """Construye el dict de subfabricación esperado por ``update_product`` desde un nodo."""
        desc = (n.denominacion or "").strip()
        label = f"{n.codigo_componente} — {desc}" if desc else str(n.codigo_componente)
        return {
            "id": n.codigo_componente,
            "descripcion": label,
            "tiempo": 0.0,
            "tipo_trabajador": 1,
            "cantidad": n.cantidad,
        }

    def _proceso_dict_from_node(self, n: BOMNodeDTO) -> Dict[str, Any]:
        """Mapea un nodo de proceso mecánico al payload de proceso en producto."""
        nombre = (n.codigo_componente or "Proceso").strip() or "Proceso"
        desc = (n.denominacion or "").strip()
        return {
            "nombre": nombre[:200],
            "descripcion": desc[:2000] if desc else nombre[:2000],
            "tiempo": self._PROC_MIN_TIME,
            "tipo_trabajador": 1,
        }

    def _merge_subfabricaciones(self, existing: Any, new_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Une subfabricaciones ya persistidas con filas nuevas sin duplicar por código lógico."""
        rows: List[Dict[str, Any]] = []
        seen_codes: Set[str] = set()
        for s in existing or []:
            rows.append(
                {
                    "id": getattr(s, "id", 0),
                    "descripcion": str(getattr(s, "descripcion", "") or ""),
                    "tiempo": float(getattr(s, "tiempo", 0.0) or 0.0),
                    "tipo_trabajador": int(getattr(s, "tipo_trabajador", 1) or 1),
                    "maquina_id": getattr(s, "maquina_id", None),
                    "producto_codigo": str(getattr(s, "producto_codigo", "") or ""),
                }
            )
        for nr in new_rows:
            cid = str(nr.get("id", "") or "")
            if cid and cid not in seen_codes:
                seen_codes.add(cid)
                rows.append(nr)
        return rows

    def _merge_procesos(self, existing: Any, new_dicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Concatena procesos existentes y propuestos, evitando duplicados por nombre (casefold)."""
        out: List[Dict[str, Any]] = []
        seen: Set[str] = set()
        for p in existing or []:
            d = {
                "nombre": str(getattr(p, "nombre", "") or ""),
                "descripcion": str(getattr(p, "descripcion", "") or ""),
                "tiempo": float(getattr(p, "tiempo", 0.0) or 0.0),
                "tipo_trabajador": int(getattr(p, "tipo_trabajador", 1) or 1),
            }
            out.append(d)
            seen.add(str(d["nombre"]).strip().lower())
        for nd in new_dicts:
            key = str(nd.get("nombre", "") or "").strip().lower()
            if key not in seen:
                out.append(nd)
                seen.add(key)
        return out

    def _link_component(self, final_code: str, node: BOMNodeDTO, stats: Dict[str, int]) -> None:
        """
        Crea material si hace falta y lo enlaza al producto final vía ``link_material_to_product``.

        Args:
            final_code: Código del producto final.
            node: Nodo componente seleccionado.
            stats: Contador ``componentes`` / ``errores``.
        """
        codigo = node.codigo_componente.strip()
        desc = (node.denominacion or "").strip() or f"Componente {codigo}"
        add_m = getattr(self.product_service, "add_material", None)
        link_m = getattr(self.product_service, "link_material_to_product", None)
        get_mats = getattr(self.product_service, "get_materials_for_product", None)
        if not callable(add_m) or not callable(link_m):
            self.logger.warning("Servicio de producto sin API de materiales; no se vincula componente %s.", codigo)
            stats["errores"] += 1
            return
        try:
            existing_codes: Set[str] = set()
            if callable(get_mats):
                for m in get_mats(final_code):
                    existing_codes.add(str(getattr(m, "codigo_componente", "") or ""))
            if codigo in existing_codes:
                return
            mid = add_m(codigo, desc)
            if not mid:
                stats["errores"] += 1
                return
            if link_m(final_code, mid):
                stats["componentes"] += 1
            else:
                stats["errores"] += 1
        except Exception as e:
            self.logger.error("Error vinculando componente %s: %s", codigo, e)
            stats["errores"] += 1
