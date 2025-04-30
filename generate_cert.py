from OpenSSL import crypto
import os

def generate_self_signed_cert():
    # Crear directorio ssl si no existe
    if not os.path.exists('ssl'):
        os.makedirs('ssl')

    # Generar key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 4096)

    # Generar certificado
    cert = crypto.X509()
    cert.get_subject().CN = "localhost"
    cert.get_subject().O = "Cafeteria System"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Válido por un año
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)

    # Agregar nombres alternativos
    alt_names = [
        "DNS:localhost",
        "DNS:192.168.100.63",
        "IP:192.168.100.63",
        "IP:127.0.0.1"
    ]
    
    san_extension = crypto.X509Extension(
        b"subjectAltName",
        False,
        ", ".join(alt_names).encode()
    )
    cert.add_extensions([san_extension])

    cert.sign(k, 'sha256')

    # Guardar certificado y llave privada
    with open("ssl/cert.pem", "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    with open("ssl/key.pem", "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

if __name__ == '__main__':
    # Eliminar certificados existentes
    if os.path.exists('ssl/cert.pem'):
        os.remove('ssl/cert.pem')
    if os.path.exists('ssl/key.pem'):
        os.remove('ssl/key.pem')
        
    generate_self_signed_cert()
    print("Certificados generados en el directorio 'ssl'") 