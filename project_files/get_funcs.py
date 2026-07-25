import ast
with open('db_manager.py', 'r') as f:
    tree = ast.parse(f.read())
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        print(node.name)
