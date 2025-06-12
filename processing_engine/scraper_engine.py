import asyncio
import aiohttp
from bs4 import BeautifulSoup
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor
from typing import List, Dict
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.utils.database import DatabaseManager
from processing_engine.content_processor import process_content

class ScraperEngine:
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or cpu_count()
        self.db_manager = DatabaseManager()
        self.session = None

    async def create_session(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100)
        )

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def fetch_url(self, url: str) -> Dict:
        """Wyodrębnienie pojedyńczej strony asynchronicznie"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return {
                        'url': url,
                        'content': content,
                        'status': 'success'
                    }
                else:
                    return {
                        'url': url,
                        'content': None,
                        'status': f'error_{response.status}'
                    }
        except Exception as e:
            return {
                'url': url,
                'content': None,
                'status': f'error_{str(e)}'
            }

    async def scrape_urls_batch(self, urls: List[str]) -> List[Dict]:
        """Wyodrębnienie wielu stron asynchronicznie"""
        await self.create_session()

        try:
            fetch_tasks = [self.fetch_url(url) for url in urls]
            fetched_data = await asyncio.gather(*fetch_tasks, return_exceptions=False)
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                processed_data = list(executor.map(process_content, fetched_data))

            return processed_data

        finally:
            await self.close_session()

    def save_results(self, results: List[Dict], job_id: str):
        successful_results = 0

        for result in results:
            if result['status'] == 'processed' and result['extracted_data']:
                data_to_save = {
                    'job_id': job_id,
                    'url': result['url'],
                    **result['extracted_data']
                }
                self.db_manager.save_scraped_data(data_to_save)
                successful_results += 1

        self.db_manager.update_job_status(job_id, 'completed', successful_results)

        return successful_results


def scrape_job(urls: List[str], job_id: str):
    engine = ScraperEngine()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        results = loop.run_until_complete(engine.scrape_urls_batch(urls))
        successful_count = engine.save_results(results, job_id)
        return successful_count
    finally:
        loop.close()
