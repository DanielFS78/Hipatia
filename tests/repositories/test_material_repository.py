import pytest
from unittest.mock import MagicMock, call
from sqlalchemy.exc import IntegrityError
from database.repositories.material_repository import MaterialRepository
from core.dtos import MaterialDTO, MaterialStatsDTO

# =================================================================================
# UNIT TESTS (Mocks)
# =================================================================================

@pytest.mark.unit
def test_get_all_materials_returns_dtos():
    """Verify that get_all_materials returns a list of MaterialDTO objects."""
    # Mock the session factory handling context manager
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    
    repo = MaterialRepository(mock_factory)
    
    # Mocking the query result
    mock_material = MagicMock()
    mock_material.id = 1
    mock_material.codigo_componente = "MAT001"
    mock_material.descripcion_componente = "Test Material"
    
    # Configure chained mock for query().order_by().all()
    mock_query = mock_session.query.return_value
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = [mock_material]
    
    result = repo.get_all_materials()
    
    assert len(result) == 1
    assert isinstance(result[0], MaterialDTO)
    assert result[0].id == 1
    assert result[0].codigo_componente == "MAT001"
    assert result[0].descripcion_componente == "Test Material"

@pytest.mark.unit
def test_get_problematic_components_stats_returns_dtos():
    """Verify that get_problematic_components_stats returns MaterialStatsDTO objects."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    
    repo = MaterialRepository(mock_factory)
    
    # Mock row result
    mock_row = MagicMock()
    mock_row.codigo_componente = "MAT001"
    mock_row.frecuencia = 5
    
    # Configure chained mock for complex query
    mock_query = mock_session.query.return_value
    mock_query.join.return_value = mock_query
    mock_query.group_by.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [mock_row]
    
    result = repo.get_problematic_components_stats()
    
    assert len(result) == 1
    assert isinstance(result[0], MaterialStatsDTO)
    assert result[0].codigo_componente == "MAT001"
    assert result[0].frecuencia == 5

@pytest.mark.unit
def test_add_material_updates_description_if_exists():
    """Verify that add_material updates description if material already exists."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    
    repo = MaterialRepository(mock_factory)
    
    # Existing material with OLD description
    mock_existing = MagicMock()
    mock_existing.id = 10
    mock_existing.descripcion_componente = "Old Description"
    
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_existing
    
    result_id = repo.add_material("EXISTING_CODE", "New Description")
    
    assert result_id == 10
    assert mock_existing.descripcion_componente == "New Description"

@pytest.mark.unit
def test_add_material_integrity_error_handling():
    """Verify retry logic on IntegrityError."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    
    repo = MaterialRepository(mock_factory)
    
    # First query returns None (not found)
    mock_session.query.return_value.filter_by.return_value.first.side_effect = [None, MagicMock(id=99)]
    
    # Commit raises IntegrityError
    mock_session.commit.side_effect = IntegrityError(None, None, Exception("Duplicate"))
    
    # Second session for validation check (retry)
    mock_session_2 = MagicMock()
    # We need to mock get_session returning a new session
    # But base_repository uses session_factory(), so we can use side_effect on factory
    # repo.session_factory is mock_factory
    # Call 1: Context manager for safe_execute. Call 2: get_session() in catch block.
    # However, safe_execute uses `with self.get_session() as session` NO wait, base uses `session = self.get_session()`
    # Let's inspect base_repository implementation logic to mock correctly.
    # Logic in add_material: safe_execute -> _operation -> session.add -> session.flush
    # If IntegrityError, catch block calls self.get_session() again.
    
    # Simpler approach: Mock safe_execute to raise IntegrityError, and test catch block logic? 
    # But safe_execute catches generic Exception. add_material has specific try/except around safe_execute.
    # Review `add_material`:
    # try: return self.safe_execute(_operation)
    # except IntegrityError: ...
    
    # safe_execute usually suppresses exceptions and returns default value. 
    # UNLESS we mock safe_execute to RAISE IntegrityError.
    
    repo.safe_execute = MagicMock(side_effect=IntegrityError(None, None, Exception("Duplicate")))
    
    # Mock specific session for the catch block
    mock_session_retry = MagicMock()
    mock_factory.side_effect = [mock_session, mock_session_retry] # Reset side effect if needed or add to existing
    
    mock_existing = MagicMock()
    mock_existing.id = 99
    mock_session_retry.query.return_value.filter_by.return_value.first.return_value = mock_existing
    
    # Re-instantiate to attach fresh mocks if needed, or just set side_effect on factory
    repo.session_factory.side_effect = [mock_session_retry] 
    
    result_id = repo.add_material("DUP_CODE", "Desc")
    
    assert result_id == 99

@pytest.mark.unit
def test_update_material_not_found():
    """Verify update_material returns False if material does not exist."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    
    success = repo.update_material(999, "CODE", "Desc")
    assert success is False

