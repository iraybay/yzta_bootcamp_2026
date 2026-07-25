import os
import glob
import re

mapping = {
    'get_db_connection': 'db_core',
    'get_all_cariler': 'cari_repository',
    'get_payment_plan': 'cari_repository',
    'get_cari_islem_history_range': 'cari_repository',
    'get_cari_detail_and_history': 'cari_repository',
    'add_cari_record': 'cari_repository',
    
    'get_dashboard_data': 'dashboard_repository',
    
    'get_stok_liste': 'stok_repository',
    'get_stok_hareketler': 'stok_repository',
    'add_stok_item': 'stok_repository',
    'add_stok': 'stok_repository',
    'add_stok_hareket': 'stok_repository',
    
    'get_fatura_irsaliye_list': 'fatura_repository',
    'add_fatura_irsaliye_full': 'fatura_repository',
    'update_fatura_status': 'fatura_repository',
    'delete_fatura_record': 'fatura_repository',
    'add_fatura_record': 'fatura_repository',
}

for filepath in glob.glob('router/*.py'):
    with open(filepath, 'r') as f:
        content = f.read()
    
    if 'db_manager' in content:
        # First remove import db_manager
        content = re.sub(r'^import db_manager$', '', content, flags=re.MULTILINE)
        
        # Collect which repos we need in this file
        needed_repos = set()
        for func, repo in mapping.items():
            if f'db_manager.{func}' in content:
                needed_repos.add(repo)
        
        if needed_repos:
            import_str = ""
            for repo in needed_repos:
                funcs_in_this_repo = [f for f, r in mapping.items() if r == repo and f'db_manager.{f}' in content]
                import_str += f"from repositories.{repo} import {', '.join(funcs_in_this_repo)}\n"
            
            # Add imports at top
            content = import_str + content
            
            # Replace db_manager.func with func
            for func in mapping.keys():
                content = content.replace(f'db_manager.{func}', func)
        
        with open(filepath, 'w') as f:
            f.write(content)

print("Imports refactored.")
