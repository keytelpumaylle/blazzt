"""
Convertidor de Videos a MP3 Multi-Plataforma
Descarga audio de YouTube, Facebook, Instagram, TikTok, etc.
Con opción de recorte de tiempo específico
"""

import json
import os
import subprocess
import sys
from pathlib import Path


class ConvertidorMP3:
    def __init__(self):
        self.ruta_descargas = "./audios"
        Path(self.ruta_descargas).mkdir(exist_ok=True)
        self.verificar_dependencias()

    def verificar_dependencias(self):
        """Verifica dependencias necesarias"""
        dependencias_ok = True

        try:
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
            dependencias_ok = False

        if not dependencias_ok:
            print("\n⚠️  Instala las dependencias faltantes y vuelve a ejecutar")
            sys.exit(1)

    def detectar_plataforma(self, url):
        """Detecta la plataforma del video"""
        url_lower = url.lower()

        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube", "🎥 YouTube"
        elif "facebook.com" in url_lower or "fb.watch" in url_lower:
            return "facebook", "📘 Facebook"
        elif "instagram.com" in url_lower:
            return "instagram", "📸 Instagram"
        elif "tiktok.com" in url_lower:
            return "tiktok", "🎵 TikTok"
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return "twitter", "🐦 Twitter/X"
        elif "soundcloud.com" in url_lower:
            return "soundcloud", "🎧 SoundCloud"
        elif "spotify.com" in url_lower:
            return "spotify", "🎶 Spotify"
        else:
            return "unknown", "🌐 Desconocido"

    def obtener_info_video(self, url):
        """Obtiene información del video/audio"""
        try:
            comando = ["yt-dlp", "--dump-json", "--no-playlist", url]

            plataforma, _ = self.detectar_plataforma(url)
            if plataforma == "facebook":
                comando.extend(
                    [
                        "--user-agent",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    ]
                )
            elif plataforma == "instagram":
                comando.extend(
                    [
                        "--user-agent",
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                    ]
                )

            resultado = subprocess.run(
                comando, capture_output=True, text=True, check=True
            )

            return json.loads(resultado.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error al obtener información: {e.stderr}")
            return None
        except json.JSONDecodeError:
            print("❌ Error al procesar información")
            return None

    def convertir_tiempo_a_segundos(self, tiempo_str):
        """Convierte tiempo en formato MM:SS o HH:MM:SS a segundos"""
        try:
            partes = tiempo_str.strip().split(":")
            if len(partes) == 2:
                minutos, segundos = map(int, partes)
                return minutos * 60 + segundos
            elif len(partes) == 3:
                horas, minutos, segundos = map(int, partes)
                return horas * 3600 + minutos * 60 + segundos
            else:
                return int(partes[0])
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

    def mostrar_info(self, info, plataforma_nombre):
        """Muestra información del contenido"""
        print("\n" + "=" * 60)
        print(f"📱 Plataforma: {plataforma_nombre}")
        print(f"🎵 Título: {info.get('title', 'Desconocido')}")

        uploader = info.get(
            "uploader", info.get("channel", info.get("artist", "Desconocido"))
        )
        print(f"👤 Autor/Artista: {uploader}")

        duracion = info.get("duration", 0)
        if duracion > 0:
            print(f"⏱️  Duración: {self.formatear_segundos(duracion)} ({duracion}s)")

        print("=" * 60 + "\n")

    def obtener_rango_tiempo(self, duracion_total):
        """Solicita el rango de tiempo para recortar"""
        print("📝 Ingresa el rango de tiempo para el audio")
        print("   Formatos: MM:SS o HH:MM:SS")
        print(f"   Duración total: {self.formatear_segundos(duracion_total)}\n")

        while True:
            inicio_str = input("⏱️  Inicio (Enter para 0:00): ").strip()
            if not inicio_str:
                inicio = 0
            else:
                inicio = self.convertir_tiempo_a_segundos(inicio_str)
                if inicio is None or inicio < 0:
                    print("❌ Tiempo inválido\n")
                    continue
                if inicio >= duracion_total:
                    print(
                        f"❌ Debe ser menor a {self.formatear_segundos(duracion_total)}\n"
                    )
                    continue
            break

        while True:
            fin_str = input("⏱️  Fin (Enter para el final): ").strip()
            if not fin_str:
                fin = duracion_total
            else:
                fin = self.convertir_tiempo_a_segundos(fin_str)
                if fin is None or fin <= 0:
                    print("❌ Tiempo inválido\n")
                    continue
                if fin > duracion_total:
                    print(
                        f"⚠️  Usando duración máxima: {self.formatear_segundos(duracion_total)}"
                    )
                    fin = duracion_total
                if fin <= inicio:
                    print("❌ El fin debe ser mayor al inicio\n")
                    continue
            break

        print(
            f"\n✅ Rango: {self.formatear_segundos(inicio)} → {self.formatear_segundos(fin)}"
        )
        print(f"   Duración del audio: {self.formatear_segundos(fin - inicio)}\n")

        return inicio, fin

    def limpiar_nombre_archivo(self, nombre):
        """Limpia caracteres inválidos del nombre"""
        caracteres_invalidos = '<>:"/\\|?*'
        for char in caracteres_invalidos:
            nombre = nombre.replace(char, "")
        return nombre.strip()[:200]

    def seleccionar_calidad_audio(self):
        """Permite seleccionar la calidad del audio"""
        print("🎧 Selecciona la calidad del audio:")
        print("1. Alta calidad (320 kbps) - Mejor calidad")
        print("2. Calidad media (192 kbps) - Balance")
        print("3. Calidad baja (128 kbps) - Menor tamaño")

        opcion = input("\nCalidad (1-3, default 1): ").strip() or "1"

        calidades = {
            "1": ("320k", "320 kbps"),
            "2": ("192k", "192 kbps"),
            "3": ("128k", "128 kbps"),
        }

        return calidades.get(opcion, calidades["1"])

    def descargar_audio_completo(self, url):
        """Descarga el audio completo"""
        try:
            plataforma, plataforma_nombre = self.detectar_plataforma(url)

            print(f"🔍 Obteniendo información de {plataforma_nombre}...")
            info = self.obtener_info_video(url)

            if not info:
                return None

            self.mostrar_info(info, plataforma_nombre)

            # Seleccionar calidad
            bitrate, bitrate_texto = self.seleccionar_calidad_audio()

            # Obtener nombre
            nombre = input(
                "\n💾 Nombre del archivo MP3 (sin extensión, Enter para auto): "
            ).strip()
            if not nombre:
                nombre = info.get("title", "audio")

            nombre = self.limpiar_nombre_archivo(nombre)
            archivo_salida = os.path.join(self.ruta_descargas, f"{nombre}.mp3")

            print(f"\n⬇️  Descargando audio desde {plataforma_nombre}...")
            print(f"🎧 Calidad: {bitrate_texto}")

            comando = [
                "yt-dlp",
                "--extract-audio",
                "--audio-format",
                "mp3",
                "--audio-quality",
                bitrate,
                "-o",
                archivo_salida,
                "--no-playlist",
            ]

            # User-agents específicos
            if plataforma == "facebook":
                comando.extend(
                    [
                        "--user-agent",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    ]
                )
            elif plataforma == "instagram":
                comando.extend(
                    [
                        "--user-agent",
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                    ]
                )

            comando.append(url)

            subprocess.run(comando, check=True)

            if os.path.exists(archivo_salida):
                print(f"\n✅ ¡Audio descargado!")
                print(f"📁 Archivo: {archivo_salida}")
                print(
                    f"💾 Tamaño: {os.path.getsize(archivo_salida) / (1024 * 1024):.2f} MB"
                )
                print(f"🎧 Calidad: {bitrate_texto}")
                return archivo_salida
            else:
                print("❌ El archivo no se creó correctamente")
                return None

        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error durante la descarga")
            self.mostrar_tips_error(plataforma)
            return None
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return None

    def descargar_audio_recortado(self, url):
        """Descarga y recorta el audio"""
        try:
            plataforma, plataforma_nombre = self.detectar_plataforma(url)

            print(f"🔍 Obteniendo información de {plataforma_nombre}...")
            info = self.obtener_info_video(url)

            if not info:
                return None

            self.mostrar_info(info, plataforma_nombre)

            duracion = info.get("duration", 0)
            if duracion == 0:
                print("❌ No se pudo obtener la duración")
                return None

            # Obtener rango de tiempo
            inicio, fin = self.obtener_rango_tiempo(duracion)

            # Seleccionar calidad
            bitrate, bitrate_texto = self.seleccionar_calidad_audio()

            # Obtener nombre
            nombre = input(
                "\n💾 Nombre del archivo MP3 (sin extensión, Enter para auto): "
            ).strip()
            if not nombre:
                titulo = info.get("title", "audio")
                nombre = f"{titulo}_{self.formatear_segundos(inicio)}-{self.formatear_segundos(fin)}"

            nombre = self.limpiar_nombre_archivo(nombre)
            archivo_temp = os.path.join(self.ruta_descargas, "temp_audio.mp3")
            archivo_salida = os.path.join(self.ruta_descargas, f"{nombre}.mp3")

            # Descargar audio completo
            print(f"\n📥 Descargando audio completo desde {plataforma_nombre}...")

            comando_descarga = [
                "yt-dlp",
                "--extract-audio",
                "--audio-format",
                "mp3",
                "--audio-quality",
                bitrate,
                "-o",
                archivo_temp,
                "--no-playlist",
            ]

            if plataforma == "facebook":
                comando_descarga.extend(
                    [
                        "--user-agent",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    ]
                )
            elif plataforma == "instagram":
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

            # Recortar audio con FFmpeg
            print(
                f"\n✂️  Recortando audio de {self.formatear_segundos(inicio)} a {self.formatear_segundos(fin)}..."
            )

            comando_recorte = [
                "ffmpeg",
                "-i",
                archivo_temp,
                "-ss",
                str(inicio),
                "-to",
                str(fin),
                "-c:a",
                "libmp3lame",
                "-b:a",
                bitrate,
                "-y",
                archivo_salida,
            ]

            subprocess.run(
                comando_recorte,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Limpiar temporal
            if os.path.exists(archivo_temp):
                os.remove(archivo_temp)

            if os.path.exists(archivo_salida):
                print(f"\n✅ ¡Audio recortado!")
                print(f"📁 Archivo: {archivo_salida}")
                print(
                    f"💾 Tamaño: {os.path.getsize(archivo_salida) / (1024 * 1024):.2f} MB"
                )
                print(f"⏱️  Duración: {self.formatear_segundos(fin - inicio)}")
                print(f"🎧 Calidad: {bitrate_texto}")
                return archivo_salida
            else:
                print("❌ El archivo no se creó")
                return None

        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error durante el proceso")
            if os.path.exists(archivo_temp):
                os.remove(archivo_temp)
            return None
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            if os.path.exists(archivo_temp):
                os.remove(archivo_temp)
            return None

    def mostrar_tips_error(self, plataforma):
        """Muestra tips según la plataforma"""
        if plataforma == "facebook":
            print("\n💡 Tips para Facebook:")
            print("   - El video debe ser público")
            print("   - Para contenido privado necesitas cookies")
        elif plataforma == "instagram":
            print("\n💡 Tips para Instagram:")
            print("   - El perfil debe ser público")
            print("   - Actualiza yt-dlp: pip install --upgrade yt-dlp")
        elif plataforma == "spotify":
            print("\n💡 Spotify:")
            print("   - Spotify requiere cuenta premium y autenticación")
            print("   - Considera usar YouTube Music en su lugar")


def mostrar_menu():
    """Muestra el menú principal"""
    print("\n" + "=" * 60)
    print("🎵 CONVERTIDOR A MP3 MULTI-PLATAFORMA")
    print("=" * 60)
    print("\n📱 Plataformas soportadas:")
    print("   🎥 YouTube | 📘 Facebook | 📸 Instagram | 🎵 TikTok")
    print("   🐦 Twitter | 🎧 SoundCloud | 🎬 Vimeo | y más...")
    print("\n¿Qué deseas hacer?")
    print("1. Descargar audio completo")
    print("2. Descargar y recortar audio (de minuto X a minuto Y)")
    print("3. Salir")
    print()


def mostrar_info_inicio():
    """Muestra información inicial"""
    print("🎵 Convertidor a MP3 Multi-Plataforma")
    print("   Extrae audio de videos de redes sociales")
    print("   Con opción de recorte personalizado\n")


def main():
    mostrar_info_inicio()

    convertidor = ConvertidorMP3()

    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción (1-3): ").strip()

        if opcion == "3":
            print("\n👋 ¡Hasta luego!")
            break

        if opcion not in ["1", "2"]:
            print("❌ Opción inválida")
            continue

        url = input("\n🔗 Ingresa la URL del video/audio: ").strip()

        if not url:
            print("❌ URL vacía")
            continue

        # Detectar plataforma
        plataforma, plataforma_nombre = convertidor.detectar_plataforma(url)
        print(f"\n✅ Plataforma detectada: {plataforma_nombre}")

        if opcion == "1":
            convertidor.descargar_audio_completo(url)
        elif opcion == "2":
            convertidor.descargar_audio_recortado(url)

        continuar = input("\n¿Convertir otro audio? (s/n): ").strip().lower()
        if continuar != "s":
            print("\n👋 ¡Hasta luego!")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido")
        sys.exit(0)
