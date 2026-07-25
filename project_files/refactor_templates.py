import glob
import re
import os

for filepath in glob.glob('templates/*.html'):
    if 'base.html' in filepath:
        continue
        
    with open(filepath, 'r') as f:
        content = f.read()
        
    # Check if already refactored
    if '{% extends' in content:
        continue
        
    # Extract Title
    title_match = re.search(r'<title>(.*?)</title>', content)
    title = title_match.group(1) if title_match else "Bulutİş ERP"
    
    # Extract Extra Styles (between <style> and </style> in head)
    # Be careful not to grab too much, only first style tag usually in head.
    style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    extra_style = style_match.group(1) if style_match else ""
    
    # Extract Content
    # We want everything inside <div class="app-container">
    # Note: Using regex for this is tricky due to nested divs. 
    # Let's find the first <header class="app-header"> and everything down to before the last <script>
    
    # We'll locate the `<div class="app-container">` and the first `<script>` near the end of body.
    app_container_start = content.find('<div class="app-container">')
    if app_container_start == -1:
        # Some might not have exactly that spacing.
        match = re.search(r'<div[^>]*class="[^"]*app-container[^"]*"[^>]*>', content)
        if match:
            app_container_start = match.start()
        else:
            print(f"Skipping {filepath}, no app-container found")
            continue
            
    # To find the end of app container, we assume it's just before the last <script> tag which belongs to the page
    # A better way is to split by </header> ... actually, the <header> is inside app-container.
    
    script_start = content.rfind('<script>')
    if script_start == -1 or script_start < app_container_start:
        script_start = content.rfind('<script ')
        if script_start == -1 or script_start < app_container_start:
            # If no script at the end, just go up to </body>
            script_start = content.find('</body>')

    content_part = content[app_container_start:script_start].strip()
    
    # Remove the outermost <div class="app-container"> and the matching closing </div>
    # Usually it's the first div and the last closing div in this block
    if content_part.startswith('<div class="app-container">'):
        content_part = content_part[len('<div class="app-container">'):]
        if content_part.endswith('</div>'):
            content_part = content_part[:-6]
    
    # Extract scripts
    body_end = content.find('</body>')
    script_part = content[script_start:body_end].strip() if script_start != -1 and body_end != -1 else ""

    # Check if there is the theme toggle script in the extracted script part, if so, remove it
    theme_script_pattern = r'<script>\s*\(function\(\)\s*\{\s*const savedTheme = localStorage.getItem\(\'theme\'\).*?\}\)\(\);\s*</script>'
    if re.search(theme_script_pattern, script_part, re.DOTALL):
        script_part = re.sub(theme_script_pattern, '', script_part, flags=re.DOTALL)
        
    # Same for the body theme toggle inside the template
    if re.search(theme_script_pattern, content_part, re.DOTALL):
        content_part = re.sub(theme_script_pattern, '', content_part, flags=re.DOTALL)

    new_content = f"{{% extends 'base.html' %}}\n\n"
    new_content += f"{{% block title %}}{title}{{% endblock %}}\n\n"
    
    if extra_style.strip():
        new_content += f"{{% block extra_head %}}\n<style>\n{extra_style}\n</style>\n{{% endblock %}}\n\n"
        
    new_content += f"{{% block content %}}\n{content_part}\n{{% endblock %}}\n\n"
    
    if script_part.strip():
        new_content += f"{{% block scripts %}}\n{script_part}\n{{% endblock %}}\n"

    # Backup the original file
    os.rename(filepath, filepath + ".bak")
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print(f"Refactored {filepath}")
