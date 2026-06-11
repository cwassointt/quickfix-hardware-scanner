import os
import subprocess
import json
import re
from datetime import datetime


def obtener_hardware():
    ps_command = """
    $ErrorActionPreference = 'SilentlyContinue'
    # FILTRO APLICADO: Solo lee discos que NO esten conectados por USB
    $disks = Get-PhysicalDisk | Where-Object { $_.BusType -ne 'USB' } | Select-Object FriendlyName, MediaType, HealthStatus, Size
    $diskArray = @()

    foreach ($d in $disks) {
        $sizeStr = "[???]"
        if ($null -ne $d.Size) {
            $gb = $d.Size / 1GB

            if ($gb -le 35) { $sizeStr = "[ 32 GB ]" }
            elseif ($gb -le 70) { $sizeStr = "[ 64 GB ]" }
            elseif ($gb -le 135) { $sizeStr = "[ 128 GB ]" }
            elseif ($gb -le 270) { $sizeStr = "[ 256 GB ]" }
            elseif ($gb -le 530) { $sizeStr = "[ 512 GB ]" }
            elseif ($gb -le 1050) { $sizeStr = "[ 1 TB ]" }
            elseif ($gb -le 2100) { $sizeStr = "[ 2 TB ]" }
            elseif ($gb -le 4200) { $sizeStr = "[ 4 TB ]" }
            else { 
                $tb = [math]::Round($gb / 1024, 1)
                $sizeStr = "[ $tb TB ]" 
            }
        }

        $diskArray += "<strong style='color:#ffcc00; letter-spacing: 1px;'>$sizeStr</strong> $($d.FriendlyName) <span style='color:#888888; font-size:13px;'>($($d.MediaType))</span> - Estado: $($d.HealthStatus)"
    }

    $info = @{
        Fabricante = (Get-CimInstance Win32_ComputerSystem).Manufacturer
        Modelo = (Get-CimInstance Win32_ComputerSystem).Model
        Serie = (Get-CimInstance Win32_BIOS).SerialNumber
        CPU = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name
        RAM = [math]::Ceiling((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
        GPUs = (Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join " | "
        Discos = $diskArray -join "<br>"
    }
    $info | ConvertTo-Json
    """
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return json.loads(result.stdout)
    except Exception as e:
        return {"Error": str(e)}


