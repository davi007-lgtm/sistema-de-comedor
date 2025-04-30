from app import app
from pyngrok import ngrok
import threading
import webbrowser

def run_flask():
    app.run(host='127.0.0.1', port=5000)

if __name__ == '__main__':
    # Iniciar Flask en un hilo separado
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Crear túnel HTTPS
    public_url = ngrok.connect(5000)
    print(f"\n* Ngrok tunnel available at: {public_url}")
    print("* Ctrl+C to quit")
    
    # Mantener el programa corriendo
    try:
        # Bloquear el hilo principal
        ngrok_process = ngrok.get_ngrok_process()
        ngrok_process.proc.wait()
    except KeyboardInterrupt:
        print("* Stopping ngrok tunnel")
        ngrok.kill() 