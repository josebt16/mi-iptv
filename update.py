import requests
import re
import time

# --- CONFIGURACIÓN ---
OUTPUT_FILE = "mi_lista_peru.m3u"
SITIO_BASE = "https://www.tvporinternet2.com"

# Lista de canales que quieres rastrear. 
# Debes buscar la URL exacta en la web y ponerla aquí.
# He llenado algunos basados en tus capturas.
CANALES = [
    {"nombre": "Disney Channel", "url": "disney-channel-en-vivo-por-internet.html", "grupo": "Infantil"},
    {"nombre": "Disney Junior", "url": "disney-junior-en-vivo-por-internet.html", "grupo": "Infantil"},
    {"nombre": "Cartoon Network", "url": "cartoon-network-en-vivo-por-internet.html", "grupo": "Infantil"},
    {"nombre": "Nick", "url": "nick-en-vivo-por-internet.html", "grupo": "Infantil"},
    {"nombre": "Discovery Kids", "url": "discovery-kids-en-vivo-por-internet.html", "grupo": "Infantil"},
    {"nombre": "Star Channel", "url": "star-channel-en-vivo-por-internet.html", "grupo": "Cine"},
    # Agrega aquí el resto de canales siguiendo el formato...
]

# Headers para parecer un navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.tvporinternet2.com/",
}

def obtener_m3u8(slug_url):
    full_url = f"{SITIO_BASE}/{slug_url}"
    print(f"Buscando en: {full_url}")
    
    try:
        # PASO 1: Entrar a la página principal del canal
        s = requests.Session()
        resp = s.get(full_url, headers=HEADERS)
        
        if resp.status_code != 200:
            print(f"Error cargando página: {resp.status_code}")
            return None

        # PASO 2: Buscar el IFRAME del reproductor
        # Buscamos algo como: <iframe src="https://..." ...>
        iframe_match = re.search(r'<iframe[^>]+src=["\'](https?://[^"\']+)["\']', resp.text)
        
        if not iframe_match:
            print("No se encontró iframe del reproductor.")
            return None
            
        iframe_url = iframe_match.group(1)
        print(f"Iframe encontrado: {iframe_url}")

        # PASO 3: Entrar al iframe para sacar el token
        # Importante: Actualizamos el Referer para que el iframe crea que venimos de la web
        headers_iframe = HEADERS.copy()
        headers_iframe["Referer"] = full_url
        
        resp_iframe = s.get(iframe_url, headers=headers_iframe)
        
        # PASO 4: Buscar el .m3u8 con token dentro del código del iframe
        # Buscamos patrones comunes de Clappr o variables JS
        # Pattern: "source": "https://....m3u8?token=..."
        m3u8_match = re.search(r'["\'](https?://[^"\']+\.m3u8\?token=[^"\']+)["\']', resp_iframe.text)
        
        if m3u8_match:
            link = m3u8_match.group(1)
            # A veces los enlaces tienen barras invertidas \ escapadas, las quitamos
            link = link.replace('\\', '')
            return link
        else:
            print("No se encontró .m3u8 en el iframe.")
            # Intento secundario: buscar cualquier m3u8
            m3u8_generic = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', resp_iframe.text)
            if m3u8_generic:
                return m3u8_generic.group(1).replace('\\', '')
            return None

    except Exception as e:
        print(f"Excepción: {e}")
        return None

def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for canal in CANALES:
            link = obtener_m3u8(canal["url"])
            
            if link:
                f.write(f'\n#EXTINF:-1 group-title="{canal["grupo"]}" tvg-logo="", {canal["nombre"]}\n')
                # Agregamos los headers al link para que funcione en el reproductor final
                f.write(f'{link}|User-Agent={HEADERS["User-Agent"]}\n')
                print(f"✔ {canal['nombre']} actualizado.")
            else:
                print(f"✘ {canal['nombre']} falló.")
            
            # Esperamos 1 segundo para no saturar la web y que no nos bloqueen
            time.sleep(1)

if __name__ == "__main__":
    main()
  
