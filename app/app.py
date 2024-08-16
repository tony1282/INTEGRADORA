import os
import re
import psycopg2
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, TableStyle, Paragraph, Spacer
from reportlab.pdfgen import canvas
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from werkzeug.utils import secure_filename
from flask import Flask, render_template, url_for, redirect, request, flash, Blueprint, jsonify, send_file
from flask_wtf.csrf import CSRFProtect

from werkzeug.security import generate_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from Models.ModelUser import ModuleUser
from Models.entities.user import User

app = Flask(__name__)
csrf=CSRFProtect() 

#-------------------------------conexion---------------------------------------------
def get_db_connection():
    try:
        conn = psycopg2.connect(host="localhost",
                                dbname="spvbma",
                                user="postgres",
                                password="gojo")
        return conn
    except psycopg2.Error as error:
        print(f"Error al conectar a la base de datos: {error}")
        return None
    
#--------------------------------Login------------------------------------------
Login_manager_app=LoginManager(app)
@Login_manager_app.user_loader
def load_user(idusuarios):
    return ModuleUser.get_by_id(get_db_connection(),idusuarios)


#-------------------------------- SECRET KEY ---------------------------
app.secret_key='chistosa'

#----------------------------------RUTAS---------------------------------------
@app.route("/")
def login():
    return render_template('sesion.html')

@app.route("/recuperar_contrasenia")
def recuperar():
    return render_template('actualizar_contrasenia.html')

@app.route("/index")
@login_required
def index():
    return render_template('index.html')

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

def allowed_username(nombre_usuario):
    # Define el patrón de la expresión regular para letras y números sin espacios ni caracteres especiales
    pattern = re.compile(r'^[a-zA-Z0-9]+$')
    # Comprueba si el nombre de usuario coincide con el patrón
    if pattern.match(nombre_usuario):
        return True
    else:
        return False

#------------------------------------------consulta de prendas-------------------------------------------
def lista_prendas():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_prenda, categoria, nombre_marca, color, talla, precio_prenda FROM prenda WHERE estado=true ORDER BY id_prenda")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Convertir los resultados en una lista de diccionarios
    prenda = [{'id_prenda': row[0], 'categoria': row[1], 'nombre_marca': row[2], 'color': row[3], 'talla': row[4], 'precio_prenda': row[5]} for row in rows]
    return prenda

# ------------------------------------------consulta de categorias-----------------------------------------------
def lista_categorias():
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM categoria ORDER BY id_categoria ASC ')
    categorias=cur.fetchall()
    cur.close()
    conn.close()
    return categorias

# --------------------------------------consulta de roles-----------------------------------------------------------
def lista_rol():
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM roles ORDER BY id_rol ASC ')
    roles=cur.fetchall()
    cur.close()
    conn.close()
    return roles

#-------------------------------------consulta de tallas---------------------------------------------------------------
def lista_tallas():
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM tallas ORDER BY id_tallas ASC')
    tallas=cur.fetchall()
    cur.close()
    conn.close()
    return tallas

#-------------------------------------consulta de colores---------------------------------------------------------------
def lista_colores():
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM colores ORDER BY id_color ASC')
    colores=cur.fetchall()
    cur.close()
    conn.close()
    return colores

#----------------------------------consulta de marcas------------------------------------------------------------------
def lista_marcas():
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM marcas ORDER BY id_marca ASC')
    marcas=cur.fetchall()
    cur.close()
    conn.close()
    return marcas

#---------------------------------------consulta de proveedor-----------------------------------------------------
def lista_proveedores():
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM proveedores ORDER BY id_proveedores ASC')
    proveedores=cur.fetchall()
    cur.close()
    conn.close()
    return proveedores

#-------------------------------------------consulta de detalles apartado--------------------------------------
def detapar():
    conn = get_db_connection()  
    cur = conn.cursor()
    cur.execute('SELECT * FROM apade ORDER BY categoria ASC;')
    detapas = cur.fetchall()
    cur.close()
    conn.close()
    return detapas

#-----------------------------------------------------PAGINADOR---------------------------------------------------------
def paginador(sql_count,sql_lim,in_page,per_pages):
    page = request.args.get('page', in_page, type=int)
    per_page = request.args.get('per_page', per_pages, type=int)

    offset = (page - 1) * per_page

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(sql_count)
    total_items = cursor.fetchone()['count']

    cursor.execute(sql_lim, (per_page, offset))
    items = cursor.fetchall()

    cursor.close()
    conn.close()

    total_pages = (total_items + per_page - 1) // per_page

    return items, page, per_page, total_items, total_pages

def paginador1(sql_count: str, sql_lim: str, search_query: str, in_page: int, per_pages: int) -> tuple[list[dict], int, int, int, int]:
# Obtener parámetros de paginación
    page = request.args.get('page', in_page, type=int)
    per_page = request.args.get('per_page', per_pages, type=int)

    # Validar los valores de entrada
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1

    offset = (page - 1) * per_page

    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Ejecutar consulta para contar el total de elementos que coinciden con la búsqueda
        cursor.execute(sql_count, (f"%{search_query}%",f"%{search_query}%"))
        total_items = cursor.fetchone()['count']

        # Ejecutar consulta para obtener elementos paginados que coinciden con la búsqueda
        cursor.execute(sql_lim, (f"%{search_query}%",f"%{search_query}%", per_page, offset))
        items = cursor.fetchall()

    except psycopg2.Error as e:
        print(f"Error en la base de datos: {e}")
        items = []
        total_items = 0
    finally:
        # Asegurar el cierre de la conexión
        cursor.close()
        conn.close()

    # Calcular el total de páginas
    total_pages = (total_items + per_page - 1) // per_page

    return items, page, per_page, total_items, total_pages

