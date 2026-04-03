
"""
Script ejecutable (`profile_queries`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import sys
import os
import logging
from typing import Callable
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database_manager import DatabaseManager
from database.repositories.reports_repository import ReportsRepository
from database.repositories.product_repository import ProductRepository
from database.models import Producto, TrabajoLog, Fabricacion

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("QueryProfiler")

class QueryCounter:
    def __init__(self):
        self.count = 0
        self.queries = []

    def __call__(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1
        self.queries.append(statement)

def profile_method(method: Callable, name: str, *args, **kwargs):
    """Executes a method and counts SQL queries."""
    
    # Reset counter
    query_counter.count = 0
    query_counter.queries = []
    
    start_time = time.time()
    result = method(*args, **kwargs)
    duration = time.time() - start_time
    
    print(f"\n--- Profiling: {name} ---")
    print(f"Execution Time: {duration:.4f}s")
    print(f"Total Queries: {query_counter.count}")
    
    # Heuristic for N+1: query count roughly equals result count (if list) or is high
    result_count = len(result) if isinstance(result, list) else 1
    print(f"Result Items: {result_count}")
    
    if query_counter.count > 1 and result_count > 0:
        ratio = query_counter.count / result_count
        print(f"Queries per Item: {ratio:.2f}")
        if ratio >= 0.8: # Threshold for suspicion
             print("⚠️  POTENTIAL N+1 DETECTED")

    # Print first few queries for debugging
    if query_counter.count > 0:
        print("Sample Queries:")
        for q in query_counter.queries[:3]:
            print(f" - {q[:100]}...")
            
    return result

# Setup
# IMPORT CONFIG
from database.config import DatabaseConfig

print("Initializing Database...")
db_url = DatabaseConfig.get_db_url()
print(f"Using Database URL: {db_url}")
db_manager = DatabaseManager(db_url)
engine = db_manager.engine

# Attach listener
query_counter = QueryCounter()
event.listen(engine, "before_cursor_execute", query_counter)

# Initialize Repositories
reports_repo = ReportsRepository(db_manager.get_session)
product_repo = ProductRepository(db_manager.get_session)

# --- SCENARIO 1: Search Products (ReportsRepo) ---
# N+1 expected here: iteration over results doing subqueries
print("\n[Scenario 1] Searching for 'Mesa' (ReportsRepository.buscar_por_codigo)")
profile_method(reports_repo.buscar_por_codigo, "ReportsRepository.buscar_por_codigo", "Mesa", limit=10)

# --- SCENARIO 2: Orders by Product (ReportsRepo) ---
# N+1 expected here: iteration over groups doing subqueries
# Find a product with orders first
session = db_manager.get_session()
test_product = session.query(Producto).first()
if test_product:
    print(f"\n[Scenario 2] Orders for Product '{test_product.codigo}' (ReportsRepository.obtener_ordenes_por_producto)")
    profile_method(reports_repo.obtener_ordenes_por_producto, "ReportsRepository.obtener_ordenes_por_producto", test_product.codigo)
else:
    print("\n[Scenario 2] No products found to test.")

# --- SCENARIO 3: Get All Products (ProductRepo) ---
# Should be safe (1 query)
print("\n[Scenario 3] Get All Products (ProductRepository.get_all_products)")
profile_method(product_repo.get_all_products, "ProductRepository.get_all_products")

session.close()
