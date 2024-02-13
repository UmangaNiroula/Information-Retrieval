from flask import Flask, render_template, request
from search_engine import execute_search

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    results = execute_search(query, "storage")  # Call execute_search function from search_engine.py
    return render_template('index.html', results=results, query=query)

if __name__ == '__main__':
    app.run(debug=True)
