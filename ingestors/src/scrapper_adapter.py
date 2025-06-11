import asyncio
from playwright.async_api import Page, BrowserContext, Browser, TimeoutError
import random
import logging
#from config import BASE_USER_AGENTS
from src.config import BASE_USER_AGENTS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



async def initialize_browser_page(playwright, headless: bool = True) -> tuple[Browser, Page]:
    """Inicializa un nuevo navegador y página de Playwright."""
    user_agent = random.choice(BASE_USER_AGENTS)
    browser = await playwright.chromium.launch(
        headless=headless,
        args=["--no-sandbox", "--disable-setuid-sandbox"]
    )
    page = await browser.new_page(user_agent=user_agent)
    logging.info(f"Navegador y página inicializados con User-Agent: {user_agent}")
    return browser, page

async def navigate_and_wait(page: Page, url: str, wait_until_state: str = 'networkidle', timeout: int = 90000):
    """Navega a una URL y espera a un estado de la red."""
    logging.info(f"Navegando a: {url}")
    await page.goto(url, wait_until=wait_until_state, timeout=timeout)
    logging.info(f"Navegación completada para: {url}")

async def handle_cookie_consent(page: Page, selectors: list[str], timeout: int = 5000, sleep_after_click: tuple = (2, 4)):
    """Intenta hacer clic en un botón de aceptación de cookies."""
    logging.info("Intentando manejar el pop-up de cookies si está presente...")
    combined_selector = ", ".join(selectors)
    try:
        cookie_accept_locator = page.locator(combined_selector)
        if await cookie_accept_locator.is_visible(timeout=timeout):
            logging.info("Pop-up de cookies detectado. Intentando hacer clic en el botón de aceptar.")
            await cookie_accept_locator.click()
            await page.wait_for_loadstate('networkidle', timeout=10000)
            await asyncio.sleep(random.uniform(*sleep_after_click))
            logging.info("Clic en el botón de cookies exitoso. Página estabilizada.")
        else:
            logging.info("No se detectó pop-up de cookies o ya fue manejado/no aplicable.")
    except TimeoutError:
        logging.info("Tiempo de espera agotado al esperar el pop-up de cookies, probablemente no apareció.")
    except Exception as e:
        logging.warning(f"Error inesperado al intentar manejar el pop-up de cookies: {e}")

async def scroll_to_bottom(page: Page, scroll_delay: tuple = (3000, 5000), max_scrolls: int = 5):
    """
    Desplaza la página hacia abajo para cargar contenido dinámico.
    Devuelve True si se detectó algún desplazamiento de contenido.
    """
    logging.info(f"Desplazándose al final de la página para cargar contenido dinámico (hasta {max_scrolls} scrolls).")
    previous_height = -1
    scroll_count = 0
    while scroll_count < max_scrolls:
        current_height = await page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            logging.info("No más contenido para cargar. Fin del desplazamiento.")
            break
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(random.uniform(scroll_delay[0]/1000, scroll_delay[1]/1000))
        previous_height = current_height
        scroll_count += 1
        logging.info(f"Desplazamiento {scroll_count} completado. Altura actual: {current_height}px")
    if scroll_count > 0:
        return True
    return False

async def human_like_delay(min_sec: float, max_sec: float):
    """Introduce una pausa aleatoria para simular comportamiento humano."""
    delay = random.uniform(min_sec, max_sec)
    logging.debug(f"Pausa simulada de {delay:.2f} segundos.")
    await asyncio.sleep(delay)

async def extract_text_content(locator, default_value="N/A", timeout=5000):
    """Extrae el text_content de un locator de forma segura."""
    try:
        await locator.wait_for(state='attached', timeout=timeout)
        text = await locator.text_content(timeout=timeout)
        if text:
            return text.strip()
    except TimeoutError:
        # Changed: Removed .selector as it's not a direct attribute of Locator
        logging.warning(f"Tiempo de espera agotado al esperar el texto para el locator. (Possibly: {locator})") 
    except Exception as e:
        # Changed: Removed .selector
        logging.warning(f"Error al obtener texto para el locator (Possibly: {locator}): {e}")
    return default_value