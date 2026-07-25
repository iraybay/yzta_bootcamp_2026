import ast

with open('db_manager.py', 'r') as f:
    code = f.read()

tree = ast.parse(code)
code_segments = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        code_segments[node.name] = ast.get_source_segment(code, node)

groups = {
    'cari_repository.py': ['get_all_cariler', 'get_cari_detail_and_history', 'get_payment_plan', 'add_cari_record', 'get_cari_islem_history_range'],
    'kasa_repository.py': ['get_kasa_banka_accounts', 'get_account_detail_and_history', 'add_kasa_banka_account_record', 'add_kasa_banka_transaction_record', 'get_kasa_banka_islem_history', 'get_monthly_liquidity_data', 'add_kasa_transaction'],
    'fatura_repository.py': ['add_fatura_record', 'get_fatura_irsaliye_list', 'add_fatura_irsaliye_full', 'update_fatura_status', 'delete_fatura_record'],
    'stok_repository.py': ['add_stok_item', 'get_stok_liste', 'add_stok', 'get_stok_hareketler', 'add_stok_hareket'],
    'dashboard_repository.py': ['get_dashboard_data']
}

header = "from repositories.db_core import get_db_connection\nimport datetime\n\n"

for filename, funcs in groups.items():
    with open(f"repositories/{filename}", 'w') as f:
        f.write(header)
        for func in funcs:
            if func in code_segments:
                f.write(code_segments[func])
                f.write("\n\n")

print("Repository extraction complete.")
