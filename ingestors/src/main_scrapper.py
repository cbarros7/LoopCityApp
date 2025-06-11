import asyncio
import logging
import argparse
import json # Para guardar en JSON si no usamos DB
from datetime import datetime

# Importar los scrapers
from eventbrite.app.eventbrite_scraper import scrape_eventbrite
from meetup.app.meetup_scraper import scrape_meetup
from src.config import (MEETUP_CATEGORY_URLS,
                    EVENTBRIT_CATEGORY_URLS
                    )

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    logging.info("Iniciando la ejecución principal del scraper.")

    # --- Configuración CLI ---
    parser = argparse.ArgumentParser(description="Ejecuta el scraper de Eventbrite, Meetup o ambos.")
    parser.add_argument('scraper_name', type=str, choices=['eventbrite', 'meetup', 'ambos'],
                        help="El nombre del scraper a ejecutar: 'eventbrite', 'meetup', o 'ambos'.")
    args = parser.parse_args()

    # --- URLs de Scrapers ---
    # eventbrite_url = "https://www.eventbrite.com/d/spain--madrid/science-and-tech--events/" 

    all_scraped_events = []

    # --- Ejecución basada en el argumento CLI ---
    if args.scraper_name == 'eventbrite' or args.scraper_name == 'ambos':
        logging.info("Iniciando el scraper de Eventbrite...")
        eventbrite_events = await scrape_eventbrite(EVENTBRIT_CATEGORY_URLS) # Ya no pasamos la colección
        all_scraped_events.extend(eventbrite_events)
        logging.info(f"Eventbrite: {len(eventbrite_events)} eventos recopilados.")
    
    if args.scraper_name == 'meetup' or args.scraper_name == 'ambos':
        logging.info("Iniciando el scraper de Meetup...")
        meetup_events = await scrape_meetup(MEETUP_CATEGORY_URLS) # Ya no pasamos la colección
        all_scraped_events.extend(meetup_events)
        logging.info(f"Meetup: {len(meetup_events)} eventos recopilados.")
    
    logging.info(f"Todos los scrapers seleccionados han finalizado. Total de eventos recopilados: {len(all_scraped_events)}")

    # --- Guardar los resultados en un archivo JSON (temporalmente, si no hay DB) ---
    output_filename = f"all_scraped_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(all_scraped_events, f, ensure_ascii=False, indent=4)
        logging.info(f"Todos los datos recopilados guardados en '{output_filename}'")
    except Exception as e:
        logging.error(f"Error al guardar los datos en JSON: {e}")

if __name__ == "__main__":
    asyncio.run(main())