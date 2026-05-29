from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Debug mode controlled by environment variable
    debug_mode = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(host='0.0.0.0', debug=debug_mode, port=8888)
