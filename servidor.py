from flask import Flask, request, jsonify, render_template_string
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

app = Flask(__name__)

# Configuración Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

ID_HOJA = '159p8vlPVs0Nh1yMjuXdFhUGclXjT6e9BalQ2H8No6dA'

creds = Credentials.from_service_account_file('credenciales.json', scopes=SCOPES)
cliente = gspread.authorize(creds)
hoja = cliente.open_by_key(ID_HOJA)

hoja_empleados = hoja.worksheet('EMPLEADOS')
hoja_sucursales = hoja.worksheet('SUCURSALES')
hoja_registros = hoja.worksheet('REGISTROS')

# Página principal al escanear QR
@app.route('/sucursal/<id_sucursal>')
def pagina_sucursal(id_sucursal):
    sucursales = hoja_sucursales.get_all_records()
    sucursal = next((s for s in sucursales if str(s['ID_SUCURSAL']) == id_sucursal), None)
    
    if not sucursal:
        return "Sucursal no encontrada", 404

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Control de Asistencia</title>
        <style>
            body {{ font-family: Arial; text-align: center; padding: 30px; background: #f0f0f0; }}
            h1 {{ color: #333; }}
            h2 {{ color: #666; }}
            input {{ width: 80%; padding: 12px; margin: 10px; font-size: 16px; border-radius: 8px; border: 1px solid #ccc; }}
            button {{ width: 80%; padding: 15px; margin: 10px; font-size: 18px; border: none; border-radius: 8px; cursor: pointer; color: white; }}
            .entrada {{ background: #28a745; }}
            .salida {{ background: #dc3545; }}
        </style>
    </head>
    <body>
        <h1>Control de Asistencia</h1>
        <h2>{sucursal['NOMBRE_SUCURSAL']}</h2>
<div id="vista-nombre" style="display:none">
    <p>Primera vez aquí. Escribe tu nombre:</p>
    <input type="text" id="nombre" placeholder="Tu nombre completo" />
    <button class="entrada" onclick="guardarNombre()">GUARDAR</button>
</div>
<div id="vista-principal" style="display:none">
    <p id="saludo"></p>
    <button class="entrada" onclick="registrar('ENTRADA')">ENTRADA</button>
    <button class="salida" onclick="registrar('SALIDA')">SALIDA</button>
</div>
<p id="mensaje"></p>
<script>
    function generarUUID() {{
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {{
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        }});
    }}

    let uuid = localStorage.getItem('uuid_dispositivo');
    if (!uuid) {{
        uuid = generarUUID();
        localStorage.setItem('uuid_dispositivo', uuid);
    }}

    let nombreGuardado = localStorage.getItem('nombre_empleado');
    if (!nombreGuardado) {{
        document.getElementById('vista-nombre').style.display = 'block';
    }} else {{
        document.getElementById('saludo').innerText = 'Hola, ' + nombreGuardado;
        document.getElementById('vista-principal').style.display = 'block';
    }}

    function guardarNombre() {{
        const nombre = document.getElementById('nombre').value;
        if (!nombre) {{ alert('Escribe tu nombre'); return; }}
        localStorage.setItem('nombre_empleado', nombre);
        document.getElementById('vista-nombre').style.display = 'none';
        document.getElementById('saludo').innerText = 'Hola, ' + nombre;
        document.getElementById('vista-principal').style.display = 'block';
    }}

    async function registrar(tipo) {{
        const nombre = localStorage.getItem('nombre_empleado');
        const res = await fetch('/registrar', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{uuid, nombre, tipo, id_sucursal: '{id_sucursal}'}})
        }});
        const data = await res.json();
        document.getElementById('mensaje').innerText = data.mensaje;
    }}
</script>
    </body>
    </html>
    """
    return html

@app.route('/registrar', methods=['POST'])
def registrar():
    datos = request.json
    uuid = datos['uuid']
    
    # Validar que el celular esté en la red correcta de la sucursal
    ip_cliente = request.remote_addr
    sucursales = hoja_sucursales.get_all_records()
    sucursal_valida = next((s for s in sucursales if str(s['ID_SUCURSAL']) == datos['id_sucursal']), None)
    
    if sucursal_valida:
        prefijo_red = '.'.join(ip_cliente.split('.')[:2])
        prefijo_sucursal = '.'.join(sucursal_valida['WIFI'].split('.')[:1])
        ip_servidor = request.host.split(':')[0]
        prefijo_servidor = '.'.join(ip_servidor.split('.')[:2])
        
        if prefijo_red != prefijo_servidor:
            return jsonify({'mensaje': 'Acceso denegado. No estás en la red de la sucursal.'})
    nombre_input = datos.get('nombre', '')
    tipo = datos['tipo']
    id_sucursal = datos['id_sucursal']

    # Buscar empleado
    empleados = hoja_empleados.get_all_records()
    empleado = next((e for e in empleados if e['ID_DISPOSITIVO'] == uuid), None)

    if not empleado:
        if not nombre_input:
            return jsonify({'mensaje': 'Primera vez: ingresa tu nombre completo'})
        hoja_empleados.append_row([uuid, nombre_input, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        nombre = nombre_input
    else:
        nombre = empleado['NOMBRE']

    # Buscar sucursal
    sucursales = hoja_sucursales.get_all_records()
    sucursal = next((s for s in sucursales if str(s['ID_SUCURSAL']) == id_sucursal), None)

# Detectar retardo
    ahora = datetime.now()
    retardo = 'NO'
    mensaje_retardo = ''

    if tipo == 'ENTRADA' and 'HORA_ENTRADA' in sucursal:
        hora_limite = datetime.strptime(sucursal['HORA_ENTRADA'], '%H:%M').replace(
            year=ahora.year, month=ahora.month, day=ahora.day)
        if ahora > hora_limite:
            minutos_tarde = int((ahora - hora_limite).total_seconds() / 60)
            retardo = f'{minutos_tarde} min'
            mensaje_retardo = f' ⚠️ Retardo de {minutos_tarde} minutos'

    hoja_registros.append_row([
        nombre,
        sucursal['NOMBRE_SUCURSAL'],
        ahora.strftime('%Y-%m-%d'),
        ahora.strftime('%H:%M:%S'),
        tipo,
        retardo
    ])

    return jsonify({'mensaje': f'{tipo} registrada para {nombre} a las {ahora.strftime("%H:%M:%S")}{mensaje_retardo}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)