@pytest.mark.unit
def test_update_material_duplicate_code():
    """Verify update_material returns False if new code is taken by another material."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_material = MagicMock(id=1, codigo_componente="OLD_CODE")
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_material
    
    # Mock duplicate check finding another material
    mock_existing = MagicMock(id=2)
    mock_session.query.return_value.filter.return_value.first.return_value = mock_existing
    
    success = repo.update_material(1, "NEW_CODE_TAKEN", "Desc")
    assert success is False

@pytest.mark.unit
def test_link_material_to_product_success():
    """Verify successful linking of material to product."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_prod = MagicMock()
    mock_prod.materiales = []
    mock_mat = MagicMock()
    
    # First query for Product, Second for Material
    mock_session.query.return_value.filter_by.return_value.first.side_effect = [mock_prod, mock_mat]
    
    success = repo.link_material_to_product("PROD-01", 1)
    
    assert success is True
    assert mock_mat in mock_prod.materiales

@pytest.mark.unit
def test_link_material_to_product_already_exists():
    """Verify successful linking (idempotent) if already linked."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_mat = MagicMock()
    mock_prod = MagicMock()
    mock_prod.materiales = [mock_mat] # Already has it
    
    mock_session.query.return_value.filter_by.return_value.first.side_effect = [mock_prod, mock_mat]
    
    success = repo.link_material_to_product("PROD-01", 1)
    
    assert success is True
    # Should not append again
    assert len(mock_prod.materiales) == 1

@pytest.mark.unit
def test_unlink_material_from_product_success():
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_mat = MagicMock()
    mock_prod = MagicMock()
    mock_prod.materiales = [mock_mat]
    
    mock_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = mock_prod
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_mat
    
    success = repo.unlink_material_from_product("PROD-01", 1)
    
    assert success is True
    assert mock_mat not in mock_prod.materiales

@pytest.mark.unit
def test_mock_default_error_value():
    """Verify default error value."""
    # Assuming helper method on instance, not testing BaseRepository logic directly but ensure override works if present
    repo = MaterialRepository(MagicMock())
    assert repo._get_default_error_value() is None

@pytest.mark.unit
def test_add_material_generic_exception():
    """Verify generic exception handling in add_material."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    # Mock safe_execute to raise Exception directly, OR better:
    # safe_execute catches generic exceptions, but add_material HAS a try/except that catches SafeExecute?
    # No, safe_execute catches exceptions. add_material calls safe_execute. 
    # If safe_execute fails, it returns None.
    # But add_material HAS logic OUTSIDE safe_execute?
    # No, looking at code:
    # try: return self.safe_execute(_operation) except IntegrityError...
    # The IntegrityError exception is raised BY safe_execute if not caught inside, BUT safe_execute DOES catch Exception.
    # Ah, safe_execute logic: try: operation() except SQLAlchemyError... except Exception...
    # So safe_execute usually returns None on error.
    # However, IntegrityError is a SQLAlchemyError.
    
    # If we want to simulate the "except Exception" clause in add_material:
    # It catches generic exception at the end of the method!
    # "except Exception as e: ... return None"
    # To reach that, safe_execute must RAISE an exception?
    # Or maybe the code inside add_material RAISES it?
    # But add_material calls safe_execute.
    # If safe_execute catches everything, add_material's outer try/except is redundant unless safe_execute raises.
    # Let's verify safe_execute implementation via thought or assumption. 
    # Usually safe_execute swallows errors.
    # If we want to hit lines 105-107 in material_repository (generic exception),
    # we need safe_execute to raise or something outside it to raise.
    # Re-reading code:
    # try: return self.safe_execute(_operation) except IntegrityError... except Exception...
    # This implies that safe_execute MIGHT propagate or raise.
    # But `BaseRepository.safe_execute` shown earlier catches Exception and returns default error value.
    # So `self.safe_execute` will return None, NOT raise.
    # So lines 105-107 might be dead code unless safe_execute implementation changed or I misunderstood.
    # OR if mock raises Exception when called?
    
    repo.safe_execute = MagicMock(side_effect=Exception("Unexpected"))
    result = repo.add_material("Error", "Desc")
    assert result is None

