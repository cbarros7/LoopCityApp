import asyncio
from playwright.async_api import async_playwright, Page, TimeoutError
import logging
from datetime import datetime
import re
import json
from src.config import MEETUP_COOKIE_SELECTORS

# Importar funciones comunes del adaptador (asegúrate de que este archivo exista y funcione)
from src.scrapper_adapter import initialize_browser_page, navigate_and_wait, handle_cookie_consent, scroll_to_bottom, human_like_delay, extract_text_content



async def scrape_meetup(urls: dict):
    """
    Realiza el scraping de eventos de Meetup para las URLs proporcionadas,
    iterando sobre cada categoría y extrayendo sus datos.

    Args:
        urls (dict): Un diccionario donde las claves son los nombres de las categorías
                     y los valores son las URLs de Meetup a scrapear.
    Returns:
        list: Una lista de diccionarios, donde cada diccionario representa un evento
              con sus detalles.
    """
    logging.info("Iniciando scraping de Meetup.com para múltiples categorías...")
    all_events_data = []
    processed_event_ids = set() # Para evitar eventos duplicados si aparecen en múltiples categorías

    async with async_playwright() as p:
        browser, page = await initialize_browser_page(p, headless=True)

        try:
            # Iterar sobre cada URL de categoría proporcionada
            for category_name, current_url in urls.items():
                logging.info(f"Scrapeando categoría: '{category_name}' desde URL: {current_url}")

                logging.info(f"Navegando a la URL de Meetup con timeout extendido y 'domcontentloaded': {current_url}")
                await navigate_and_wait(page, current_url, wait_until_state='domcontentloaded', timeout=120000)

                await handle_cookie_consent(page, MEETUP_COOKIE_SELECTORS)

                logging.info("Comenzando el desplazamiento para cargar más contenido (y datos JSON) en la página de listado.")
                await scroll_to_bottom(page, max_scrolls=10) # Ajusta max_scrolls si es necesario

                json_script_locator = page.locator('script[id="__NEXT_DATA__"][type="application/json"]')

                try:
                    await json_script_locator.wait_for(state='attached', timeout=30000)
                    json_content = await json_script_locator.text_content()
                    app_data = json.loads(json_content)
                    logging.info(f"Datos JSON de __NEXT_DATA__ extraídos y parseados para '{category_name}'.")

                except TimeoutError:
                    logging.error(f"Tiempo de espera agotado para encontrar el script '__NEXT_DATA__' para '{category_name}'. No se pudo extraer la información del evento desde JSON.")
                    screenshot_path = f"screenshot_meetup_no_json_script_{category_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    await page.screenshot(path=screenshot_path)
                    logging.error(f"Captura de pantalla guardada en: {screenshot_path}")
                    continue # Continuar con la siguiente URL si falla la extracción JSON
                except json.JSONDecodeError as e:
                    logging.error(f"Error al decodificar el JSON de '__NEXT_DATA__' para '{category_name}': {e}")
                    continue # Continuar con la siguiente URL si falla la decodificación JSON

                apollo_data = app_data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})

                if not apollo_data:
                    logging.warning(f"No se encontraron datos en '__APOLLO_STATE__' para '{category_name}'. La estructura puede haber cambiado o los datos no están disponibles.")

                    # Fallback a DOM scraping si no se encuentran datos de Apollo
                    logging.info("Intentando extraer URLs e IDs de eventos mediante DOM scraping como fallback.")
                    event_link_elements_locator = page.locator('a[id="event-card-in-search-results"]')

                    try:
                        await event_link_elements_locator.first.wait_for(state='visible', timeout=30000)
                        event_elements = await event_link_elements_locator.all()
                        logging.info(f"Se encontraron {len(event_elements)} enlaces de eventos mediante DOM scraping (fallback) para '{category_name}'.")

                        for event_element in event_elements:
                            raw_link = await event_element.get_attribute('href')
                            if raw_link:
                                cleaned_link = re.sub(r'\?.*$', '', raw_link)
                                event_id_match = re.search(r'/events/(\d+)/?$', cleaned_link)
                                event_id = event_id_match.group(1) if event_id_match else None

                                if event_id and event_id not in processed_event_ids:
                                    event_info = {
                                        "source": "Meetup",
                                        "category": category_name, # Añadido el campo de categoría
                                        "event_id": event_id,
                                        "link": cleaned_link if cleaned_link.startswith("http") else f"https://www.meetup.com{cleaned_link}",
                                        "scraped_at": datetime.now().isoformat(),
                                        "title": "N/A (DOM Fallback)",
                                        "description": "N/A (DOM Fallback)",
                                        "date_time_raw": "N/A (DOM Fallback)",
                                        "attendees_count": 0,
                                        "address": "N/A (DOM Fallback)",
                                        "latitude": None,
                                        "longitude": None
                                    }
                                    all_events_data.append(event_info)
                                    processed_event_ids.add(event_id)
                                    logging.info(f"Meetup (Fallback - '{category_name}'): Evento extraído (ID: {event_id}, Título: '{event_info.get('title', 'N/A')}').")
                                    await human_like_delay(0.1, 0.5)

                    except TimeoutError:
                        logging.warning(f"Tiempo de espera agotado para encontrar enlaces de eventos mediante DOM scraping para '{category_name}'. No se pudo extraer información.")
                    except Exception as dom_e:
                        logging.error(f"Error durante el fallback DOM scraping para '{category_name}': {dom_e}")

                    continue # Continuar con la siguiente URL después de intentar el fallback

                events_raw = {}
                venues_raw = {}

                for key, value in apollo_data.items():
                    if key.startswith("Event:"):
                        events_raw[value.get('id')] = value
                    elif key.startswith("Venue:"):
                        venues_raw[value.get('id')] = value

                if not events_raw:
                    logging.warning(f"No se encontraron objetos de evento en el JSON extraído después de filtrar (aparentamente apollo_data no contenía Event: objetos) para '{category_name}'.")
                    continue # Continuar con la siguiente URL si no hay eventos

                logging.info(f"Se encontraron {len(events_raw)} eventos únicos en los datos JSON para '{category_name}'.")

                for event_id, event_data_json in events_raw.items():
                    if event_id in processed_event_ids:
                        logging.debug(f"DEBUG: Saltando ID de evento duplicado ya procesado: {event_id}.")
                        continue

                    event_info = {
                        "source": "Meetup",
                        "category": category_name, # Añadido el campo de categoría
                        "event_id": event_id,
                        "link": event_data_json.get('eventUrl', 'N/A'),
                        "title": event_data_json.get('title', 'N/A'),
                        "description": event_data_json.get('description', 'N/A'),
                        "date_time_raw": event_data_json.get('dateTime', 'N/A'),
                        "attendees_count": event_data_json.get('rsvps', {}).get('totalCount', 0),
                        "scraped_at": datetime.now().isoformat()
                    }

                    venue_ref = event_data_json.get('venue')
                    if venue_ref and isinstance(venue_ref, dict):
                        venue_id = venue_ref.get('id') or venue_ref.get('__ref', '').split(':')[-1]

                        if venue_id and venue_id in venues_raw:
                            venue_details = venues_raw[venue_id]
                            event_info["venue_name"] = venue_details.get('name', 'N/A')
                            event_info["address"] = venue_details.get('address', 'N/A')
                            event_info["city"] = venue_details.get('city', 'N/A')
                            event_info["state"] = venue_details.get('state', 'N/A')
                            event_info["country"] = venue_details.get('country', 'N/A')
                            event_info["latitude"] = venue_details.get('lat', None)
                            event_info["longitude"] = venue_details.get('lon', None)
                        else:
                            logging.warning(f"Referencia de lugar '{venue_id}' no encontrada en 'venues_raw' para el evento {event_id}.")
                    else:
                        logging.warning(f"No se encontró referencia de lugar para el evento {event_id} o no tiene el formato esperado.")

                    all_events_data.append(event_info)
                    processed_event_ids.add(event_id)
                    logging.info(f"Meetup ({category_name}): Evento extraído (ID: {event_id}, Título: '{event_info.get('title', 'N/A')}'). Total único extraído: {len(all_events_data)}")

                    await human_like_delay(0.5, 2) # Pausa humanizada entre extracciones de eventos

            logging.info(f"Meetup: Finalizado el scraping de todas las categorías. Total de eventos únicos extraídos: {len(all_events_data)}")

        except Exception as e:
            logging.error(f"Error general inesperado durante el scraping de Meetup: {e}")
            logging.error(f"URL intentada: {page.url}")
            screenshot_path = f"screenshot_meetup_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path)
            logging.error(f"Captura de pantalla guardada en: {screenshot_path}")
        finally:
            if browser:
                await browser.close()

            # Guardar todos los eventos en un solo archivo JSON
            if all_events_data:
                try:
                    output_filename = 'all_scraped_meetup_events.json'
                    with open(output_filename, 'w', encoding='utf-8') as f:
                        json.dump(all_events_data, f, ensure_ascii=False, indent=4)
                    logging.info(f"Todos los datos de {len(all_events_data)} eventos guardados en '{output_filename}'")
                except Exception as e:
                    logging.error(f"Error al guardar el archivo JSON final '{output_filename}': {e}")
    return all_events_data