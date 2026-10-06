"""
Descargador Multi-Plataforma con recorte usando yt-dlp
Soporta: YouTube, Facebook, Instagram (Reels/Posts), TikTok, Twitter/X, y más
Compatible con Google Colab y sistemas locales
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


class DescargadorMultiPlataforma:
    def __init__(self):
        self.ruta_descargas = "./descargas"
        Path(self.ruta_descargas).mkdir(exist_ok=True)
        self.verificar_dependencias()

    def verificar_dependencias(self):
        """Verifica dependencias necesarias"""
        dependencias_ok = True

        try:
            # Verificar yt-dlp
            subprocess.run(
                ["yt-dlp", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ yt-dlp no encontrado")
            print("   Instala con: pip install -U yt-dlp")
            dependencias_ok = False

        try:
            # Verificar FFmpeg
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ FFmpeg no encontrado")
            print("   Arch Linux: sudo pacman -S ffmpeg")
            print("   Ubuntu/Debian: sudo apt install ffmpeg")
            print("   Fedora: sudo dnf install ffmpeg")
            print("   Mac: brew install ffmpeg")
            dependencias_ok = False

        if not dependencias_ok:
            print(
                "\n⚠️  Instala las dependencias faltantes y vuelve a ejecutar el script"
            )
            sys.exit(1)

    def detectar_plataforma(self, url):
        """Detecta la plataforma del video"""
        url_lower = url.lower()

        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube", "🎥 YouTube"
        elif (
            "facebook.com" in url_lower
            or "fb.watch" in url_lower
            or "fb.com" in url_lower
        ):
            return "facebook", "📘 Facebook"
        elif "instagram.com" in url_lower:
            if "/reel/" in url_lower:
                return "instagram_reel", "📸 Instagram Reel"
            else:
                return "instagram", "📸 Instagram"
        elif "tiktok.com" in url_lower:
            return "tiktok", "🎵 TikTok"
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return "twitter", "🐦 Twitter/X"
        elif "twitch.tv" in url_lower:
            return "twitch", "🎮 Twitch"
        elif "vimeo.com" in url_lower:
            return "vimeo", "🎬 Vimeo"
        else:
            return "unknown", "🌐 Desconocido"

    def obtener_info_video(self, url):
        """Obtiene información del video usando yt-dlp"""
        try:
            comando = [
                "yt-dlp",
                "--dump-json",
                "--no-playlist",
            ]

            # Agregar JS runtime si está disponible
            if hasattr(self, "js_runtime") and self.js_runtime:
                comando.extend(["--js-runtimes", self.js_runtime])
                # Agregar componentes remotos para YouTube challenges
                comando.extend(["--remote-components", "ejs:github"])

            # Agregar extractor args para YouTube
            comando.extend(["--extractor-args", "youtube:player_client=web"])

            # Para Facebook puede necesitar cookies o user-agent
            plataforma, _ = self.detectar_plataforma(url)
            if plataforma == "facebook":
                comando.extend(
                    [
                        "--user-agent",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    ]
                )

            comando.append(url)

            resultado = subprocess.run(
                comando, capture_output=True, text=True, check=True
            )

            return json.loads(resultado.stdout)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.lower()

            # Detectar error de JavaScript runtime
            if "javascript runtime" in error_msg or "js runtime" in error_msg:
                print(f"❌ Error: YouTube requiere un runtime de JavaScript")
                print("\n💡 Solución rápida:")
                print("   Instala Node.js:")
                print("   • Arch Linux: sudo pacman -S nodejs")
                print("   • Ubuntu/Debian: sudo apt install nodejs")
                print("   • Mac: brew install nodejs")
                print("\n   O instala Deno:")
                print("   • curl -fsSL https://deno.land/install.sh | sh")
                print('   • Luego agrega al PATH: export PATH="$HOME/.deno/bin:$PATH"')
                print("\n   Después de instalar, reinicia el script")
            elif "not available" in error_msg:
                print(f"❌ Error: El video no está disponible")
                print("   Posibles causas:")
                print("   • Video privado o eliminado")
                print("   • Restricciones geográficas")
                print("   • Video solo para miembros")
            else:
                print(f"❌ Error al obtener información: {e.stderr}")

            return None
        except json.JSONDecodeError:
            print("❌ Error al procesar información del video")
            return None

    def convertir_tiempo_a_segundos(self, tiempo_str):
        """Convierte tiempo en formato MM:SS o HH:MM:SS a segundos"""
        try:
            partes = tiempo_str.strip().split(":")
            if len(partes) == 2:  # MM:SS
                minutos, segundos = map(int, partes)
                return minutos * 60 + segundos
            elif len(partes) == 3:  # HH:MM:SS
                horas, minutos, segundos = map(int, partes)
                return horas * 3600 + minutos * 60 + segundos
            else:
                return int(partes[0])  # Solo segundos
        except ValueError:
            return None

    def formatear_segundos(self, segundos):
        """Convierte segundos a formato HH:MM:SS"""
        horas = segundos // 3600
        minutos = (segundos % 3600) // 60
        segs = segundos % 60
        if horas > 0:
            return f"{int(horas):02d}:{int(minutos):02d}:{int(segs):02d}"
        return f"{int(minutos):02d}:{int(segs):02d}"

    def mostrar_info_video(self, info, plataforma_nombre):
        """Muestra información del video"""
        print("\n" + "=" * 60)
        print(f"📱 Plataforma: {plataforma_nombre}")
        print(f"📹 Título: {info.get('title', 'Desconocido')}")

        uploader = info.get(
            "uploader", info.get("channel", info.get("creator", "Desconocido"))
        )
        print(f"👤 Autor/Canal: {uploader}")

        duracion = info.get("duration", 0)
        if duracion > 0:
            print(
                f"⏱️  Duración: {self.formatear_segundos(duracion)} ({duracion} segundos)"
            )

        vistas = info.get("view_count", 0)
        if vistas > 0:
            print(f"👁️  Vistas: {vistas:,}")

        likes = info.get("like_count", 0)
        if likes > 0:
            print(f"👍 Likes: {likes:,}")

        print("=" * 60 + "\n")

    def obtener_rango_tiempo(self, duracion_total):
        """Solicita al usuario el rango de tiempo a descargar"""
        print("📝 Ingresa el rango de tiempo a descargar")
        print("   Formatos válidos: MM:SS o HH:MM:SS")
        print(f"   Duración total: {self.formatear_segundos(duracion_total)}\n")

        while True:
            inicio_str = input(
                "⏱️  Tiempo de inicio (ej: 1:30 o deja vacío para 0:00): "
            ).strip()
            if not inicio_str:
                inicio = 0
            else:
                inicio = self.convertir_tiempo_a_segundos(inicio_str)
                if inicio is None or inicio < 0:
                    print("❌ Tiempo inválido. Intenta de nuevo.\n")
                    continue
                if inicio >= duracion_total:
                    print(
                        f"❌ El inicio debe ser menor a {self.formatear_segundos(duracion_total)}\n"
                    )
                    continue
            break

        while True:
            fin_str = input(
                "⏱️  Tiempo de fin (ej: 3:45 o deja vacío para el final): "
            ).strip()
            if not fin_str:
                fin = duracion_total
            else:
                fin = self.convertir_tiempo_a_segundos(fin_str)
                if fin is None or fin <= 0:
                    print("❌ Tiempo inválido. Intenta de nuevo.\n")
                    continue
                if fin > duracion_total:
                    print(
                        f"⚠️  El fin excede la duración. Usando {self.formatear_segundos(duracion_total)}"
                    )
                    fin = duracion_total
                if fin <= inicio:
                    print("❌ El tiempo de fin debe ser mayor al de inicio.\n")
                    continue
            break

        duracion = fin - inicio
        print(
            f"\n✅ Rango seleccionado: {self.formatear_segundos(inicio)} → {self.formatear_segundos(fin)}"
        )
        print(f"   Duración del clip: {self.formatear_segundos(duracion)}\n")

        return inicio, fin

    def limpiar_nombre_archivo(self, nombre):
        """Limpia el nombre de archivo de caracteres inválidos"""
        caracteres_invalidos = '<>:"/\\|?*'
        for char in caracteres_invalidos:
            nombre = nombre.replace(char, "")
        return nombre.strip()[:200]  # Limitar longitud

    def descargar_video_completo(self, url, nombre_archivo=None):
        """Descarga el video completo"""
        try:
            plataforma, plataforma_nombre = self.detectar_plataforma(url)

            print(f"🔍 Obteniendo información del video de {plataforma_nombre}...")
            info = self.obtener_info_video(url)

            if not info:
                return None

            self.mostrar_info_video(info, plataforma_nombre)

            # Configurar opciones según plataforma
            if plataforma in ["instagram_reel", "instagram", "tiktok"]:
                # Para Reels/TikTok, generalmente hay una sola calidad
                print("📥 Estos videos tienen calidad fija (no hay opciones)")
                formato = "best"
                opcion = "1"
            else:
                # Mostrar opciones de calidad para otras plataformas
                print("🎬 Selecciona la calidad:")
                print("1. Mejor calidad disponible")
                print("2. 720p (HD)")
                print("3. 480p (SD)")
                print("4. Solo audio (MP3)")

                opcion = input(f"\nOpción (1-4, default 1): ").strip() or "1"

                # Configurar formato según opción
                if opcion == "1":
                    formato = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                elif opcion == "2":
                    formato = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"
                elif opcion == "3":
                    formato = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best"
                elif opcion == "4":
                    formato = "bestaudio[ext=m4a]/bestaudio"
                else:
                    formato = "best[ext=mp4]/best"

            # Obtener nombre de archivo
            if not nombre_archivo:
                nombre_archivo = input(
                    "\n💾 Nombre del archivo (sin extensión, Enter para usar título): "
                ).strip()
                if not nombre_archivo:
                    titulo = info.get("title", "video")
                    nombre_archivo = f"{plataforma}_{titulo}"

            nombre_archivo = self.limpiar_nombre_archivo(nombre_archivo)
            extension = ".mp3" if opcion == "4" else ".mp4"
            archivo_salida = os.path.join(
                self.ruta_descargas, f"{nombre_archivo}{extension}"
            )

            # Comando de descarga
            print(f"\n⬇️  Descargando desde {plataforma_nombre}...")

            comando = [
                "yt-dlp",
                "-f",
                formato,
                "--merge-output-format",
                "mp4" if opcion != "4" else "mp3",
                "-o",
                archivo_salida,
                "--no-playlist",
            ]

            # Opciones específicas por plataforma
            if plataforma == "facebook":
                comando.extend(
                    [
                        "--user-agent",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    ]
                )

            if plataforma in ["instagram", "instagram_reel"]:
                comando.extend(
                    [
                        "--user-agent",
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                    ]
                )

            if opcion == "4":
                comando.extend(["--extract-audio", "--audio-format", "mp3"])

            comando.append(url)

            subprocess.run(comando, check=True)

            if os.path.exists(archivo_salida):
                print(f"\n✅ ¡Descarga completada!")
                print(f"📁 Archivo: {archivo_salida}")
                print(
                    f"💾 Tamaño: {os.path.getsize(archivo_salida) / (1024 * 1024):.2f} MB"
                )
                print(f"✨ Compatible con CapCut, Premiere, DaVinci, etc.")
                return archivo_salida
            else:
                print("❌ El archivo no se creó correctamente")
                return None

        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error durante la descarga")
            if plataforma == "facebook":
                print("\n💡 Tips para Facebook:")
                print("   - Asegúrate de que el video sea público")
                print("   - Si es privado, necesitarás cookies de tu sesión")
                print("   - Algunos videos de Facebook están protegidos")
            elif plataforma == "instagram":
                print("\n💡 Tips para Instagram:")
                print("   - El perfil debe ser público")
                print("   - Para contenido privado necesitas autenticación")
            return None
        except Exception as e:
            print(f"\n❌ Error inesperado: {str(e)}")
            return None

    def descargar_con_recorte(self, url):
        """Descarga un video y permite hacer múltiples cortes del mismo"""
        try:
            plataforma, plataforma_nombre = self.detectar_plataforma(url)

            print(f"🔍 Obteniendo información del video de {plataforma_nombre}...")
            info = self.obtener_info_video(url)

            if not info:
                return None

            self.mostrar_info_video(info, plataforma_nombre)

            duracion = info.get("duration", 0)
            if duracion == 0:
                print("❌ No se pudo obtener la duración del video")
                print("💡 Algunos videos muy cortos o Lives no pueden recortarse")
                return None

            # Preguntar cuántos cortos quiere hacer
            while True:
                try:
                    num_cortos = input("\n🎬 ¿Cuántos cortos quieres hacer de este video? (1-20): ").strip()
                    if not num_cortos:
                        num_cortos = 1
                    else:
                        num_cortos = int(num_cortos)
                    
                    if num_cortos < 1 or num_cortos > 20:
                        print("❌ Por favor ingresa un número entre 1 y 20")
                        continue
                    break
                except ValueError:
                    print("❌ Por favor ingresa un número válido")
                    continue

            # Recolectar información de todos los cortos
            cortos = []
            print(f"\n📝 Vamos a configurar {num_cortos} corto(s)\n")
            
            for i in range(num_cortos):
                print(f"{'='*60}")
                print(f"  CORTO {i+1} de {num_cortos}")
                print(f"{'='*60}")
                
                # Obtener rango de tiempo para este corto
                inicio, fin = self.obtener_rango_tiempo(duracion)
                
                # Obtener nombre de archivo para este corto
                nombre_archivo = input(
                    f"\n💾 Nombre para el corto #{i+1} (sin extensión, Enter para auto): "
                ).strip()
                
                if not nombre_archivo:
                    titulo = info.get("title", "clip")
                    nombre_archivo = f"{plataforma}_{titulo}_corto{i+1}_{self.formatear_segundos(inicio)}-{self.formatear_segundos(fin)}"
                
                nombre_archivo = self.limpiar_nombre_archivo(nombre_archivo)
                
                cortos.append({
                    'inicio': inicio,
                    'fin': fin,
                    'nombre': nombre_archivo,
                    'numero': i + 1
                })
                
                print(f"✅ Corto #{i+1} configurado: {nombre_archivo}")
                print(f"   Rango: {self.formatear_segundos(inicio)} → {self.formatear_segundos(fin)}\n")

            # Descargar video completo UNA SOLA VEZ
            archivo_temp = os.path.join(self.ruta_descargas, "temp_video.mp4")
            print(f"\n{'='*60}")
            print(f"📥 Descargando video desde {plataforma_nombre}...")
            print(f"   (Solo se descargará una vez para todos los cortos)")
            print(f"{'='*60}\n")

            comando_descarga = [
                "yt-dlp",
                "-f",
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "--merge-output-format",
                "mp4",
                "-o",
                archivo_temp,
                "--no-playlist",
            ]

            # Opciones específicas por plataforma
            if plataforma == "facebook":
                comando_descarga.extend(
                    [
                        "--user-agent",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    ]
                )

            if plataforma in ["instagram", "instagram_reel"]:
                comando_descarga.extend(
                    [
                        "--user-agent",
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                    ]
                )

            comando_descarga.append(url)

            subprocess.run(
                comando_descarga,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            print(f"✅ ¡Video descargado exitosamente!\n")

            # Procesar todos los cortos del video descargado
            archivos_creados = []
            print(f"{'='*60}")
            print(f"✂️  Procesando {num_cortos} corto(s)...")
            print(f"{'='*60}\n")

            for corto in cortos:
                inicio = corto['inicio']
                fin = corto['fin']
                nombre_archivo = corto['nombre']
                numero = corto['numero']
                
                archivo_salida = os.path.join(self.ruta_descargas, f"{nombre_archivo}.mp4")
                
                print(f"✂️  [{numero}/{num_cortos}] Recortando: {nombre_archivo}")
                print(f"   Rango: {self.formatear_segundos(inicio)} → {self.formatear_segundos(fin)}")

                comando_recorte = [
                    "ffmpeg",
                    "-i",
                    archivo_temp,
                    "-ss",
                    str(inicio),
                    "-to",
                    str(fin),
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    "-preset",
                    "fast",
                    "-crf",
                    "23",
                    "-y",
                    archivo_salida,
                ]

                subprocess.run(
                    comando_recorte,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                if os.path.exists(archivo_salida):
                    tamaño = os.path.getsize(archivo_salida) / (1024 * 1024)
                    duracion_clip = fin - inicio
                    archivos_creados.append({
                        'archivo': archivo_salida,
                        'tamaño': tamaño,
                        'duracion': duracion_clip,
                        'nombre': nombre_archivo
                    })
                    print(f"   ✅ Completado ({tamaño:.2f} MB, {self.formatear_segundos(duracion_clip)})\n")
                else:
                    print(f"   ❌ Error al crear el archivo\n")

            # Limpiar archivo temporal
            if os.path.exists(archivo_temp):
                os.remove(archivo_temp)
                print(f"🗑️  Archivo temporal eliminado\n")

            # Mostrar resumen final
            if archivos_creados:
                print(f"\n{'='*60}")
                print(f"✅ ¡PROCESO COMPLETADO!")
                print(f"{'='*60}")
                print(f"� Resumen de {len(archivos_creados)} corto(s) creado(s):\n")
                
                tamaño_total = 0
                for i, clip in enumerate(archivos_creados, 1):
                    print(f"{i}. {clip['nombre']}.mp4")
                    print(f"   📁 {clip['archivo']}")
                    print(f"   💾 Tamaño: {clip['tamaño']:.2f} MB")
                    print(f"   ⏱️  Duración: {self.formatear_segundos(clip['duracion'])}")
                    tamaño_total += clip['tamaño']
                    print()
                
                print(f"💾 Tamaño total: {tamaño_total:.2f} MB")
                print(f"✨ Todos los clips son compatibles con: CapCut, Premiere, DaVinci, etc.")
                print(f"{'='*60}\n")
                
                return archivos_creados
            else:
                print("❌ No se creó ningún archivo correctamente")
                return None

        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error durante el proceso")
            if plataforma == "facebook":
                print("\n💡 Tips para Facebook:")
                print("   - Verifica que el video sea accesible públicamente")
                print("   - Intenta copiar la URL directamente desde el navegador")
            if 'archivo_temp' in locals() and os.path.exists(archivo_temp):
                os.remove(archivo_temp)
            return None
        except Exception as e:
            print(f"\n❌ Error inesperado: {str(e)}")
            if 'archivo_temp' in locals() and os.path.exists(archivo_temp):
                os.remove(archivo_temp)
            return None


def mostrar_menu():
    """Muestra el menú principal"""
    print("\n" + "=" * 60)
    print("🌐 DESCARGADOR MULTI-PLATAFORMA CON RECORTE")
    print("=" * 60)
    print("\n📱 Plataformas soportadas:")
    print("   🎥 YouTube | 📘 Facebook | 📸 Instagram (Reels)")
    print("   🎵 TikTok | 🐦 Twitter/X | 🎮 Twitch | 🎬 Vimeo")
    print("\n¿Qué deseas hacer?")
    print("1. Descargar video completo")
    print("2. Descargar un segmento específico (recortar)")
    print("3. Salir")
    print()


def main():
    print("🌐 Descargador Multi-Plataforma")
    print("   Compatible con YouTube, Facebook, Instagram, TikTok y más\n")

    descargador = DescargadorMultiPlataforma()

    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción (1-3): ").strip()

        if opcion == "3":
            print("\n👋 ¡Hasta luego!")
            break

        if opcion not in ["1", "2"]:
            print("❌ Opción inválida")
            continue

        url = input("🔗 Ingresa la URL del video: ").strip()

        if not url:
            print("❌ URL vacía")
            continue

        # Detectar y mostrar plataforma
        plataforma, plataforma_nombre = descargador.detectar_plataforma(url)
        print(f"\n✅ Plataforma detectada: {plataforma_nombre}")

        if plataforma == "unknown":
            print("⚠️  La plataforma no fue reconocida, intentando de todos modos...")

        if opcion == "1":
            descargador.descargar_video_completo(url)
        elif opcion == "2":
            descargador.descargar_con_recorte(url)

        continuar = input("\n¿Deseas descargar otro video? (s/n): ").strip().lower()
        if continuar != "s":
            print("\n👋 ¡Hasta luego!")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(0)
