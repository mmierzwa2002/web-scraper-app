from pymongo import MongoClient
from typing import Dict
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        mongodb_url = os.getenv('MONGODB_URL')
        
        if not mongodb_url:
            raise ValueError("URL do połączenia z MongoDB nieustawione, ustaw w pliku .env")
        
        try:
            self.client = MongoClient(
                mongodb_url,
                serverSelectionTimeoutMS=10000,
                retryWrites=True
            )
            self.client.admin.command('ping')
            print("Połączono z MongoDB Atlas")
            
        except Exception as e:
            print(f"Połączenie z MongoDB Atlas nie powiodło się, {e}")
            print("Sprawdź:")
            print("1. Plik .env posiada poprawny URL połączeniowy")
            print("2. IP jest na białej liście w Atlas")
            print("3. Dane użytkownika bazy danych są poprawne")
            raise
            
        self.db = self.client['web_scraper']
        self.scraped_data = self.db['scraped_data']
        self.jobs = self.db['jobs']
    
    def save_scraped_data(self, data: Dict):
        """Save scraped data to MongoDB Atlas"""
        data['created_at'] = datetime.utcnow()
        try:
            result = self.scraped_data.insert_one(data)
            print(f"Dane zapisane do Atlas z ID: {result.inserted_id}")
            return result
        except Exception as e:
            print(f"Nie udało się zapisać danych do bazy danych: {e}")
            raise
    
    def get_scraped_data(self, limit: int = 100):
        """Pobierz dane z Atlas"""
        try:
            return list(self.scraped_data.find().limit(limit).sort('created_at', -1))
        except Exception as e:
            print(f"Nie udało się pobrać danych z Atlas: {e}")
            raise
    
    def save_job(self, job_data: Dict):
        """Zapisz informacje zadania do Atlas"""
        try:
            result = self.jobs.insert_one(job_data)
            print(f"Zadanie zapisane do Atlas z ID: {result.inserted_id}")
            return result
        except Exception as e:
            print(f"Nie udało się zapisać zadania do Atlas: {e}")
            raise
    
    def update_job_status(self, job_id: str, status: str, results_count: int = 0):
        """Aktualizacja statusu zadania w Atlas"""
        update_data = {
            'status': status,
            'updated_at': datetime.utcnow()
        }
        if status == 'completed':
            update_data['completed_at'] = datetime.utcnow()
            update_data['results_count'] = results_count
        
        try:
            result = self.jobs.update_one(
                {'job_id': job_id},
                {'$set': update_data}
            )
            print(f"Status zadania {job_id} zaktualizowany do: {status}")
            return result
        except Exception as e:
            print(f"Nie udało się zaktualizować statusu zadania: {e}")
            raise

    def update_job_field(self, job_id: str, field: str, value):
        """Zaktualizuj konkretne pole zadania"""
        try:
            result = self.jobs.update_one(
                {'job_id': job_id},
                {'$set': {field: value, 'updated_at': datetime.utcnow()}}
            )
            print(f"Zaktualizowano pole '{field}' dla zadania {job_id}")
            return result
        except Exception as e:
            print(f"Nie udało się zaktualizować pola '{field}' w zadaniu {job_id}: {e}")
            raise

    def close_connection(self):
        """Zamknij połączenie"""
        if self.client:
            self.client.close()
            print("Zamknięto połączenie Atlas")
