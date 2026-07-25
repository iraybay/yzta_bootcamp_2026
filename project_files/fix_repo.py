import ast

with open('db_manager.py', 'r') as f:
    code = f.read()

tree = ast.parse(code)
func_code = ""
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == 'get_monthly_liquidity_data':
        func_code = ast.get_source_segment(code, node)
        break

if func_code:
    with open('repositories/kasa_repository.py', 'a') as f:
        f.write("\n\n")
        f.write(func_code)
    print("Added get_monthly_liquidity_data to kasa_repository.py")
else:
    print("Function not found!")
