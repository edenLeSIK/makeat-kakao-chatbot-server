from app import app
from app.models import initialize_database 

if __name__ == "__main__":
    initialize_database()
    app.run(host='0.0.0.0', port=5000, debug=True)
