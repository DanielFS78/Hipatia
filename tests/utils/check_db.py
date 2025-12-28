import sqlite3

print("="*70)
print("DIAGNÓSTICO DE BASE DE DATOS: montaje.db")
print("="*70)

conn = sqlite3.connect('montaje.db')
cursor = conn.cursor()

# 1. Verificar versión del esquema
print("\n[1] VERSIÓN DEL ESQUEMA:")
cursor.execute("SELECT value FROM db_info WHERE key = 'schema_version'")
version = cursor.fetchone()
print(f"    Versión actual: {version[0] if version else 'NO DEFINIDA'}")

# 2. Verificar estructura de tabla trabajadores
print("\n[2] ESTRUCTURA DE TABLA 'trabajadores':")
cursor.execute("PRAGMA table_info(trabajadores)")
cols = cursor.fetchall()
for col in cols:
    print(f"    {col[1]:20s} {col[2]:10s} {'NOT NULL' if col[3] else 'NULL':8s} DEFAULT: {col[4]}")

# 3. Verificar datos de trabajadores
print("\n[3] TRABAJADORES EN LA BASE DE DATOS:")
cursor.execute("SELECT id, nombre_completo, tipo_trabajador FROM trabajadores")
workers = cursor.fetchall()
if workers:
    for w in workers:
        print(f"    ID:{w[0]:3d} | Nombre: {w[1]:30s} | Nivel: {w[2]}")
else:
    print("    ⚠️ NO HAY TRABAJADORES EN LA BD")

# 4. Verificar estructura de preprocesos
print("\n[4] ESTRUCTURA DE TABLA 'preprocesos':")
cursor.execute("PRAGMA table_info(preprocesos)")
prep_cols = cursor.fetchall()
for col in prep_cols:
    print(f"    {col[1]:20s} {col[2]:10s} {'NOT NULL' if col[3] else 'NULL':8s} DEFAULT: {col[4]}")

# 5. Verificar productos con subfabricaciones
print("\n[5] MUESTRA DE PRODUCTOS CON SUBFABRICACIONES:")
cursor.execute("""
    SELECT p.codigo, p.descripcion, p.tipo_trabajador, 
           COUNT(s.id) as num_subfabs
    FROM productos p
    LEFT JOIN subfabricaciones s ON p.codigo = s.producto_codigo
    WHERE p.tiene_subfabricaciones = 1
    GROUP BY p.codigo
    LIMIT 5
""")
prods = cursor.fetchall()
for prod in prods:
    print(f"    {prod[0]:15s} | {prod[1]:40s} | Nivel req: {prod[2]} | Subfabs: {prod[3]}")

# 6. Verificar niveles de habilidad en subfabricaciones
print("\n[6] DISTRIBUCIÓN DE NIVELES DE HABILIDAD EN SUBFABRICACIONES:")
cursor.execute("""
    SELECT tipo_trabajador, COUNT(*) as cantidad
    FROM subfabricaciones
    GROUP BY tipo_trabajador
    ORDER BY tipo_trabajador
""")
skill_dist = cursor.fetchall()
for level, count in skill_dist:
    print(f"    Nivel {level}: {count} subfabricaciones")

# 7. Verificar si hay pilas guardadas
print("\n[7] PILAS GUARDADAS:")
cursor.execute("SELECT COUNT(*) FROM pilas")
pila_count = cursor.fetchone()[0]
print(f"    Total de pilas: {pila_count}")

if pila_count > 0:
    cursor.execute("SELECT id, nombre, fecha_creacion FROM pilas ORDER BY id DESC LIMIT 3")
    pilas = cursor.fetchall()
    print("    Últimas 3 pilas:")
    for p in pilas:
        print(f"      ID:{p[0]:3d} | {p[1]:30s} | {p[2]}")

conn.close()

print("\n" + "="*70)
print("DIAGNÓSTICO COMPLETADO")
print("="*70)