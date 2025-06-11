# config.py

# --- Configuración del Gestor de Proxies (proxy_manager.py) ---
PROXY_LIST_URLS = {
    # Agrega o elimina URLs de listas de proxies aquí.
    # Si una URL requiere Playwright (ej. por contenido JS), asegúrate de que el parser lo maneje.
    "geonode_com": "https://www.geonode.com/free-proxy-list",
    # "proxydb_net": "http://proxydb.net" # Ejemplo de otro sitio, descomentar si es necesario
}

PAGES_PER_PROXY_LIST_URL = 1 # Páginas a scrapear por CADA URL de lista de proxies (mantén bajo para pruebas)
PROXY_EXPIRATION_HOURS = 2   # Los proxies se consideran "activos" por este tiempo

# Retrasos para el scraping de listas de proxies (para evitar bloqueos)
MIN_DELAY_BETWEEN_PROXY_SITES = 3
MAX_DELAY_BETWEEN_PROXY_SITES = 6
MIN_DELAY_BETWEEN_PROXY_PAGES = 1
MAX_DELAY_BETWEEN_PROXY_PAGES = 3

# Encabezado User-Agent para el scraping de listas de proxies
PROXY_SCRAPER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# --- Configuración del Scraper de Eventbrite (eventbrite_scraper.py) ---
EVENTBRITE_BASE_URL = "https://www.eventbrite.com"
EVENTBRITE_SEARCH_URL = "https://www.eventbrite.com/d/spain--madrid--85682783/all-events/"

# URLs específicas para las categorías de Tecnología y Actividades Sociales, filtradas por "Esta semana"
MEETUP_CATEGORY_URLS = {
    "Tecnologia": "https://www.meetup.com/es-ES/find/?location=es--Madrid&source=EVENTS&categoryId=546&eventType=inPerson&dateRange=this-week",
    "Actividades sociales": "https://www.meetup.com/es-ES/find/?location=es--Madrid&source=EVENTS&categoryId=652&eventType=inPerson&dateRange=this-week"
}

# Configuración específica de Meetup
MEETUP_COOKIE_SELECTORS = [
    'button[id="onetrust-accept-btn-handler"]',
    'button:has-text("Aceptar todas")'
]

EVENTBRIT_CATEGORY_URLS = {
    "Tecnologia": "https://www.eventbrite.com/d/spain--madrid/science-and-tech--events--this-weekend/",
}

# Configuración específica de Eventbrite
EVENTBRITE_COOKIE_SELECTORS = [
    '[data-automation="gdpr-agree-button"]',
    'button:has-text("Aceptar todas")',
    'button:has-text("Accept All")'
]

# Base User-Agents para el scraping general
BASE_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/125.0.0.0",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/125.0.0.0 Mobile/15E144 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Brave Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"
]

MAX_EVENTBRITE_PAGE_ATTEMPTS = 5 # Máximos intentos para obtener una sola página de Eventbrite con diferentes proxies
EVENTBRITE_PLAYWRIGHT_TIMEOUT = 30000 # Timeout para las operaciones de página de Playwright (30 segundos)
EVENTBRITE_MIN_DELAY = 5 # Retraso mínimo entre solicitudes exitosas a Eventbrite
EVENTBRITE_MAX_DELAY = 10 # Retraso máximo entre solicitudes exitosas a Eventbrite

# User-Agent que simula un navegador real para Eventbrite (importante para evitar detecciones)
EVENTBRITE_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# Número máximo de páginas de Eventbrite a raspar en una ejecución.
# Ten en cuenta que Eventbrite usa "infinite scroll", por lo que esta paginación simple
# solo es un límite de iteraciones. Para un scraping completo, necesitarías simular el scroll.
MAX_EVENTBRITE_PAGES_TO_SCRAPE = 3