from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Oxyx Builds</title>
        <style>
            body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; padding: 50px; }
            h1 { font-size: 3em; }
        </style>
    </head>
    <body>
        <h1>🚀 Oxyx Builds</h1>
        <p>Running on Vercel!</p>
    </body>
    </html>
    """

# Vercel handler
def handler(request):
    return app(request)
