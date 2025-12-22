# src/app.py - Simple runner file
from create_app import create_app

# Create the application instance for running
app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config['DEBUG'])