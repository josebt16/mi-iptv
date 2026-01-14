import cloudscraper # Usamos cloudscraper en vez de requests directo
import re
import time

# --- CONFIGURACIÓN ---
OUTPUT_FILE = "mi_lista_peru.m3u"
SITIO_BASE = "https://www.tvporinternet2.com"

# IMPORTANTE: Verifica que estas URLs existan entrando manualmente a la web.
# Copia la parte final de la URL del navegador.
CANALES = [
    {"nombre": "Disney Channel", "url": "disney-channel-en-vivo-por-internet.html", "grupo": "Infantil"},
    {"nombre": "Star Channel", "url": "star-channel-en-vivo-por-internet.html", "grupo": "Cine"},
    {"nombre": "Cartoon Network", "url": "cartoon-network-en-vivo-por-internet.html", "grupo": "Infantil"},
    {"nombre": "ESPN 5", "url": "espn-5-en-vivo-por-internet.html", "grupo": "Deportes"}, # Agregado basado en tu captura
]

def obtener_m3u8(slug_url):
    full_url = f"{SITIO_BASE}/{slug_url}"
    print(f"--------------------------------------------------")
    print(f"Procesando: {canal['nombre']} ({full_url})")
    
    # Creamos un scraper que simula ser un navegador real
    scraper = cloudscraper.create_scraper()
    
    try:
        # PASO 1: Entrar a la página principal
        resp = scraper.get(full_url)
        
        if resp.status_code != 200:
            print(f"ERROR HTTP: {resp.status_code}")
            return None

        # PASO 2: Buscar el IFRAME
        # Buscamos <iframe src="...">
        iframe_match = re.search(r'<iframe[^>]+src=["\'](https?://[^"\']+)["\']', resp.text)
        
        if not iframe_match:
            print("FALLO: No se encontró iframe en el HTML.")
            # Debug: Imprimir un poco del HTML para ver qué devolvió (si es bloqueo o error 404)
            print(f"Snippet HTML: {resp.text[:200]}...") 
            return None
            
        iframe_url = iframe_match.group(1)
        print(f"Iframe encontrado: {iframe_url}")

        # PASO 3: Entrar al iframe (con Referer correcto)
        # El sitio del video (laligafutboldeportes) valida que vengas de tvporinternet2
        headers = {"Referer": full_url}
        resp_iframe = scraper.get(iframe_url, headers=headers)
        
        # PASO 4: Buscar el .m3u8 con token
        # Regex ajustado para capturar cualquier m3u8 con token
        m3u8_match = re.search(r'["\'](https?://[^"\']+\.m3u8\?token=[^"\']+)["\']', resp_iframe.text)
        
        if m3u8_match:
            link = m3u8_match.group(1).replace('\\', '')
            print("¡EXITO! Enlace extraído.")
            return link
        else:
            print("FALLO: No se encontró patrón .m3u8 en el iframe.")
            print(f"Snippet Iframe: {resp_iframe.text[:200]}...")
            return None

    except Exception as e:
        print(f"EXCEPCION: {e}")
        return None

if __name__ == "__main__":
    count = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for canal in CANALES:
            link = obtener_m3u8(canal["url"])
            
            if link:
                f.write(f'\n#EXTINF:-1 group-title="{canal["grupo"]}" tvg-logo="", {canal["nombre"]}\n')
                f.write(f'{link}\n') # Cloudscraper ya maneja headers, pero el player final quizás no.
                count += 1
            
            time.sleep(2) # Pausa ética
            
    print(f"--------------------------------------------------")
    print(f"Resumen: Se actualizaron {count} canales.")
    
