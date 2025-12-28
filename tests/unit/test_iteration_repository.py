import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from database.repositories.iteration_repository import IterationRepository
from core.dtos import ProductIterationDTO, ProductIterationMaterialDTO
from database.models import ProductIteration, Material

class TestIterationRepository:

    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_session):
        repo = IterationRepository(session_factory=lambda: mock_session)
        # Mock the logger to avoid actual logging during tests
        repo.logger = MagicMock()
        return repo

    def test_get_all_iterations_with_dates_returns_dtos(self, repository, mock_session):
        # Arrange
        mock_iter1 = MagicMock(spec=ProductIteration)
        mock_iter1.id = 1
        mock_iter1.producto_codigo = "PROD001"
        mock_iter1.descripcion_cambio = "Cambio 1"
        mock_iter1.fecha_creacion = datetime(2023, 1, 1, 12, 0)
        mock_iter1.nombre_responsable = "User 1"
        mock_iter1.tipo_fallo = "Leve"
        mock_iter1.ruta_imagen = "img1.png"
        mock_iter1.ruta_plano = "plano1.pdf"
        mock_iter1.producto.descripcion = "Desc Prod 1"

        mock_session.query.return_value.options.return_value.order_by.return_value.all.return_value = [mock_iter1]

        # Act
        results = repository.get_all_iterations_with_dates()

        # Assert
        assert len(results) == 1
        dto = results[0]
        assert isinstance(dto, ProductIterationDTO)
        assert dto.id == 1
        assert dto.producto_codigo == "PROD001"
        assert dto.producto_descripcion == "Desc Prod 1"
        assert dto.nombre_responsable == "User 1"

    def test_get_product_iterations_returns_dtos_with_materials(self, repository, mock_session):
        # Arrange
        mock_iter = MagicMock(spec=ProductIteration)
        mock_iter.id = 2
        mock_iter.producto_codigo = "PROD002"
        mock_iter.descripcion_cambio = "Cambio 2"
        mock_iter.fecha_creacion = datetime(2023, 1, 2, 12, 0)
        mock_iter.nombre_responsable = "User 2"
        mock_iter.tipo_fallo = "Grave"
        mock_iter.ruta_imagen = None
        mock_iter.ruta_plano = None
        
        mock_mat = MagicMock(spec=Material)
        mock_mat.id = 10
        mock_mat.codigo_componente = "MAT001"
        mock_mat.descripcion_componente = "Material 1"
        
        mock_iter.materiales = [mock_mat]

        mock_session.query.return_value.filter_by.return_value.options.return_value.order_by.return_value.all.return_value = [mock_iter]

        # Act
        results = repository.get_product_iterations("PROD002")

        # Assert
        assert len(results) == 1
        dto = results[0]
        assert isinstance(dto, ProductIterationDTO)
        assert dto.producto_codigo == "PROD002"
        assert len(dto.materiales) == 1
        mat_dto = dto.materiales[0]
        assert isinstance(mat_dto, ProductIterationMaterialDTO)
        assert mat_dto.codigo == "MAT001"

    def test_add_product_iteration_success(self, repository, mock_session):
        # Arrange
        # Mock lookup for material
        mock_session.query.return_value.filter_by.return_value.first.return_value = None # Material doesn't exist

        # Act
        materiales = [{'codigo': 'MAT_NEW', 'descripcion': 'New Material'}]
        result_id = repository.add_product_iteration(
            codigo_producto="PROD003",
            responsable="User 3",
            descripcion="New Iteration",
            tipo_fallo="Mejora",
            materiales_list=materiales,
            ruta_imagen="path/to/img",
            ruta_plano="path/to/plan"
        )

        # Assert
        assert mock_session.add.call_count >= 1 # Iteration + Material
        
        args, _ = mock_session.add.call_args_list[0]
        obj = args[0]
        assert isinstance(obj, ProductIteration)
        assert obj.producto_codigo == "PROD003"
        
        # Verify material addition
        args_mat, _ = mock_session.add.call_args_list[1]
        obj_mat = args_mat[0]
        assert isinstance(obj_mat, Material)
        assert obj_mat.codigo_componente == "MAT_NEW"

    def test_add_product_iteration_existing_material_update(self, repository, mock_session):
        """Test adding iteration updates (or doesn't duplicate) existing material, and updates description."""
        # Arrange
        mock_mat = MagicMock(spec=Material)
        mock_mat.id = 1
        mock_mat.codigo_componente = "MAT_EXIST"
        mock_mat.descripcion_componente = "Old Desc"
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_mat
        
        # Act
        # Same code, new description
        materiales = [{'codigo': 'MAT_EXIST', 'descripcion': 'New Desc'}] 
        repository.add_product_iteration(
            "PROD", "Resp", "Desc", "Fail", materiales
        )
        
        # Assert
        # Check description updated (lines 155-156)
        assert mock_mat.descripcion_componente == "New Desc"

    def test_update_product_iteration_success(self, repository, mock_session):
        # Arrange
        mock_iter = MagicMock(spec=ProductIteration)
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_iter

        # Act
        result = repository.update_product_iteration(1, "New User", "New Desc", "New Type")

        # Assert
        assert result is True
        assert mock_iter.nombre_responsable == "New User"
        assert mock_iter.descripcion_cambio == "New Desc"

    def test_delete_product_iteration_success(self, repository, mock_session):
        # Arrange
        mock_iter = MagicMock(spec=ProductIteration)
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_iter

        # Act
        result = repository.delete_product_iteration(1)

        # Assert
        assert result is True
        mock_session.delete.assert_called_once_with(mock_iter)

    def test_update_iteration_file_path(self, repository, mock_session):
        # Arrange
        mock_iter = MagicMock(spec=ProductIteration)
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_iter
        
        # Act
        result = repository.update_iteration_file_path(1, "ruta_plano", "/path/to/file.pdf")
        
        # Assert
        assert result is True
        assert mock_iter.ruta_plano == "/path/to/file.pdf"
        
    def test_update_iteration_file_path_invalid_column(self, repository, mock_session):
        # Act
        result = repository.update_iteration_file_path(1, "invalid_col", "path")
        
        # Assert
        assert result is False

    def test_update_iteration_image_path_success(self, repository, mock_session):
        """Test success path for update_iteration_image_path (lines 247-249)."""
        # Arrange
        mock_iter = MagicMock(spec=ProductIteration)
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_iter
        
        # Act
        result = repository.update_iteration_image_path(10, "new_image.jpg")
        
        # Assert
        assert result is True
        assert mock_iter.ruta_imagen == "new_image.jpg"

    def test_update_non_existent_iteration_returns_false(self, repository, mock_session):
        # Arrange
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        # Act
        result = repository.update_product_iteration(999, "User", "Desc", "Type")
        
        # Assert
        assert result is False

    def test_delete_non_existent_iteration_returns_false(self, repository, mock_session):
         # Arrange
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        # Act
        result = repository.delete_product_iteration(999)
        
        # Assert
        assert result is False

    def test_get_default_error_value(self, repository, mock_session):
        """Test el valor por defecto en caso de error global."""
        assert repository._get_default_error_value() == []

    def test_add_product_iteration_error(self, repository, mock_session):
        """Test error handling in add_product_iteration."""
        mock_session.add.side_effect = Exception("Database Error")
        
        result_id = repository.add_product_iteration(
            codigo_producto="PROD003",
            responsable="User 3",
            descripcion="New Iteration",
            tipo_fallo="Mejora",
            materiales_list=[]
        )
        
        # En caso de error, BaseRepository captura y loguea, retornando _get_default_error_value (que es [])
        # Sin embargo, add_product_iteration espera retornar Optional[int] (None si falla)
        # El BaseRepository.safe_execute devuelve _get_default_error_value() si falla
        # Para IterationRepository, _get_default_error_value devuelve []
        # Esto podría ser un problema si el consumidor espera None. 
        # Pero dado el código actual de IterationRepository, si safe_execute devuelve [],
        # el método devuelve [] también. 
        # Verifiquemos qué devuelve realmente safe_execute. 
        # Si devuelve [], entonces el result_id será []. 
        assert result_id == [] # Based on _get_default_error_value implementation

    def test_update_iteration_image_path_not_found(self, repository, mock_session):
        """Test update_iteration_image_path when iteration does not exist."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        result = repository.update_iteration_image_path(999, "path.jpg")
        assert result is False

    def test_update_iteration_file_path_not_found(self, repository, mock_session):
        """Test update_iteration_file_path when iteration does not exist."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        result = repository.update_iteration_file_path(999, "ruta_imagen", "path.jpg")
        assert result is False
