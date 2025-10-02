from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head><title>Crimson IT Policy Generator - Test</title></head>
    <body>
        <h1>Crimson IT Policy Generator</h1>
        <p>Test version running successfully!</p>
        <p>If you see this, Flask is working correctly.</p>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "message": "Test app running"}

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)