from playwright.sync_api import sync_playwright
import time

# --- CONFIGURACIÓN ---
OUTPUT_FILE = "mi_lista_peru.m3u"
BASE_URL = "https://www.tvporinternet2.com"

# Lista de canales (Asegúrate que los .html sean correctos)
CANALES = [
    {"nombre": "Disney Channel", "url": "disney-channel-en-vivo-por-internet.html", "grupo": "Infantil"},
    {"nombre": "Star Channel", "url": "star-channel-en-vivo-por-internet.html", "grupo": "Cine"},
    {"nombre": "Cartoon Network", "url": "cartoon-network-en-vivo-por-internet.html", "grupo": "Infantil"},
    {"nombre": "ESPN 5", "url": "espn-5-en-vivo-por-internet.html", "grupo": "Deportes"},
    {"nombre": "Azteca 7", "url": "azteca-7-en-vivo-por-internet.html", "grupo": "Mexico"},
]

def obtener_token_con_navegador(page, url_parcial):
    full_url = f"{BASE_URL}/{url_parcial}"
    print(f"--- Procesando: {full_url} ---")
    
    # Variable para guardar el m3u8 si lo encontramos
    m3u8_found = None

    # Función que se activa con cada petición de red que hace el navegador
    def handle_request(request):
        nonlocal m3u8_found
        # Buscamos peticiones que contengan .m3u8 y 'token'
        if ".m3u8" in request.url and "token=" in request.url:
            print(f"¡Capturado! {request.url[:60]}...")
            m3u8_found = request.url

    # Activamos la "escucha" de red
    page.on("request", handle_request)

    try:
        # 1. Ir a la página
        page.goto(full_url, timeout=60000)
        
        # 2. Esperar un poco a que carguen los scripts y anuncios
        # A veces el video tarda unos segundos en iniciar la petición
        page.wait_for_timeout(8000) # Esperar 8 segundos
        
        # Si aun no lo tenemos, intentamos buscar si hay iframes y entrar en ellos
        if not m3u8_found:
            print("Buscando en iframes...")
            for frame in page.frames:
                try:
                    # A veces hay que forzar la carga del iframe
                    frame.wait_for_load_state("networkidle", timeout=2000)
                except:
                    pass
        
    except Exception as e:
        print(f"Error navegando: {e}")
    finally:
        # Dejamos de escuchar para no mezclar canales
        page.remove_listener("request", handle_request)

    return m3u8_found

def main():
    with sync_playwright() as p:
        # Lanzamos el navegador (headless=True significa sin ventana visible)
        browser = p.chromium.launch(headless=True)
        
        # Contexto con User Agent real para engañar al servidor
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            
            for canal in CANALES:
                link = obtener_token_con_navegador(page, canal["url"])
                
                if link:
                    f.write(f'\n#EXTINF:-1 group-title="{canal["grupo"]}" tvg-logo="", {canal["nombre"]}\n')
                    
                    # --- CAMBIO AQUÍ ---
                    # Agregamos el User-Agent al final para que el reproductor de la TV no sea bloqueado
                    ua_string = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    f.write(f'{link}|User-Agent={ua_string}\n') 
                    # -------------------
                else:
                    print(f"FALLO: No se encontró token para {canal['nombre']}")

        browser.close()

if __name__ == "__main__":
    main()
