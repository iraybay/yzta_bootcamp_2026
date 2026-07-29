import os
import sys
import webbrowser
from flask import Flask
import db_manager
import router

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

static_folder = os.path.join(base_dir, 'static')
template_folder = os.path.join(base_dir, 'templates')

app = Flask(__name__, 
            static_folder=static_folder,
            template_folder=template_folder)

# Initialize SQLite database schema and mock records
db_manager.init_db()

# Register modular blueprints from router directory
router.register_routers(app)

if __name__ == '__main__':
    port = 5002
    # Open browser automatically if running as binary executable
    if getattr(sys, 'frozen', False):
        webbrowser.open(f'http://127.0.0.1:{port}')
    
    # Run server on port 5002 to prevent collision and macOS AirPlay collision
    app.run(host='0.0.0.0', port=port, debug=not getattr(sys, 'frozen', False))

