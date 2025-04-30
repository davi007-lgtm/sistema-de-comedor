from app import app

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',  # Permite acceso desde cualquier IP en la red local
        port=5000,
        debug=True
    ) 