@pytest.mark.unit
def test_update_material_success():
    """Verify successful material update."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_material = MagicMock(id=1, codigo_componente="OLD")
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_material
    
    # Mock duplicate check: No conflict
    mock_session.query.return_value.filter.return_value.first.return_value = None
    
    success = repo.update_material(1, "NEW", "Desc")
    assert success is True
    assert mock_material.codigo_componente == "NEW"

@pytest.mark.unit
def test_link_material_to_product_not_found():
    """Verify failure to link if product or material not found."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    # Simulate Product found, Material NOT found
    mock_session.query.return_value.filter_by.return_value.first.side_effect = [MagicMock(), None]
    
    success = repo.link_material_to_product("PROD", 999)
    assert success is False

@pytest.mark.unit
def test_unlink_material_from_product_not_linked():
    """Verify unlink returns True if not linked (idempotent)."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_prod = MagicMock()
    mock_prod.materiales = [] # Empty
    mock_mat = MagicMock()
    
    mock_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = mock_prod
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_mat
    
    success = repo.unlink_material_from_product("PROD", 1)
    assert success is True

@pytest.mark.unit
def test_link_material_to_iteration_success():
    """Verify linking material to iteration."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_iter = MagicMock()
    mock_iter.materiales = []
    mock_mat = MagicMock()
    
    mock_session.query.return_value.filter_by.return_value.first.side_effect = [mock_iter, mock_mat]
    
    success = repo.link_material_to_iteration(1, 100)
    assert success is True
    assert mock_mat in mock_iter.materiales

@pytest.mark.unit
def test_link_material_to_iteration_not_found():
    """Verify linking fails if entities not found."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    # Iteration not found
    mock_session.query.return_value.filter_by.return_value.first.side_effect = [None, MagicMock()]
    
    success = repo.link_material_to_iteration(999, 100)
    assert success is False

@pytest.mark.unit
def test_delete_material_link_from_iteration_success():
    """Verify unlinking material from iteration."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_mat = MagicMock()
    mock_iter = MagicMock()
    mock_iter.materiales = [mock_mat]
    
    mock_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = mock_iter
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_mat
    
    success = repo.delete_material_link_from_iteration(1, 100)
    assert success is True
    assert mock_mat not in mock_iter.materiales

# ... (Integration tests remain same)

@pytest.mark.unit
def test_add_material_integrity_error_but_lookup_fails():
    """Verify IntegrityError handling when subsequent lookup also fails (returns None)."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    # First query None
    mock_session.query.return_value.filter_by.return_value.first.side_effect = [None]
    # Commit raises IntegrityError
    mock_session.commit.side_effect = IntegrityError(None, None, Exception("Duplicate"))
    
    # Retry session
    mock_session_retry = MagicMock()
    mock_factory.side_effect = [mock_session, mock_session_retry]
    repo.session_factory.side_effect = [mock_session_retry]
    
    # Retry query ALSO returns None
    mock_session_retry.query.return_value.filter_by.return_value.first.return_value = None
    
    repo.safe_execute = MagicMock(side_effect=IntegrityError(None, None, Exception("Duplicate")))
    
    # We need to ensure we hit the exact structure of add_material which manually handles IntegrityError
    # BUT we mocked safe_execute in the previous test which bypasses the real logic partially if we aren't careful.
    # Actually, in strict unit testing of the METHOD logic, we shouldn't mock the method `safe_execute` if we want to test the `except IntegrityError` block AROUND it.
    # However, `safe_execute` is called inside `add_material`.
    # `try: return self.safe_execute(_operation) except IntegrityError...`
    # So mocking `safe_execute` to raise `IntegrityError` IS the correct way to reach the except block.
    
    result = repo.add_material("FAIL_CODE", "Desc")
    assert result is None

@pytest.mark.unit
def test_unlink_material_from_product_product_not_found():
    """Verify unlink returns False if product not found."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    # Product None, Material ignored (lazy eval or second query)
    mock_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = None
    mock_session.query.return_value.filter_by.return_value.first.return_value = MagicMock() # Material found
    
    success = repo.unlink_material_from_product("MISSING_PROD", 1)
    assert success is False

