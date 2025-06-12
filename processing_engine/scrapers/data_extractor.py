import re
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import urljoin, urlparse

class DataExtractor:
    
    @staticmethod
    def extract_emails(soup: BeautifulSoup) -> List[str]:
        email_pattern = r'\b[A-Za-z][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        text = soup.get_text()
        emails = re.findall(email_pattern, text)
        return list(set(emails))

    @staticmethod
    def extract_addresses(soup: BeautifulSoup) -> List[str]:
        address_pattern = r'(\d{2}-\d{3})\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż-]+(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż-]+)*)'
        postcode_finder = re.compile(r'\d{2}-\d{3}')
        
        found_addresses = set()
        potential_elements = soup.find_all(text=postcode_finder)
        
        for element_text in potential_elements:
            clean_text = ' '.join(element_text.split())
            matches = re.findall(address_pattern, clean_text)
            
            for match in matches:
                full_address = ' '.join(match)
                found_addresses.add(full_address)
        
        return list(found_addresses)
    
    @staticmethod
    def extract_phone_numbers(soup: BeautifulSoup) -> List[str]:
        phone_pattern = r'\b(?:\+?\d[()\-\s\.]?){8,15}\d\b'
        
        text = soup.get_text()
        matches = re.findall(phone_pattern, text)
        
        found_phones = set()
        for match in matches:
            cleaned_number = re.sub(r'\D', '', match)
            
            if len(cleaned_number) == 11 and cleaned_number.startswith('48'):
                normalized_number = cleaned_number[2:]
                found_phones.add(normalized_number)
                
            elif len(cleaned_number) == 9:
                found_phones.add(cleaned_number)

        return list(found_phones)

    @staticmethod
    def extract_links(soup: BeautifulSoup, base_url: str) -> List[str]:
        found_links = set()
        for link_tag in soup.find_all('a', href=True):
            href = link_tag.get('href').strip()
            absolute_link = urljoin(base_url, href)
            parsed_link = urlparse(absolute_link)
            if parsed_link.scheme in ['http', 'https'] and parsed_link.netloc:
                found_links.add(absolute_link)
        return list(found_links)