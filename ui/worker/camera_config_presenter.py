# -*- coding: utf-8 -*-
"""
Nombre del Módulo: camera_config_presenter

Descripción: Lógica de sondeo, detalle y validación de cámaras para ``CameraConfigDialog``,
             usando ``CameraManager`` y DTOs de configuración.
"""

import logging
from typing import List, Optional, Tuple
from core.camera_manager import CameraManager, CameraInfo
from core.dtos import CameraConfigDTO, CameraDetailDTO

class CameraConfigPresenter:
    """
    Presentador que desacopla la lógica de CameraManager de la UI de configuración.
    """

    def __init__(self, camera_manager: CameraManager):
        self.camera_manager = camera_manager
        self.logger = logging.getLogger("EvolucionTiemposApp.CameraConfigPresenter")
        self._detected_cameras: List[CameraConfigDTO] = []

    def detect_cameras_light(self) -> List[CameraConfigDTO]:
        """
        Realiza un sondeo rápido de cámaras y devuelve DTOs.
        """
        try:
            self.logger.info("Presenter: Iniciando sondeo ligero...")
            raw_cameras = self.camera_manager.detect_cameras(force_refresh=True)
            self._detected_cameras = [
                CameraConfigDTO(
                    index=cam.index,
                    name=cam.name,
                    is_external=cam.is_external
                ) for cam in raw_cameras
            ]
            return self._detected_cameras
        except Exception as e:
            self.logger.error(f"Error en sondeo ligero (presenter): {e}")
            return []

    def get_camera_detail(self, index: int) -> Optional[CameraDetailDTO]:
        """
        Obtiene información detallada de una cámara (puede ser info previa o nueva).
        """
        raw_info = self.camera_manager.get_camera_info(index)
        if not raw_info:
            return None
            
        return self._map_to_detail_dto(raw_info)

    def test_camera(self, index: int) -> Tuple[bool, Optional[CameraDetailDTO]]:
        """
        Realiza una validación pesada con preview.
        """
        try:
            self.logger.info(f"Presenter: Probando cámara {index}...")
            success = self.camera_manager.test_camera_with_preview(index, duration=3.0)
            raw_info = self.camera_manager.get_camera_info(index)
            
            detail = self._map_to_detail_dto(raw_info) if raw_info else None
            return success, detail
        except Exception as e:
            self.logger.error(f"Error probando cámara {index}: {e}")
            return False, None

    def validate_before_save(self, index: int) -> Tuple[bool, str, Optional[CameraDetailDTO]]:
        """
        Valida la cámara antes de permitir el guardado si no está validada.
        """
        raw_info = self.camera_manager.get_camera_info(index)
        if raw_info and raw_info.is_working:
            return True, "", self._map_to_detail_dto(raw_info)

        is_valid, error_msg = self.camera_manager.validate_camera(index)
        if is_valid:
            updated_info = self.camera_manager.get_camera_info(index)
            return True, "", self._map_to_detail_dto(updated_info) if updated_info else None
        
        return False, error_msg or "Validación de cámara fallida.", None

    def _map_to_detail_dto(self, info: CameraInfo) -> CameraDetailDTO:
        """Convierte CameraInfo de core a CameraDetailDTO."""
        return CameraDetailDTO(
            index=info.index,
            name=info.name,
            width=info.width,
            height=info.height,
            fps=info.fps,
            backend=info.backend,
            is_working=info.is_working,
            error_message=info.error_message
        )