#-----------------------------------------------------------------------------------------------------------------------
@app.route('/descargar_reporte')
def descargar_reporte():
    proveedor_id = request.args.get('proveedor_id')

    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM public.prenda WHERE estado=true AND id_proveedores={0}".format(proveedor_id))
    prendas = cursor.fetchall()

    # Crear un archivo PDF en memoria
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Encabezado
    estilos = getSampleStyleSheet()
    elementos = []

    for prenda in prendas:
        titulo =Paragraph (f"Reporte de prendas del proveedor {prenda[2]}", estilos['Title'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 12))  # Agrega espacio debajo del título
        # Crear los datos de la tabla
        data = [['Categoría', 'Talla', 'Color', 'Precio', 'Marca', 'Cantidad']]  # Encabezados de la tabla
        fila = [prenda[3], prenda[9], prenda[8], f"${prenda[10]:.2f}", prenda[4], prenda[11]]
        data.append(fila)

    # Crear la tabla
    tabla = Table(data)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Color de fondo de los encabezados
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Color del texto de los encabezados
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alineación de todo el texto
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Fuente de los encabezados
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Espaciado inferior de los encabezados
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Color de fondo de las celdas
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Bordes de la tabla
    ]))

    # Añadir la tabla al documento
    elementos.append(tabla)
    
    # Construir el documento
    doc.build(elementos)

    # Guardar el PDF en memoria
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"reporte_proveedor_{prenda[2]}.pdf", mimetype='application/pdf')

#--------------------------------------------------------inicio de sesion --------------------------------------------
@app.route('/loguear', methods=('GET','POST'))
def loguear():
    if request.method == 'POST':
        nombre_usuario=request.form['nombre_usuario']
        contrasenia=request.form['contrasenia']
        user=User(0,nombre_usuario,contrasenia,None,None)
        loged_user=ModuleUser.login(get_db_connection(),user)

        if loged_user!= None:
            if loged_user.contrasenia:
                login_user(loged_user)
                return redirect(url_for('dashboard'))
            else:
                flash('Nombre de usuario y/o contraseña incorrecta.')
                return redirect(url_for('login'))
        else:
            flash('Nombre de usuario y/o contraseña incorrecta.')
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#--------------------------------------------------------actualizar contrasenia--------------------------------------------
@app.route('/actualizar_contraseña', methods=['POST'])
def actualizar_contraseña():
    correo_electronico = request.form['correo_electronico']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if new_password != confirm_password:
        flash("Las contraseñas no coinciden.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM usuarios WHERE correo_electronico = '{}'".format(correo_electronico))
    user = cursor.fetchone()

    if user:
        hashed_password = generate_password_hash(new_password)
        cursor.execute("UPDATE usuarios SET contrasenia = '{}' WHERE correo_electronico = '{}'", (hashed_password, correo_electronico))
        conn.commit()
        flash("Contraseña actualizada correctamente.")
    else:
        flash("Correo electrónico no registrado.")
    
    conn.close()
    return redirect(url_for('login'))

#------------------------------------------------- CRUD usuarios --------------------------------------------------------

@app.route("/usuarios")
@login_required
def usuarios():
    search_query = request.args.get('buscar', '', type=str)
    sql_count = 'SELECT COUNT(*) FROM usuarios WHERE estado=true AND (nombre_usuario ILIKE %s OR correo_electronico ILIKE %s);'
    sql_lim = 'SELECT * FROM usuarios WHERE estado=true AND (nombre_usuario ILIKE %s OR correo_electronico ILIKE %s) ORDER BY id_usuario DESC LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count, sql_lim, search_query, 1, 5)
    return render_template('usuarios.html',
                            usuarios=paginado[0],
                            page=paginado[1],
                            per_page=paginado[2],
                            total_items=paginado[3],
                            total_pages=paginado[4],
                            search_query=search_query)

@app.route("/usuarios/papelera")
@login_required
def usuarios_papelera():
    search_query = request.args.get('buscar', '', type=str)
    sql_count = 'SELECT COUNT(*) FROM usuarios WHERE estado=false AND (nombre_usuario ILIKE %s OR correo_electronico ILIKE %s);'
    sql_lim = 'SELECT * FROM usuarios WHERE estado=false AND (nombre_usuario ILIKE %s OR correo_electronico ILIKE %s) ORDER BY id_usuario DESC LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count, sql_lim, search_query, 1, 5)
    return render_template('usuarios_papelera.html',
                            usuarios=paginado[0],
                            page=paginado[1],
                            per_page=paginado[2],
                            total_items=paginado[3],
                            total_pages=paginado[4],
                            search_query=search_query)

@app.route("/usuarios/nuevo")
@login_required
def usuario_nuevo():
    titulo = "Nuevo usuario"
    return render_template('usuario_nuevo.html', titulo=titulo, roles=lista_rol())

