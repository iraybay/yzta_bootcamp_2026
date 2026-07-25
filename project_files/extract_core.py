import ast

with open('db_manager.py', 'r') as f:
    code = f.read()

tree = ast.parse(code)
functions_to_extract = ['get_db_connection', 'init_db', '_seed_core_data', '_seed_extra_stok_fatura']
extracted_code = ["import sqlite3\nimport os\nimport datetime\n\nDB_FILE = 'bulutis.db'\n\n"]

for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in functions_to_extract:
        # We need the source segment. Fortunately Python 3.8+ AST has get_source_segment
        extracted_code.append(ast.get_source_segment(code, node))
        extracted_code.append("\n\n")

with open('repositories/db_core.py', 'w') as f:
    f.write("".join(extracted_code))

print("Extraction complete.")
