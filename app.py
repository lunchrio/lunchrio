from flask import Flask
from flask import render_template
from flask_bootstrap import Bootstrap
import os

app = Flask(__name__)
Bootstrap(app)

@app.route('/')
def hello_world():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)