@app.route('/usuarios/crear', methods=('GET', 'POST'))
@login_required
def usuarios_crear():
    if request.method == 'POST':
        nombre_usuario= request.form['nombre_usuario']
        if allowed_username(nombre_usuario):
            apellido_paterno= request.form['apellido_paterno']
            apellido_materno= request.form['apellido_materno']
            celular_usuario= request.form['celular_usuario']
            domicilio_usuario= request.form['domicilio_usuario']
            contrasenia= request.form['contrasenia']
            Pass= generate_password_hash(contrasenia)
            correo_electronico= request.form['correo_electronico']
            rol= request.form['id_rol']
            estado = True
            creado = datetime.now()
            editado =datetime.now() 

            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            sql_validar="SELECT COUNT(*) FROM usuarios WHERE correo_electronico = '{}'".format(correo_electronico)
            cur.execute(sql_validar)
            existe = cur.fetchone()['count']
            if existe:
                cur.close()
                conn.close()
                flash('ERROR: El correo seleccionado ya existe. intente con otro.')
                return redirect(url_for('usuario_nuevo'))
            else:
                sql="INSERT INTO usuarios(nombre_usuario, apellido_paterno, apellido_materno, celular_usuario, domicilo_usuario, contrasenia, correo_electronico, rol, estado, creado, editado ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                valores=(nombre_usuario,apellido_paterno,apellido_materno,celular_usuario,domicilio_usuario,Pass,correo_electronico,rol,estado,creado,editado)
                cur.execute(sql,valores)
                conn.commit()
                cur.close()
                conn.close()
                flash('¡Usuario agregado exitosamente!')
                return redirect(url_for('usuarios'))
        else:
            flash('Error: El correo de usuario no cumple con las características. Intente con otro.')
            return redirect(url_for('usuario_nuevo'))
    return redirect(url_for('usuario_nuevo'))

@app.route('/usuarios/<string:id>')
@login_required
def usuarios_detalles(id):
    titulo="Detalles de usuario"
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM usuarios INNER JOIN roles ON roles.id_rol=usuarios.rol WHERE id_usuario={0}'.format(id))
    usuarios=cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('usuario_detalles.html',titulo=titulo, usuarios=usuarios[0])

@app.route('/usuarios/papelera/<string:id>')
@login_required
def usuarios_detallesRes(id):
    titulo="Detalles de usuario"
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM usuarios INNER JOIN roles  ON roles.id_rol=usuarios.rol WHERE id_usuario={0}'.format(id))
    usuarios=cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('usuario_detallesRes.html',titulo=titulo, usuarios=usuarios[0])

@app.route('/usuarios/restaurar/<string:id>')
@login_required
def usuarios_restaurar(id):
    estado = True
    editado = datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    #sql="DELETE FROM usuarios WHERE id_usuario={0}".format(id)
    sql="UPDATE usuarios SET  estado=%s,editado=%s WHERE id_usuario=%s"
    valores=(estado,editado,id)
    cur.execute(sql,valores)
    conn.commit()
    cur.close()
    conn.close()
    flash('Usuario restaurado')
    return redirect(url_for('usuarios'))

@app.route('/usuarios/editar/<string:id>')
@login_required
def usuarios_editar(id):
    if current_user.rol == 1:
        titulo="Editar Usuario"
        conn=get_db_connection()
        cur=conn.cursor()
        cur.execute('SELECT * FROM usuarios WHERE id_usuario={0}'.format(id))
        usuarios=cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return render_template('usuarios_editar.html',titulo=titulo, usuarios=usuarios[0],roles=lista_rol())
    else:
        return redirect(url_for('usuarios'))

