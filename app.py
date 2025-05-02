from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from Flask!"

@app.route('/scrape')
def scrape():
    # Your scraping code here
    return "Scrape triggered!"
