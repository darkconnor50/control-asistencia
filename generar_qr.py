import qrcode
import os

# IP de tu servidor
IP_SERVIDOR = '10.117.1.89'
PUERTO = '5000'

sucursales = [
    {'id': '1', 'nombre': 'Sucursal Trabajo'},
    {'id': '2', 'nombre': 'Sucursal Casa'}
]

if not os.path.exists('qr_sucursales'):
    os.makedirs('qr_sucursales')

for s in sucursales:
    url = f"http://{IP_SERVIDOR}:{PUERTO}/sucursal/{s['id']}"
    qr = qrcode.make(url)
    archivo = f"qr_sucursales/QR_{s['nombre'].replace(' ', '_')}.png"
    qr.save(archivo)
    print(f"QR generado: {archivo}")
    print(f"URL: {url}")

print("\nTodos los QR fueron generados en la carpeta qr_sucursales")