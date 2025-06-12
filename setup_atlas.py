from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def setup_atlas_database():
    """Inicjalizacja MongoDB oraz kolekcji"""
    try:
        mongodb_url = os.getenv('MONGODB_URL')
        
        if not mongodb_url:
            print("Nie znaleziono MONGODB_URL w .env")
            print("Upewnij się, że plik .env posiada URL połączeniowy do twojego klastra MongoDB Atlas")
            return
        
        print("Łączenie z MongoDB Atlas")
        
        # Połącz z MongoDB Atlas
        client = MongoClient(mongodb_url)
        
        # Testuj połączenie
        client.admin.command('ping')
        print("Połączono!")
        
        # Utwórz bazę danych
        db = client['web_scraper']
        
        # Utwórz kolekcje z indeksami
        scraped_data = db['scraped_data']
        jobs = db['jobs']
        
        # Utwórz indeksy dla lepszej wydajności
        print("Tworzenie indeksów")
        scraped_data.create_index("url")
        scraped_data.create_index("created_at")
        scraped_data.create_index("job_id")
        
        jobs.create_index("job_id", unique=True)
        jobs.create_index("created_at")
        jobs.create_index("status")
        
        print("Baza danych web_scraper utworzona!")
        print("Kolekcje oraz indeksy utworzone!")
        
        # Wprowadzanie testowych danych
        sample_job = {
            'job_id': 'atlas-test-001',
            'urls': ['https://example.com'],
            'status': 'completed',
            'created_at': datetime.utcnow(),
            'results_count': 0
        }
        
        result = jobs.insert_one(sample_job)
        print(f"Prztkładowe zadanie dodane z ID: {result.inserted_id}")
        
        # Pokaż statystyki bazy danych
        collections = db.list_collection_names()
        print(f"Ilość kolekcji w bazie danych: {collections}")
        
        client.close()
        print("Konfiguracja atlas powiodła się")
        
    except Exception as e:
        print(f"Konfiguracja nie powiodła się: {e}")
        print("\nSprawdź:")
        print("1. URL Połączeniowe w .env")
        print("2. Czy twoje IP jest na białej liscie w MongoDB Atlas")
        print("3. Zweryfikuj dane logowania użytkownika")
        print("4. Czy masz zainstalowany dnspython: pip install dnspython")

if __name__ == "__main__":
    setup_atlas_database()