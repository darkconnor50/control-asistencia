import gspread
from google.oauth2.service_account import Credentials
import uuid
import json
import os
import subprocess
from datetime import datetime

# Configuración
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

ID_HOJA = '159p8vlPVs0Nh1yMjuXdFhUGclXjT6e9BalQ2H8No6dA'
ARCHIVO_UUID = 'dispositivo.json'

# Conectar con Google Sheets
creds = Credentials.from_service_account_file('credenciales.json', scopes=SCOPES)
cliente = gspread.authorize(creds)
hoja = cliente.open_by_key(ID_HOJA)

hoja_empleados = hoja.worksheet('EMPLEADOS')
hoja_sucursales = hoja.worksheet('SUCURSALES')
hoja_registros = hoja.worksheet('REGISTROS')

# Obtener red WiFi actual
def obtener_wifi_actual():
    result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], capture_output=True, text=True)
    for linea in result.stdout.split('\n'):
        if 'SSID' in linea and 'AP BSSID' not in linea and 'BSSID' not in linea:
            return linea.split(':')[1].strip()
    return None

# Obtener o crear UUID del dispositivo
def obtener_uuid():
    if os.path.exists(ARCHIVO_UUID):
        with open(ARCHIVO_UUID, 'r') as f:
            datos = json.load(f)
            return datos['uuid']
    else:
        nuevo_uuid = str(uuid.uuid4())
        with open(ARCHIVO_UUID, 'w') as f:
            json.dump({'uuid': nuevo_uuid}, f)
        return nuevo_uuid

# Verificar si el empleado ya está registrado
def buscar_empleado(id_dispositivo):
    registros = hoja_empleados.get_all_records()
    for r in registros:
        if r['ID_DISPOSITIVO'] == id_dispositivo:
            return r['NOMBRE']
    return None

# Registrar nuevo empleado
def registrar_empleado(id_dispositivo):
    nombre = input("Bienvenido. Escribe tu nombre completo: ")
    hoja_empleados.append_row([id_dispositivo, nombre, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    print(f"Empleado {nombre} registrado correctamente.")
    return nombre

# Obtener lista de sucursales
def obtener_sucursales():
    return hoja_sucursales.get_all_records()

# Registrar entrada o salida
def registrar_asistencia(nombre, sucursal, tipo):
    ahora = datetime.now()
    hoja_registros.append_row([
        nombre,
        sucursal,
        ahora.strftime('%Y-%m-%d'),
        ahora.strftime('%H:%M:%S'),
        tipo
    ])
    print(f"{tipo} registrada para {nombre} en {sucursal} a las {ahora.strftime('%H:%M:%S')}")

# FLUJO PRINCIPAL
print("=== CONTROL DE ASISTENCIA ===")

# Detectar WiFi actual
wifi_actual = obtener_wifi_actual()
print(f"Red WiFi detectada: {wifi_actual}")

# Obtener sucursales y validar WiFi
sucursales = obtener_sucursales()
sucursal_actual = None

for s in sucursales:
    if s['WIFI'] == wifi_actual:
        sucursal_actual = s['NOMBRE_SUCURSAL']
        break

if not sucursal_actual:
    print(f"\nAcceso denegado. La red '{wifi_actual}' no corresponde a ninguna sucursal registrada.")
else:
    print(f"Sucursal detectada: {sucursal_actual}")
    
    id_dispositivo = obtener_uuid()
    nombre = buscar_empleado(id_dispositivo)

    if not nombre:
        nombre = registrar_empleado(id_dispositivo)

    print(f"\nBienvenido, {nombre}")
    
    tipo = input("\n¿Entrada o Salida? (E/S): ").upper()
    tipo = "ENTRADA" if tipo == "E" else "SALIDA"
    
    registrar_asistencia(nombre, sucursal_actual, tipo)