import glob
import re
import os

if not os.path.exists('static/js'):
    os.makedirs('static/js')

for filepath in glob.glob('templates/*.html'):
    if 'base.html' in filepath:
        continue
        
    basename = os.path.basename(filepath).replace('.html', '')
    js_filename = f"static/js/{basename}.js"
    
    with open(filepath, 'r') as f:
        content = f.read()
        
    # Find all script tags inside {% block scripts %}
    block_start = content.find('{% block scripts %}')
    block_end = content.find('{% endblock %}', block_start)
    
    if block_start == -1 or block_end == -1:
        continue
        
    scripts_block = content[block_start + 19:block_end]
    
    # We will extract script tags that do NOT contain {{ (Jinja tags)
    script_matches = re.finditer(r'<script>(.*?)</script>', scripts_block, re.DOTALL)
    
    extracted_js = ""
    new_scripts_block = scripts_block
    
    for match in script_matches:
        script_content = match.group(1)
        if '{{' not in script_content and '{%' not in script_content:
            extracted_js += script_content + "\n\n"
            new_scripts_block = new_scripts_block.replace(match.group(0), "")
            
    if extracted_js.strip():
        with open(js_filename, 'w') as f:
            f.write(extracted_js.strip())
            
        # Add the script tag to the block
        new_scripts_block += f'\n<script src="/{js_filename}"></script>\n'
        
        # Replace block in content
        new_content = content[:block_start + 19] + new_scripts_block + content[block_end:]
        
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Extracted JS for {basename}")
        
print("JS extraction complete.")
