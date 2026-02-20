from datetime import datetime
import reporte

def verificar_y_ejecutar():
    ahora = datetime.now()
    if ahora.day == 15 and ahora.hour == 11 and ahora.minute == 59:
        print(f"Ejecutando reporte quincenal: {ahora}")
        reporte.generar_reporte()
    else:
        print(f"No es momento de generar reporte. Hoy es día {ahora.day} a las {ahora.strftime('%H:%M')}")

if __name__ == '__main__':
    verificar_y_ejecutar()