def generar_html_unificado():
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    hw = obtener_hardware()

    # --- SISTEMA DE GUÍA AUTOMÁTICA (SN + FECHA) ---
    serie_completa = str(hw.get('Serie', '')).strip()

    # Filtro elegante para PCs de escritorio
    if "O.E.M." in serie_completa.upper() or "DEFAULT" in serie_completa.upper() or not serie_completa:
        serie_corta = "DESK"
        hw['Serie'] = "PC de Escritorio"
    elif len(serie_completa) >= 4:
        serie_corta = serie_completa[-4:].upper()
    else:
        serie_corta = serie_completa.zfill(4).upper()

    marca_tiempo = datetime.now().strftime("%y%m%d-%H%M")
    guia = f"{serie_corta}_{marca_tiempo}"
    # -----------------------------------------------

    modelo_raw = hw.get("Modelo", "Generico")
    modelo_limpio = re.sub(r'[\\/*?:"<>|]', "_", modelo_raw).strip()
    nombre_archivo = f"{modelo_limpio}_{guia}.html"
    ruta_final = os.path.join(ruta_actual, nombre_archivo)
    ruta_temp_bat = os.path.join(ruta_actual, "temp_bat.html")

    # Generar reporte de bateria de Windows
    subprocess.run(["powercfg", "/batteryreport", "/output", ruta_temp_bat], capture_output=True,
                   creationflags=subprocess.CREATE_NO_WINDOW)

    fecha_visual = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Panel HTML personalizado
    panel_quickfix = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 20px auto; background: #0a0a0a; color: #e3e5e8; border-radius: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.8); border: 1px solid #2a2a2a; overflow: hidden;">

        <div style="background: linear-gradient(180deg, #111111 0%, #0a0a0a 100%); padding: 30px 25px; text-align: left; border-bottom: 2px solid #ff6a00;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 800; letter-spacing: -0.5px;">
                <span style="color: #ffffff;">Quick</span><span style="color: #ff6a00;">Fix</span>
            </h1>
            <p style="margin: 5px 0 0 0; color: #888888; font-size: 14px; text-transform: uppercase; letter-spacing: 2px;">Laboratorio Especialista | Lima, Perú</p>
        </div>

        <div style="padding: 30px;">
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #1f1f1f; padding-bottom: 20px; margin-bottom: 25px;">
                <div><span style="color: #666666; font-size: 13px; text-transform: uppercase;">Orden de Ingreso (SN_Fecha)</span><br><strong style="font-size: 24px; color: #ff6a00;">#{guia}</strong></div>
                <div style="text-align: right;"><span style="color: #666666; font-size: 13px; text-transform: uppercase;">Fecha del Escaneo</span><br><strong style="font-size: 16px; color: #ffffff;">{fecha_visual}</strong></div>
            </div>

            <h3 style="color: #ffffff; margin-bottom: 20px; font-weight: 600; font-size: 18px; display: flex; align-items: center;">
                <span style="display: inline-block; width: 4px; height: 18px; background: #ffcc00; margin-right: 10px; border-radius: 2px;"></span>
                Hardware del Equipo
            </h3>

            <table style="width: 100%; border-collapse: collapse; font-size: 15px;">
                <tr><td style="padding: 12px 0; border-bottom: 1px solid #1f1f1f; width: 180px; color:#888888;">Marca y Modelo</td><td style="padding: 12px 0; border-bottom: 1px solid #1f1f1f; color:#ffffff;"><strong>{hw.get('Fabricante', '')} {hw.get('Modelo', '')}</strong></td></tr>
                <tr><td style="padding: 12px 0; border-bottom: 1px solid #1f1f1f; color:#888888;">Número de Serie (SN)</td><td style="padding: 12px 0; border-bottom: 1px solid #1f1f1f;"><strong style="color: #ffcc00; font-family: monospace; font-size: 16px;">{hw.get('Serie', 'N/A')}</strong></td></tr>
                <tr><td style="padding: 12px 0; border-bottom: 1px solid #1f1f1f; color:#888888;">Procesador (CPU)</td><td style="padding: 12px 0; border-bottom: 1px solid #1f1f1f; color:#ffffff;">{hw.get('CPU', 'N/A')}</td></tr>
                <tr><td style="padding: 12px 0; border-bottom: 1px solid #1f1f1f; color:#888888;">Gráficos (GPU)</td><td style="padding: 12px 0; border-bottom: 1px solid #1f1f1f; color:#ffffff;">{hw.get('GPUs', 'N/A')}</td></tr>
                <tr><td style="padding: 12px 0; border-bottom: 1px solid #1f1f1f; color:#888888;">Memoria RAM</td><td style="padding: 12px 0; border-bottom: 1px solid #1f1f1f; color:#ffffff;">{hw.get('RAM', 'N/A')} GB</td></tr>
                <tr><td style="padding: 12px 0; border-bottom: 1px solid #1f1f1f; color:#888888;">Almacenamiento</td><td style="padding: 12px 0; border-bottom: 1px solid #1f1f1f; color:#ffffff; line-height: 1.6;">{hw.get('Discos', 'N/A')}</td></tr>
            </table>
        </div>
    </div>
    """

    contenido_html = ""
    if os.path.exists(ruta_temp_bat):
        with open(ruta_temp_bat, "r", encoding="utf-8", errors="ignore") as f:
            contenido_html = f.read()
        os.remove(ruta_temp_bat)

        estilo_oscuro_bateria = "<style>body { background-color: #121212 !important; color: #cccccc !important; }</style>"

        titulo_personalizado = f"<title>QuickFix - {modelo_limpio} ({guia})</title>"
        contenido_html = re.sub(r'<title>.*?</title>', titulo_personalizado, contenido_html, flags=re.IGNORECASE)

        if "<body" in contenido_html:
            contenido_html = re.sub(r'(<body[^>]*>)', r'\1\n' + estilo_oscuro_bateria + panel_quickfix, contenido_html,
                                    count=1, flags=re.IGNORECASE)
        else:
            contenido_html = estilo_oscuro_bateria + panel_quickfix + contenido_html
    else:
        contenido_html = f"<html><head><meta charset='utf-8'><title>QuickFix - {modelo_limpio} ({guia})</title></head><body style='background:#121212; margin: 0; padding: 20px;'>{panel_quickfix}</body></html>"

    with open(ruta_final, "w", encoding="utf-8") as f:
        f.write(contenido_html)

    os.startfile(ruta_final)


if __name__ == "__main__":
    generar_html_unificado()