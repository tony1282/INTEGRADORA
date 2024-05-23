from flask import Flask, render_template, url_for, redirect

app = Flask(__name__)

@app.route("/") #diccionario de rutas 
def index():
    titulo = 'inicio 2'
    return render_template('index.html', titulo= titulo)

@app.route("/sobre_nosotros") #diccionario de rutas 
def sobre_nosotros():
    return render_template('sobre_nosotros.html')

@app.route("/layout") #diccionario de rutas 
def layout():
    return render_template('layout.html')

@app.route("/error")
def error():
    return render_template('error.html')


@app.route("/dasboard")
def dasboard():
    return render_template('dasboard.html')

if __name__ == '__main__':
    app.run(debug=True, port= 8080)

    #activar entorno virtual .venv\Scripts\activate
    #correr aplicacion python app\app.py run