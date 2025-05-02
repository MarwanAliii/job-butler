import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from Render!"

@app.route('/scrape')
def scrape():
    return "Scraper triggered!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Use PORT from env, fallback to 10000
    app.run(host='0.0.0.0', port=port)
