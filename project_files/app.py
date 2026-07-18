import os
from flask import Flask
import db_manager
import router

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Initialize SQLite database schema and mock records
db_manager.init_db()

# Register modular blueprints from router directory
router.register_routers(app)

if __name__ == '__main__':
    # Run server on port 5002 to prevent collision and macOS AirPlay collision
    app.run(host='0.0.0.0', port=5002, debug=True)
