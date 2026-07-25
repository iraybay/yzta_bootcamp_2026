with open('templates/kasa_detay.html', 'r') as f:
    lines = f.readlines()

div_count = 0
for i, line in enumerate(lines):
    if '{% block content %}' in line:
        div_count = 0
    if '{% block scripts %}' in line:
        break
        
    div_count += line.count('<div') - line.count('</div')
    
    # Also consider <section>
    
print("Unmatched divs at end of block content:", div_count)