@pytest.mark.unit
def test_unlink_material_from_product_material_not_found():
    """Verify unlink returns True if material not found (idempotent)."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_prod = MagicMock()
    # Product found, Material None
    mock_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = mock_prod
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    
    success = repo.unlink_material_from_product("PROD", 999)
    # Code says: if not material: return True
    assert success is True

@pytest.mark.unit
def test_link_material_to_iteration_already_linked():
    """Verify link iteration returns True if already linked."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_mat = MagicMock()
    mock_iter = MagicMock()
    mock_iter.materiales = [mock_mat]
    
    mock_session.query.return_value.filter_by.return_value.first.side_effect = [mock_iter, mock_mat]
    
    success = repo.link_material_to_iteration(1, 100)
    assert success is True
    # Ensure did not append again
    assert len(mock_iter.materiales) == 1

@pytest.mark.unit
def test_delete_material_link_from_iteration_iteration_not_found():
    """Verify delete link returns False if iteration not found."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = None
    mock_session.query.return_value.filter_by.return_value.first.return_value = MagicMock()
    
    success = repo.delete_material_link_from_iteration(999, 100)
    assert success is False

@pytest.mark.unit
def test_delete_material_link_from_iteration_material_not_found():
    """Verify delete link returns True if material not found."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    
    success = repo.delete_material_link_from_iteration(1, 999)
    assert success is True

@pytest.mark.unit
def test_delete_material_link_from_iteration_not_linked():
    """Verify delete link returns True if not linked."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    repo = MaterialRepository(mock_factory)
    
    mock_mat = MagicMock()
    mock_iter = MagicMock()
    mock_iter.materiales = [] # Empty
    
    mock_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = mock_iter
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_mat
    
    success = repo.delete_material_link_from_iteration(1, 100)
    assert success is True

# =================================================================================
# INTEGRATION TESTS (Real DB via Fixtures)
# =================================================================================

@pytest.mark.integration
def test_add_and_retrieve_material(repos):
    """Test adding a material and retrieving it via get_all_materials."""
    repo = repos['material']
    
    # Add material
    start_count = len(repo.get_all_materials())
    repo.add_material("INT_MAT_001", "Integration Material 1")
    
    # Retrieve
    materials = repo.get_all_materials()
    assert len(materials) == start_count + 1
    
    # Verify content
    new_material = next((m for m in materials if m.codigo_componente == "INT_MAT_001"), None)
    assert new_material is not None
    assert new_material.descripcion_componente == "Integration Material 1"
    assert isinstance(new_material, MaterialDTO)

@pytest.mark.integration
def test_add_duplicate_material_returns_existing_id(repos):
    """Test that adding a duplicate material returns the existing ID."""
    repo = repos['material']
    
    # Add first time
    id1 = repo.add_material("DUP_MAT_001", "Duplicate Material")
    assert id1 is not None
    
    # Add second time
    id2 = repo.add_material("DUP_MAT_001", "Duplicate Material")
    assert id2 == id1

@pytest.mark.integration
def test_update_material(repos):
    """Test updating a material's code and description."""
    repo = repos['material']
    
    material_id = repo.add_material("UPD_MAT_001", "Original Description")
    
    success = repo.update_material(material_id, "UPD_MAT_001_V2", "Updated Description")
    assert success is True
    
    materials = repo.get_all_materials()
    updated_material = next((m for m in materials if m.id == material_id), None)
    
    assert updated_material.codigo_componente == "UPD_MAT_001_V2"
    assert updated_material.descripcion_componente == "Updated Description"

# =================================================================================
# SETUP TESTS
# =================================================================================

@pytest.mark.setup
def test_material_table_structure(in_memory_db_manager):
    """Verify the materials table exists and has correct columns."""
    cursor = in_memory_db_manager.conn.cursor()
    cursor.execute("PRAGMA table_info(materiales)")
    columns = {row[1] for row in cursor.fetchall()}
    
    assert 'id' in columns
    assert 'codigo_componente' in columns
    assert 'descripcion_componente' in columns
