from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from flask_socketio import SocketIO, emit
import uuid
from datetime import datetime
import threading
import sys
import os
import json
import pytz
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.utils.database import DatabaseManager
from processing_engine.scraper_engine import scrape_job

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
socketio = SocketIO(app, cors_allowed_origins="*")

db_manager = DatabaseManager()

def to_local_time(utc_dt):
    """Konwertowanie UTC na czas Polski"""
    if not utc_dt:
        return ""
    local_tz = pytz.timezone('Europe/Warsaw')
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_dt.strftime('%Y-%m-%d %H:%M:%S')

app.jinja_env.filters['to_localtime'] = to_local_time

@app.route('/')
def index():
    """Panel główny"""
    recent_jobs = list(db_manager.jobs.find().sort('created_at', -1).limit(10))
    return render_template('index.html', recent_jobs=recent_jobs)

@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    """Interfejs scrapowania"""
    if request.method == 'POST':
        urls_text = request.form.get('urls', '')
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        if not urls:
            return render_template('scrape.html', error="Podaj chociaż jedno URL")
        
        # Stwórz nowe zadanie
        job_id = str(uuid.uuid4())
        job_data = {
            'job_id': job_id,
            'urls': urls,
            'status': 'pending',
            'created_at': datetime.utcnow(),
            'results_count': 0
        }
        
        db_manager.save_job(job_data)
        def run_scraping():
            try:
                db_manager.update_job_status(job_id, 'running')
                successful_count = scrape_job(urls, job_id)
                db_manager.update_job_status(job_id, 'completed')
                db_manager.update_job_field(job_id, 'results_count', successful_count)
                socketio.emit('job_completed', {
                    'job_id': job_id,
                    'status': 'completed',
                    'results_count': successful_count
                })
            except Exception as e:
                db_manager.update_job_status(job_id, f'error: {str(e)}')
                socketio.emit('job_error', {
                    'job_id': job_id,
                    'error': str(e)
                })

        threading.Thread(target=run_scraping, daemon=True).start()

        return redirect(url_for('job_status', job_id=job_id))

    return render_template('scrape.html')

@app.route('/job/<job_id>')
def job_status(job_id):
    job = db_manager.jobs.find_one({'job_id': job_id})
    if not job:
        return "Nie znaleziono zadania", 404
    
    results = list(db_manager.scraped_data.find({'job_id': job_id}))
    summary = []
    if results:
        for result in results:
            summary.append({
                'url': result.get('url', 'N/A'),
                'counts': {
                    'emails': len(result.get('emails', [])),
                    'phone_numbers': len(result.get('phone_numbers', [])),
                    'addresses': len(result.get('addresses', [])),
                    'links': len(result.get('links', []))
                }
            })
    return render_template('job_status.html', job=job, summary=summary)

def json_converter(o):
    """Funkcja pomocna dla konwertowania do string"""
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, uuid.UUID):
        return str(o)

@app.route('/job/<job_id>/download')
def download_results(job_id):
    job_results = list(db_manager.scraped_data.find({'job_id': job_id}, {'_id': 0}))
    json_output = json.dumps(
        job_results, 
        indent=2, 
        default=json_converter, 
        ensure_ascii=False
    )

    return Response(
        json_output,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment;filename=results_{job_id}.json'}
    )

@app.route('/api/job/<job_id>/status')
def api_job_status(job_id):
    job = db_manager.jobs.find_one({'job_id': job_id})
    if not job:
        return jsonify({'error': 'Nie znaleziono zadania'}), 404
    
    job['_id'] = str(job['_id'])
    return jsonify(job)

@app.route('/results')
def results():
    """Wyświetlanie oraz filtrowania wszystkich zadań"""
    status_filter = request.args.get('status', 'all')
    url_filter = request.args.get('url', '')
    date_from_filter = request.args.get('date_from', '')
    filters = {
        'status': status_filter,
        'url': url_filter,
        'date_from': date_from_filter
    }
    query = {}
    if status_filter and status_filter != 'all':
        query['status'] = status_filter
    
    if url_filter:
        query['urls'] = {'$regex': url_filter, '$options': 'i'}
        
    if date_from_filter:
        try:
            start_date = datetime.strptime(date_from_filter, '%Y-%m-%d')
            query['created_at'] = {'$gte': start_date}
        except ValueError:
            pass
    page = int(request.args.get('page', 1))
    per_page = 15
    skip = (page - 1) * per_page
    jobs_cursor = db_manager.jobs.find(query).sort('created_at', -1)
    total_count = db_manager.jobs.count_documents(query)
    jobs = list(jobs_cursor.skip(skip).limit(per_page))

    for job in jobs:
        job['_id'] = str(job['_id'])

    return render_template('results.html',
                           jobs=jobs,
                           page=page,
                           per_page=per_page,
                           total_count=total_count,
                           filters=filters)

@app.route('/api/results')
def api_results():
    results = list(db_manager.scraped_data.find().limit(100).sort('created_at', -1))
    for result in results:
        result['_id'] = str(result['_id'])
    return jsonify(results)

@app.route('/results/<job_id>')
def view_results(job_id):
    job = db_manager.jobs.find_one({'job_id': job_id})
    if not job:
        return "Nie znaleziono zadania", 404

    results = list(db_manager.scraped_data.find({'job_id': job_id}).sort('created_at', -1))
    for r in results:
        r['_id'] = str(r['_id'])

    return render_template('results_detail.html', job=job, results=results)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
