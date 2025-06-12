# web-scraper-app
Full-stack web application designed to scrape websites for the following information:
- E-mails
- Phone numbers (Polish format)
- Post-code + city location (Polish format)
- Any links on the webpage

It features a web interface for submitting scraping jobs, viewing status in real-time, and browsing/filtering all past results.

The app is containerized using Docker and Docker Compose for easy setup and deployment.
It uses:
 - Docker
 - Docker compose
 - Flask
 - MongoDB Atlas

## Prerequisites
 - Docker
 - Docker Compose

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/mmierzwa2002/web-scraper-app
cd web-scraper-app
```

### 2. Configure .env
 - Create a file named .env in the root directory of the project
 - Add the following variables:
 MONGODB_URL= your MongoDB Atlas connection string
 FLASK_SECRET_KEY="generate a strong random string here"
 MAX_WORKERS= number of CPUs used in scraping

### 3. Build and Run with Docker Compose
1. Make sure Docker is running and you have Docker Compose installed
2. Navigate to the project directory in a terminal
3. Type docker-compose up --build

### 4. (Optional) Initialize the Database
You can run a one-time script to create database indexes for optimal performance, and to check whether MongoDB connection is working in general:
 - Open a new terminal window
 - Type docker ps
 - Next, run docker exec -it <container-name> python
 - setup_atlas.py

### 5. Access the Application
The app will be available at: http://localhost:5000/
