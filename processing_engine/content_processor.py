from bs4 import BeautifulSoup
from typing import Dict
from .scrapers.data_extractor import DataExtractor

def process_content(data: Dict) -> Dict:
    """Przetwarzanie zawartości pojedyńczej strony"""
    if data['status'] != 'success' or not data['content']:
        return {
            'url': data['url'],
            'status': data['status'],
            'extracted_data': None
        }

    try:
        soup = BeautifulSoup(data['content'], 'html.parser')

        url = data['url']

        extracted_data = {
            'emails': DataExtractor.extract_emails(soup),
            'addresses': DataExtractor.extract_addresses(soup),
            'phone_numbers': DataExtractor.extract_phone_numbers(soup),
            'links': DataExtractor.extract_links(soup, base_url=url)
        }

        return {
            'url': data['url'],
            'status': 'processed',
            'extracted_data': extracted_data
        }

    except Exception as e:
        return {
            'url': data['url'],
            'status': f'processing_error_{str(e)}',
            'extracted_data': None
        }