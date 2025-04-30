from app import app
import os

if __name__ == '__main__':
    # Obtener puerto de Railway o usar 5000 por defecto
    port = int(os.environ.get('PORT', 5000))
    
    # En desarrollo usar 0.0.0.0, en producción Railway maneja esto
    host = '0.0.0.0'
    
    app.run(
        host=host,
        port=port,
        debug=False  # Deshabilitar debug en producción
    ) 