import asyncio
from playwright.async_api import async_playwright, Page
import logging
from datetime import datetime
import re

# Importar funciones comunes del adaptador
from src.scrapper_adapter import initialize_browser_page, navigate_and_wait, handle_cookie_consent, scroll_to_bottom, human_like_delay, extract_text_content
from src.config import EVENTBRITE_COOKIE_SELECTORS


async def scrape_eventbrite(urls: str):  # Ya no recibe events_collection
    logging.info("Iniciando scraping de Eventbrite...")

    all_events_data = []  # Lista para almacenar los eventos
    processed_event_ids = set()
    
    current_page_number = 1
    total_pages_available = 1

    async with async_playwright() as p:
        browser, page = await initialize_browser_page(p, headless=True)

        try:
            for category_name, current_url in urls.items(): 
                while current_page_number <= total_pages_available:
                    page_url = f"{current_url}?page={current_page_number}"
                    await navigate_and_wait(page, page_url, wait_until_state='domcontentloaded', timeout=120000)

                    if current_page_number == 1:
                        await handle_cookie_consent(page, EVENTBRITE_COOKIE_SELECTORS)

                    logging.info(f"--- Procesando Página {current_page_number} (Eventbrite) ---")

                    # Extraer JSON de __SERVER_DATA__ para obtener info de paginación
                    try:
                        server_data_json = await page.evaluate("() => window.__SERVER_DATA__")

                        if (
                            server_data_json
                            and "search_data" in server_data_json
                            and "events" in server_data_json["search_data"]
                            and "pagination" in server_data_json["search_data"]["events"]
                        ):
                            pagination_info = server_data_json["search_data"]["events"]["pagination"]
                            total_pages_available = pagination_info.get("page_count", 1)
                            logging.info(
                                f"Información de paginación de __SERVER_DATA__: Total Pages: {total_pages_available}, "
                                f"Current Page: {pagination_info.get('page_number')}"
                            )
                        else:
                            logging.warning("No se encontró la información de paginación en window.__SERVER_DATA__. Asumiendo 1 página total.")

                    except Exception as e:
                        logging.warning(f"Error al extraer window.__SERVER_DATA__: {e}. Esto podría afectar la paginación.")

                    logging.info("Esperando elementos de evento y forzando el desplazamiento en la página actual.")
                    try:
                        await page.wait_for_selector('a.event-card-link[data-event-id]:has(h3), div.event-card', timeout=30000, state='attached')
                        logging.info("Elementos de Eventbrite detectados en el DOM para la página actual.")
                    except TimeoutError:
                        logging.warning(f"No se encontraron elementos de evento en la Página {current_page_number} después de la espera inicial.")
                        if current_page_number == 1:
                            logging.warning("No se encontraron eventos en la primera página. El scraping podría no haber funcionado o no hay eventos para los criterios.")
                        break

                    await scroll_to_bottom(page)

                    event_elements_on_page = await page.locator('a.event-card-link[data-event-id]').all()
                    if not event_elements_on_page:
                        event_elements_on_page = await page.locator('div.event-card').all()
                        if event_elements_on_page:
                            logging.info("Usando selector de fallback para eventos: 'div.event-card'")

                    logging.info(f"Se encontraron {len(event_elements_on_page)} eventos potenciales en la Página {current_page_number} después del desplazamiento.")

                    if not event_elements_on_page and current_page_number > 1:
                        logging.info(f"No se encontraron eventos en la Página {current_page_number}. Asumiendo el final de la paginación.")
                        break
                    elif not event_elements_on_page and current_page_number == 1:
                        logging.warning("No se encontraron eventos en la primera página. El scraping podría no haber funcionado o no hay eventos para los criterios.")
                        break

                    for i, event_element in enumerate(event_elements_on_page):
                        try:
                            event_id = await event_element.get_attribute('data-event-id')
                            link = await event_element.get_attribute('href')

                            if not event_id and link:
                                match = re.search(r'e=(\d+)', link)
                                if match:
                                    event_id = match.group(1)

                            if event_id and event_id.strip() in processed_event_ids:
                                logging.debug(f"DEBUG: Saltando ID de evento duplicado en memoria (Eventbrite): {event_id}. (Índice: {i})")
                                await human_like_delay(0.5, 1.5)
                                continue

                            if event_id and link:
                                event_info = {
                                    "source": "Eventbrite",
                                    "category": category_name,
                                    "event_id": event_id.strip(),
                                    "link": link.strip(),
                                    "scraped_at": datetime.now().isoformat()
                                }
                                all_events_data.append(event_info)
                                processed_event_ids.add(event_id.strip())

                                logging.info(
                                    f"Eventbrite: Evento extraído (ID: {event_id}). "
                                    f"Únicos totales: {len(all_events_data)} (Página {current_page_number})"
                                )
                            else:
                                logging.debug(
                                    f"DEBUG: Saltando evento {i} porque falta el ID o el Link (ID: '{event_id}', Link: '{link}')."
                                )

                        except Exception as e:
                            logging.warning(f"Error al extraer o procesar detalles para el evento {i}: {e}")
                            await human_like_delay(2.0, 5.0)

                    current_page_number += 1
                    await human_like_delay(5.0, 12.0)

                logging.info(f"Scraping de Eventbrite completado. Total de eventos únicos recopilados: {len(all_events_data)}")

        except Exception as e:
            logging.error(f"Error general inesperado durante el scraping de Eventbrite: {e}")
            logging.error(f"URL intentada: {page.url}")
            screenshot_path = f"screenshot_eventbrite_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path)
            logging.error(f"Captura de pantalla guardada en: {screenshot_path}")

        finally:
            if browser:
                await browser.close()

    return all_events_data
