#!/usr/bin/env python3
"""
Nombre del Módulo: tools.hardware.detect_cameras

Descripción: Script para detectar TODAS las cámaras disponibles en el sistema, incluyendo las que están en índices no continuos.
"""

import cv2
import platform
import time
from typing import TypedDict


class CameraInfo(TypedDict):
    index: int
    width: int
    height: int
    fps: float

print("=" * 70)
print("DETECCIÓN EXHAUSTIVA DE CÁMARAS")
print("=" * 70)
print()

print(f"Sistema Operativo: {platform.system()} {platform.release()}")
print(f"OpenCV versión: {cv2.__version__}")
print()

# Probar todos los índices de 0 a 20 (exhaustivo)
print("Probando índices de cámara de 0 a 20...")
print("(Esto puede tardar ~30 segundos)\n")

camaras_encontradas: list[CameraInfo] = []

for i in range(21):
    print(f"Probando índice {i}...", end=" ", flush=True)

    # Intentar con DSHOW (Windows)
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)

    if cap.isOpened():
        # Verificar que realmente funciona capturando un frame
        ret, frame = cap.read()

        if ret and frame is not None:
            # Obtener propiedades
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(cap.get(cv2.CAP_PROP_FPS))

            camaras_encontradas.append({
                'index': i,
                'width': width,
                'height': height,
                'fps': fps
            })

            print(f"✓ ENCONTRADA - {width}x{height} @ {fps:.0f}fps")
        else:
            print("✗ Se abre pero no captura frames")

        cap.release()
    else:
        print("✗ No disponible")

    time.sleep(0.1)  # Pequeña pausa entre pruebas

print()
print("=" * 70)
print("RESULTADOS")
print("=" * 70)
print()

if not camaras_encontradas:
    print("❌ No se encontraron cámaras")
    print()
    print("Posibles causas:")
    print("• No hay cámara conectada")
    print("• La cámara está en uso por otra aplicación")
    print("• Windows bloqueó el acceso (permisos)")
    print()
else:
    print(f"✓ Se encontraron {len(camaras_encontradas)} cámara(s):\n")

    for i, cam in enumerate(camaras_encontradas, 1):
        print(f"{i}. ÍNDICE {cam['index']}")
        print(f"   Resolución: {cam['width']}x{cam['height']}")
        print(f"   FPS: {cam['fps']:.1f}")
        print()

    # Si hay más de una cámara
    if len(camaras_encontradas) > 1:
        print("💡 TIENES MÚLTIPLES CÁMARAS")
        print()
        print("Índices detectados:", [c['index'] for c in camaras_encontradas])
        print()
        print("En la aplicación, al detectar cámaras deberías ver todas estas.")
        print()
    else:
        print("⚠️ SOLO SE DETECTÓ 1 CÁMARA")
        print()
        print("Si esperabas ver más cámaras (como una Logitech):")
        print("• Verifica que esté conectada")
        print("• Cierra otras apps que usen la cámara (Zoom, Skype, etc)")
        print("• Desconecta y reconecta la cámara USB")
        print("• Prueba otro puerto USB")
        print()

print("=" * 70)
print()

# Preguntar si quiere probar una cámara específica
if camaras_encontradas:
    print("¿Quieres probar una cámara específica con preview? (s/n): ", end="")
    respuesta = input().lower().strip()

    if respuesta == 's':
        print()
        print("Cámaras disponibles:")
        for i, cam in enumerate(camaras_encontradas, 1):
            print(f"  {i}. Índice {cam['index']}")

        print()
        num_str = input(f"Selecciona (1-{len(camaras_encontradas)}): ").strip()

        try:
            num_int = int(num_str)
            if 1 <= num_int <= len(camaras_encontradas):
                cam_index = camaras_encontradas[num_int - 1]['index']

                print(f"\nAbriendo preview de cámara {cam_index}...")
                print("Presiona ESC para cerrar\n")

                cap = cv2.VideoCapture(cam_index, int(cv2.CAP_DSHOW))

                while True:
                    ret, frame = cap.read()

                    if not ret:
                        print("Error leyendo frame")
                        break

                    cv2.putText(
                        frame,
                        f"Camara {cam_index} - Presiona ESC para cerrar",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )

                    cv2.imshow(f'Preview Camara {cam_index}', frame)

                    if cv2.waitKey(1) & 0xFF == 27:  # ESC
                        break

                cap.release()
                cv2.destroyAllWindows()

                print("\n✓ Preview cerrado")
        except Exception:
            print("Entrada inválida")

print("\nScript finalizado")