@app.route('/usuarios/editar/<string:id>', methods=['POST'])
@login_required
def usuarios_actualizar(id):
    if request.method == 'POST':
        nombre_usuario= request.form['nombre_usuario']
        apellido_paterno= request.form['apellido_paterno']
        apellido_materno= request.form['apellido_materno']
        celular_usuario= request.form['celular_usuario']
        domicilio_usuario= request.form['domicilio_usuario']
        correo_electronico= request.form['correo_electronico']
        rol= request.form['id_rol']
        editado =datetime.now() 

        conn=get_db_connection()
        cur=conn.cursor()
        sql="UPDATE public.usuarios SET nombre_usuario=%s, apellido_paterno=%s, apellido_materno=%s, celular_usuario=%s, domicilo_usuario=%s, correo_electronico=%s, rol=%s, editado=%s WHERE id_usuario=%s"
        valores=(nombre_usuario,apellido_paterno,apellido_materno,celular_usuario,domicilio_usuario, correo_electronico,rol,editado,id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()
        flash("usuario editado correctamente")
    return redirect(url_for('usuarios'))

@app.route('/usuarios/eliminar/<string:id>') 
@login_required
def usuarios_eliminar(id):
    if current_user.rol == 1:
        estado=False
        editado = datetime.now()
        conn = get_db_connection()
        cur = conn.cursor()
        #sql="DELETE FROM usuarios WHERE id_usuario={0}".format(id)
        sql="UPDATE usuarios SET  estado=%s, editado=%s WHERE id_usuario=%s"
        valores=(estado,editado,id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()
        flash('Usuario eliminado')
        return redirect(url_for('usuarios'))
    else:
        return redirect(url_for('usuarios'))

#---------------------------------------- CRUD proveedores ------------------------------------------------------------
@app.route("/proveedores")
@login_required 
def proveedores():
    search_query = request.args.get('buscar', '', type=str)
    sql_count = 'SELECT COUNT(*) FROM proveedores WHERE estado=true AND (nombre_proveedor ILIKE %s or celular_proveedor ILIKE %s);'
    sql_lim = 'SELECT * FROM proveedores WHERE estado=true AND (nombre_proveedor ILIKE %s or celular_proveedor ILIKE %s) ORDER BY id_proveedores DESC  LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count, sql_lim, search_query, 1, 5)
    return render_template('proveedores.html',
                            proveedores=paginado[0],
                            page=paginado[1],
                            per_page=paginado[2],
                            total_items=paginado[3],
                            total_pages=paginado[4],
                            search_query=search_query)

@app.route("/proveedores/papelera")
@login_required
def proveedor_papelera():
    search_query = request.args.get('buscar', '', type=str)
    sql_count = 'SELECT COUNT(*) FROM proveedores WHERE estado=false AND (nombre_proveedor ILIKE %s or celular_proveedor ILIKE %s);'
    sql_lim = 'SELECT * FROM proveedores WHERE estado=false AND (nombre_proveedor ILIKE %s or celular_proveedor ILIKE %s) ORDER BY id_proveedores DESC  LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count, sql_lim, search_query, 1, 5)
    return render_template('proveedor_papelera.html',
                            proveedores=paginado[0],
                            page=paginado[1],
                            per_page=paginado[2],
                            total_items=paginado[3],
                            total_pages=paginado[4],
                            search_query=search_query)

@app.route("/proveedores/nuevo")
@login_required
def proveedores_nuevo():
    titulo = "Nuevo proveedor"
    return render_template('proveedores_nuevo.html', titulo=titulo)

@app.route('/proveedores/crear', methods=('GET', 'POST'))
@login_required
def proveedores_crear():
    if request.method == 'POST':
        nombre_proveedor= request.form['nombre']
        celular_proveedor= request.form['celular']
        estado=True
        creado= datetime.now()
        modificado = datetime.now()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO proveedores (nombre_proveedor , celular_proveedor, estado, creado, modificado)'
                    'VALUES (%s, %s, %s, %s, %s)',
                    (nombre_proveedor,celular_proveedor, estado, creado, modificado))
        conn.commit()
        cur.close()
        conn.close()
        flash('proveedor agregado exitosamente!')
        return redirect(url_for('proveedores'))
    return redirect(url_for('proveedores_nuevo'))

@app.route('/proveedores/<string:id>')
@login_required
def proveedores_detalles(id):
    titulo="Detalles de proveedor"
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM proveedores WHERE id_proveedores={0}'.format(id))
    proveedores=cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('proveedores_detalles.html',titulo=titulo, proveedores=proveedores[0])

@app.route('/proveedores/detalles/<string:id>')
@login_required
def proveedores_detallesRes(id):
    titulo="Detalles de proveedor"
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM proveedores WHERE id_proveedores={0}'.format(id))
    proveedores=cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('proveedores_detallesRes.html',titulo=titulo, proveedores=proveedores[0])

@app.route('/proveedores/editar/<string:id>')
@login_required
def proveedores_editar(id):
    if current_user.rol == 1:
        titulo="Editar Proveedor"
        conn=get_db_connection()
        cur=conn.cursor()
        cur.execute('SELECT * FROM proveedores WHERE id_proveedores={0}'.format(id))
        proveedores=cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return render_template('proveedores_editar.html',titulo=titulo, proveedor=proveedores[0])
    else:
        return redirect(url_for('proveedores'))

@app.route('/proveedores/editar/<string:id>', methods=['POST'])
@login_required
def proveedores_actualizar(id):
    if request.method == 'POST':
        nombre_proveedor= request.form['nombre_proveedor']
        celular_proveedor= request.form['celular_proveedor']
        estado=True
        creado= datetime.now()
        modificado = datetime.now()

        conn=get_db_connection()
        cur=conn.cursor()
        sql="UPDATE proveedores SET nombre_proveedor=%s,celular_proveedor=%s, estado=%s,creado=%s,modificado=%s WHERE id_proveedores=%s"
        valores=(nombre_proveedor,celular_proveedor, estado, creado, modificado, id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()
        flash("proveedor editado correctamente")
    return redirect(url_for('proveedores'))

@app.route('/proveedores/eliminar/<string:id>')
@login_required
def proveedor_eliminar(id):
    if current_user.rol == 1:
        estado=False
        modificado= datetime.now()
        conn = get_db_connection()
        cur = conn.cursor()
        #sql="DELETE FROM proveedores WHERE id_proveedores={0}".format(id)
        sql="UPDATE proveedores SET estado=%s, modificado=%s WHERE id_proveedores=%s"
        valores=(estado,modificado,id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()
        flash('Proveedor eliminado')
        return redirect(url_for('proveedores'))
    else:
        return redirect(url_for('proveedores'))

@app.route('/proveedores/eliminar/papelera/<string:id>')
@login_required
def proveedor_restaurar(id):
    estado=True
    modificado= datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    #sql="DELETE FROM proveedores WHERE id_proveedores={0}".format(id)
    sql="UPDATE proveedores SET estado=%s, modificado=%s WHERE id_proveedores=%s"
    valores=(estado,modificado,id)
    cur.execute(sql,valores)
    conn.commit()
    cur.close()
    conn.close()
    flash('Proveedor restaurado')
    return redirect(url_for('proveedores'))  
  
#------------------------------------------CRUD prendas ----------------------------------------------------------
@app.route("/prendas")
@login_required
def prendas():
    search_query = request.args.get('buscar', '', type=str)
    sql_count= 'SELECT COUNT(*) FROM public.prendas_vista WHERE estado=true AND (categoria ILIKE %s OR color ILIKE %s);'
    sql_lim='SELECT * FROM public.prendas_vista WHERE estado=true AND (categoria ILIKE %s OR color ILIKE %s) ORDER BY id_prenda DESC LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count, sql_lim, search_query, 1, 5)
    return render_template('prendas.html',
                            prendas=paginado[0],
                            page=paginado[1],
                            per_page=paginado[2],
                            total_items=paginado[3],
                            total_pages=paginado[4],
                            search_query=search_query)

@app.route("/prenda/papelera")
@login_required
def prenda_papelera():
    search_query = request.args.get('buscar', '', type=str)
    sql_count= 'SELECT COUNT(*) FROM public.prendas_vista WHERE estado=false AND (categoria ILIKE %s OR color ILIKE %s);'
    sql_lim='SELECT * FROM public.prendas_vista WHERE estado=false AND (categoria ILIKE %s OR color ILIKE %s) ORDER BY id_prenda DESC LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count, sql_lim, search_query, 1, 5)
    return render_template('prendas_papelera.html',
                            prendas=paginado[0],
                            page=paginado[1],
                            per_page=paginado[2],
                            total_items=paginado[3],
                            total_pages=paginado[4],
                            search_query=search_query)

@app.route("/prendas/nuevo")
@login_required
def prenda_nuevo():
    titulo = "Nueva prenda"
    return render_template('prenda_nuevo.html', titulo=titulo,categorias=lista_categorias(),tallas=lista_tallas(),colores=lista_colores(),marcas=lista_marcas(),proveedores=lista_proveedores())

@app.route('/prendas/crear', methods=('GET', 'POST'))
@login_required
def prendas_crear():
    if request.method == 'POST':
        codigo_producto= request.form['codigo_prod']
        nombre_proveedor= request.form['nombre_prov']
        categoria_prenda= request.form['categoria_prenda']
        marca_prenda= request.form['marca_prenda']
        estado= True
        creado= datetime.now()
        modificado= datetime.now()
        color_prenda= request.form['color_prenda']
        talla_prenda= request.form['talla_prenda']
        precio_prenda= request.form['precio_prenda']
        cantidad= request.form['cantidad']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO prendas(codigo_producto, nombre_proveedor, categoria_prenda, marca_prenda, estado, creado, modificado, color_prenda, talla_prenda, precio_prenda,cantidad)'
	                'VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);',
                    (codigo_producto, nombre_proveedor, categoria_prenda, marca_prenda, estado, creado, modificado, color_prenda, talla_prenda, precio_prenda,cantidad))
        conn.commit()
        cur.close()
        conn.close()
        flash('¡Prenda agregada exitosamente!')
        return redirect(url_for('prendas'))
    return redirect(url_for('prenda_nuevo'))

@app.route('/prendas/<string:id>')
@login_required
def prendas_detalles(id):
    titulo="Detalles de prendas"
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM public.prenda WHERE id_prenda={0}'.format(id))
    prendas=cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('prendas_detalles.html',titulo=titulo, prendas=prendas[0])

@app.route('/prendas/detalles/<string:id>')
@login_required
def prendas_detallesRes(id):
    titulo="Detalles de prendas"
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM public.prenda WHERE id_prenda={0}'.format(id))
    prendas=cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('prendas_detallesRes.html',titulo=titulo, prendas=prendas[0])

@app.route('/prendas/editar/<string:id>')
@login_required
def prendas_editar(id):
    if current_user.rol == 1:
        titulo="Editar Prenda"
        conn=get_db_connection()
        cur=conn.cursor()
        cur.execute('SELECT * FROM prendas WHERE id_prenda={0}'.format(id))
        prendas=cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return render_template('prendas_editar.html',titulo=titulo,prendas=prendas[0],colores=lista_colores())
    else:
        return redirect(url_for('prendas'))

@app.route('/prendas/editar/<string:id>',methods=['POST'])
@login_required
def prendas_actualizar(id):
    if request.method == 'POST':
        codigo_producto= request.form['codigo_prod']
        modificado= datetime.now()
        color_prenda= request.form['color_prenda']
        precio_prenda= request.form['precio_prenda']
        cantidad= request.form['cantidad'] 

        conn=get_db_connection()
        cur=conn.cursor()
        sql="UPDATE public.prendas SET  modificado=%s, color_prenda=%s, precio_prenda=%s, cantidad=%s WHERE id_prenda=%s;"
        valores=(modificado, color_prenda, precio_prenda, cantidad, id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()
        flash("Prenda actualizada")
    return redirect(url_for('prendas'))

@app.route('/prendas/eliminar/<string:id>')
@login_required
def prendas_eliminar(id):
    if current_user.rol == 1:
        estado = False
        modificado   = datetime.now()
        conn = get_db_connection()
        cur = conn.cursor()
        #sql="DELETE FROM usuarios WHERE id_usuario={0}".format(id)
        sql="UPDATE prendas SET  estado=%s,modificado=%s WHERE id_prenda=%s"
        valores=(estado,modificado,id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()
        flash('Prenda eliminada eliminado')
        return redirect(url_for('prendas'))
    else:
        return redirect(url_for('prendas'))

@app.route('/prendas/restaurar/<string:id>')
@login_required
def prendas_restaurar(id):
    estado = True
    modificado   = datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    #sql="DELETE FROM usuarios WHERE id_usuario={0}".format(id)
    sql="UPDATE prendas SET  estado=%s,modificado=%s WHERE id_prenda=%s"
    valores=(estado,modificado,id)
    cur.execute(sql,valores)
    conn.commit()
    cur.close()
    conn.close()
    flash('Prenda restaurada')
    return redirect(url_for('prendas'))

#---------------------------------CRUD ventas ------------------------------------------------------------

@app.route("/ventas")
@login_required
def ventas():
    search_query = request.args.get('buscar', '', type=str)
    sql_count='SELECT COUNT(*) FROM vista_venta WHERE total_venta ILIKE %s OR nombre_usuario ILIKE %s;'
    sql_lim='SELECT * FROM vista_venta WHERE total_venta ILIKE %s OR nombre_usuario ILIKE %s LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count, sql_lim, search_query, 1, 5)
    return render_template('ventas.html', 
                            ventas=paginado[0],
                            page=paginado[1],
                            per_page=paginado[2],
                            total_items=paginado[3],
                            total_pages=paginado[4],
                            search_query=search_query)

@app.route('/venta_nuevo')
def venta_nuevo():
    # Calcular la suma total de los precios en el carrito
    total_precio = sum(item['precio_prenda'] for item in carrito)
    
    return render_template('venta_nuevo.html', 
                           carrito=carrito, 
                           total_precio=total_precio,
                           prendas=lista_prendas(),  # Asegúrate de tener una función para obtener la lista de prendas
                           titulo="Nueva Venta")

@app.route('/ventas/crear', methods=['POST'])
def ventas_crear():
    usuario = getattr(current_user, 'id_usuario', None)
    fecha_creacion = datetime.now()

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        total_precio = 0

        # Procesar cada prenda en el carrito
        prendas_detalle = []
        for item in carrito:
            cantidad = item.get('cantidad', 0)
            total_precio += item['precio_prenda'] 
            # Crear una descripción de la prenda para mostrar en la venta
            prendas_detalle.append(f"{item['categoria']}, {item['nombre_marca']}, {item['color']}, {item['talla']}, {item['precio_prenda']}")

        # Convertir la lista de detalles de prendas a una cadena
        prendas_string = ', '.join(prendas_detalle)

        # Insertar la venta en la base de datos y obtener el ID de la venta recién creada
        cur.execute("""
            INSERT INTO public.ventas (usuario, fecha_creacion, prenda_mostrar, total_venta) 
            VALUES (%s, %s, %s, %s) RETURNING id_venta
        """, (usuario, fecha_creacion, prendas_string, total_precio))
        id_venta = cur.fetchone()[0]
        conn.commit()

        # Insertar los detalles de la venta en la base de datos
        for item in carrito:
            cantidad = item.get('cantidad', 0)
            cur.execute("""
                INSERT INTO public.detalles_ventas (prenda, id_venta, cantidad)
                VALUES (%s, %s, %s)
            """, (item['id_prenda'], id_venta, cantidad))

        conn.commit()

        # Limpiar el carrito después de la venta
        carrito.clear()
        flash(f"Venta creada con éxito. Total: {total_precio:.2f} MX", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al crear la venta: {str(e)}", "error")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for('ventas'))

carrito = []

@app.route('/ventas/agregar_prenda', methods=['POST'])
def agregar_prenda():
    id_prenda = request.form.get('id_prenda')
    prendas = lista_prendas()

    if id_prenda:
        try:
            id_prenda = int(id_prenda)
            prenda = next((p for p in prendas if p['id_prenda'] == id_prenda), None)
            if prenda:
                carrito.append(prenda)
                print("Prenda añadida al carrito:", prenda)
                print("Carrito actual:", carrito)

                conn = get_db_connection()
                cur = conn.cursor()

                # Restar la cantidad en la tabla prendas
                cur.execute("UPDATE prendas SET cantidad = cantidad - 1 WHERE id_prenda = %s AND cantidad > 0", (id_prenda,))

                cur.execute("""
                INSERT INTO temp_carrito (nombre_marca, color, talla, precio_prenda, cantidad, categoria)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (prenda['nombre_marca'], prenda['color'], prenda['talla'], prenda['precio_prenda'], 1, prenda['categoria']))

                conn.commit()
                cur.close()
                conn.close()

        except ValueError:
            print("Error: El valor de id_prenda no es un número válido")

    return redirect(url_for('venta_nuevo'))


@app.route('/ventas/quitar_prenda', methods=['POST'])
def quitar_prenda():
    id_prenda = request.form.get('id_prenda')

    if id_prenda:
        try:
            id_prenda = int(id_prenda)
            prenda = next((p for p in carrito if p['id_prenda'] == id_prenda), None)

            if prenda:
                carrito.remove(prenda)

                conn = get_db_connection()
                cur = conn.cursor()

                # Incrementar la cantidad en la tabla prendas
                cur.execute("UPDATE prendas SET cantidad = cantidad + 1 WHERE id_prenda = %s", (id_prenda,))

                cur.execute("DELETE FROM temp_carrito WHERE id_prenda = %s", (id_prenda,))

                conn.commit()
                cur.close()
                conn.close()

        except ValueError:
            print("Error: El valor de id_prenda no es un número válido")

    return redirect(url_for('venta_nuevo'))

@app.route('/ventas/<string:id>')
@login_required
def venta_detallado(id):
    titulo = "Vista ventas"
    conn = get_db_connection()
    cur= conn.cursor()
    cur.execute('SELECT * FROM vista_venta WHERE id_venta={0}'.format(id))
    ventas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('venta_detallado.html',titulo = titulo, ventas = ventas[0])

#--------------------------- CRUD de sistema de apartado ---------------------------------------------------

@app.route("/sApartado")
@login_required
def sApartado():
    search_query = request.args.get('buscar', '', type=str)
    sql_count = 'SELECT COUNT(*) FROM apartado WHERE activo=true AND (nombre_cliente ILIKE %s OR nombre_usuario ILIKE %s);'
    sql_lim = 'SELECT * FROM apartado WHERE activo=true AND (nombre_cliente ILIKE %s OR nombre_usuario ILIKE %s) ORDER BY id_apartado DESC LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count, sql_lim, search_query, 1, 5)
    return render_template('sApartado.html',
                            apartado=paginado[0],
                            page=paginado[1],
                            per_page=paginado[2],
                            total_items=paginado[3],
                            total_pages=paginado[4],
                            search_query=search_query)

@app.route("/sApartado/papelera")
@login_required
def apartado_papelera():
    sql_count = 'SELECT COUNT(*) FROM apartado WHERE activo=false;'
    sql_lim = 'SELECT * FROM apartado WHERE activo=false ORDER BY id_apartado DESC LIMIT %s OFFSET %s;'
    paginado = paginador(sql_count,sql_lim,1,1)
    return render_template('apartado_papelera.html',
                            apartados=paginado[0],
                            page=paginado[1],
                            per_page=paginado[2],
                            total_items=paginado[3],
                            total_pages=paginado[4])
    
@app.route("/sApartado/nuevo")
@login_required
def apartado_nuevo():
    total_precio = sum(item['precio_prenda'] for item in carrito)
    return render_template('apartado_nuevo.html', 
                           detapa=detapar(), 
                           carrito=carrito, 
                           total_precio=total_precio,
                           prendas=lista_prendas())

@app.route('/sApartado/crear', methods=['GET', 'POST'])
@login_required
def apartados_crear():
    usuario = getattr(current_user, 'id_usuario', None)
    anticipo = request.form['anticipo']
    nombre_cliente = request.form['nombre_cliente']
    creado = datetime.now()
    fecha_apartado = request.form['fecha_apartado']
    fecha_limite = request.form['fecha_limite']
    editado = datetime.now()
    activo = True

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        total_precio = 0

        # Procesar cada prenda en el carrito
        prendas_detalle = []
        for item in carrito:
            cantidad = item.get('cantidad', 0)
            total_precio += item['precio_prenda'] 
            # Crear una descripción de la prenda para mostrar en la venta
            prendas_detalle.append(f"{item['categoria']}, {item['nombre_marca']}, {item['color']}, {item['talla']}, {item['precio_prenda']}")

        # Convertir la lista de detalles de prendas a una cadena
        prendas_string = ', '.join(prendas_detalle)

        # Insertar la venta en la base de datos y obtener el ID de la venta recién creada
        cur.execute("""
            INSERT INTO public.apartados (anticipo, precio_final, nombre_cliente, creado, fecha_apartado, fecha_limite, editado, activo, usuario, prenda_mostrar) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_apartado
        """, (anticipo, total_precio, nombre_cliente, creado, fecha_apartado, fecha_limite ,editado, activo, usuario ,prendas_string ))
        id_apartado = cur.fetchone()[0]
        conn.commit()

        # Insertar los detalles de la venta en la base de datos
        for item in carrito:
            cantidad = item.get('cantidad', 0)
            cur.execute("""
                INSERT INTO public.detalles_apartado (prenda, id_apartado, cantidad)
                VALUES (%s, %s, %s)
            """, (item['id_prenda'], id_apartado, cantidad))

        conn.commit()

        # Limpiar el carrito después de la venta
        carrito.clear()
        flash(f"Venta creada con éxito. Total: {total_precio:.2f} MX", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al crear el apartado: {str(e)}", "error")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for('sApartado'))
    
@app.route('/apartado/agregar_prendaApa', methods=['POST'])
def agregar_prendaApa():
    id_prenda = request.form.get('id_prenda')
    prendas = lista_prendas()

    if id_prenda:
        try:
            id_prenda = int(id_prenda)
            prenda = next((p for p in prendas if p['id_prenda'] == id_prenda), None)
            if prenda:
                carrito.append(prenda)
                print("Prenda añadida al carrito:", prenda)
                print("Carrito actual:", carrito)

                conn = get_db_connection()
                cur = conn.cursor()

                # Restar la cantidad en la tabla prendas
                cur.execute("UPDATE prendas SET cantidad = cantidad - 1 WHERE id_prenda = %s AND cantidad > 0", (id_prenda,))

                cur.execute("""
                INSERT INTO temp_carrito (nombre_marca, color, talla, precio_prenda, cantidad, categoria)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (prenda['nombre_marca'], prenda['color'], prenda['talla'], prenda['precio_prenda'], 1, prenda['categoria']))

                conn.commit()
                cur.close()
                conn.close()

        except ValueError:
            print("Error: El valor de id_prenda no es un número válido")

    return redirect(url_for('apartado_nuevo'))

@app.route('/aparrtado/quitar_prendaApa', methods=['POST'])
def quitar_prendaApa():
    id_prenda = request.form.get('id_prenda')

    if id_prenda:
        try:
            id_prenda = int(id_prenda)
            prenda = next((p for p in carrito if p['id_prenda'] == id_prenda), None)

            if prenda:
                carrito.remove(prenda)

                conn = get_db_connection()
                cur = conn.cursor()

                # Incrementar la cantidad en la tabla prendas
                cur.execute("UPDATE prendas SET cantidad = cantidad + 1 WHERE id_prenda = %s", (id_prenda,))

                cur.execute("DELETE FROM temp_carrito WHERE id_prenda = %s", (id_prenda,))

                conn.commit()
                cur.close()
                conn.close()

        except ValueError:
            print("Error: El valor de id_prenda no es un número válido")

    return redirect(url_for('apartado_nuevo'))

@app.route('/sApartado/<string:id>')
@login_required
def apartado_detalle(id):
    titulo="Detalles de apartado"
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM apartado WHERE id_apartado={0}'.format(id))
    apartados=cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('apartado_detalle.html', titulo=titulo, apartados=apartados[0])

@app.route('/sApartado/papelera/detalle<string:id>')
@login_required
def apartado_detallePa(id):
    titulo="Detalles de apartado"
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM apartado WHERE id_apartado={0}'.format(id))
    apartados=cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('apartado_detallePa.html',titulo=titulo, apartados=apartados)

@app.route('/sApartado/editar/<string:id>')
@login_required
def apartado_editar(id):
    titulo="Editar apartado"
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * FROM apartados WHERE id_apartado={0}'.format(id))
    apartados=cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('apartado_editar.html',titulo=titulo, apartados=apartados[0], detapas=detapar())

@app.route('/sApartado/editar/<string:id>', methods=['POST'])
@login_required
def apartado_actualizar(id):
    
  if current_user.rol == 1:   
      if request.method == 'POST':
        anticipo = request.form['anticipo']
        precio_final = request.form['precio_final']
        nombre_cliente = request.form['nombre_cliente']
        detapa= request.form ['detapa']
        fecha_apartado = request.form['fecha_apartado']
        fecha_limite = request.form['fecha_limite']
        editado= datetime.now()
        activo = True

        conn=get_db_connection()
        cur=conn.cursor()
        sql="UPDATE apartados SET anticipo=%s,precio_final=%s,nombre_cliente=%s,detapa=%s,fecha_apartado=%s,fecha_limite=%s,editado=%s, activo=%s WHERE id_apartado=%s"
        valores=(anticipo, precio_final, nombre_cliente,detapa, fecha_apartado, fecha_limite,editado, activo,id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()
        flash("apartado editado correctamente")
        return redirect(url_for('sApartado'))

  else:
        flash('¡!no lo puedes borrar')
        return redirect(url_for('sApartado'))

@app.route('/sApartado/eliminar/<string:id>')
@login_required
def apartado_eliminar(id):
 if current_user.rol == 1:
    activo = False
    conn = get_db_connection()
    cur = conn.cursor()
    sql="UPDATE apartados SET activo=%s WHERE id_apartado=%s"
    valores=(activo,id)
    cur.execute(sql,valores)
    conn.commit()
    cur.close()
    conn.close()
    flash('¡Apartado cancelado correctamente!')
    return redirect(url_for('sApartado'))
 else:
        flash('¡!no lo puedes borrar')
        return redirect(url_for('sApartado'))
      
@app.route('/sApartado/restaurar/<string:id>')
@login_required
def apartado_restaurar(id):
 if current_user.rol == 1:
    activo = True
    conn = get_db_connection()
    cur = conn.cursor()
    sql="UPDATE apartados SET activo=%s WHERE id_apartado=%s"
    valores=(activo,id)
    cur.execute(sql,valores)
    conn.commit()
    cur.close()
    conn.close()
    flash('¡Apartado restaurado!')
    return redirect(url_for('apartado_papelera'))
 else:
        flash('¡!no lo puedes borrar')
        return redirect(url_for('sApartado'))
 
#-------------------------------errores------------------------------------
def pagina_no_encontrada(error):
    return render_template('404.html')

def acceso_no_autorizado(error):
    return redirect(url_for('login'))

if __name__ == '__main__':
    csrf.init_app(app)
    app.register_error_handler(404, pagina_no_encontrada)
    app.register_error_handler(401, acceso_no_autorizado)
    app.run(host= '0.0.0.0', port=5000) 
#todos los derechos reservados