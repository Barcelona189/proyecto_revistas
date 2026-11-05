from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura'

# Configuración de Supabase
SUPABASE_URL = "https://bcofavjvxdieenjzdbej.supabase.co"
SUPABASE_KEY = "sb_publishable__cG18v5TPe1KGEo0NXyvBA_rnoD0M2n"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ruta principal (Dashboard, cliente, buscador y tabla de envíos)
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    # Si se envía un nuevo envío y los datos de suscripción por POST
    if request.method == 'POST':
        try:
            # 1. Guardar o actualizar datos de la suscripción y cliente
            no_suscripcion = request.form.get('suscripcion')
            nombre = request.form.get('nombre')
            nit = request.form.get('nit')
            dir_cobro = request.form.get('dir_cobro')
            tel_cobro = request.form.get('tel_cobro')
            dir_entrega = request.form.get('dir_entrega')
            tel_entrega = request.form.get('tel_entrega')
            fecha_inicio = request.form.get('inicio')
            fecha_fin = request.form.get('fin')
            nombre_revista = request.form.get('revista')

            supabase.table('clientes').upsert({
                "id": 1,
                "nombre": nombre,
                "nit": nit,
                "tel_cobro": tel_cobro,
                "dir_cobro": dir_cobro
            }).execute()
 
            supabase.table('suscripciones').upsert({
                "no_suscripcion": no_suscripcion,
                "tel_entrega": tel_entrega,
                "dir_entrega": dir_entrega,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin
            }).execute()

            supabase.table('revistas').upsert({
                "id": 1,
                "nombre_revista": nombre_revista
            }).execute()

            # 2. Guardar el nuevo envío en la tabla 'envios'
            nuevo_envio = {
                "no_envio": int(request.form['no_envio']),
                "revista_no": int(request.form['revista_no']),
                "fecha_prog": request.form['fecha_prog'],
                "empleado": request.form['empleado'],
                "fecha_ent": request.form['fecha_ent'] if request.form['fecha_ent'] else None,
                "obs": request.form['obs']
            }
            supabase.table('envios').insert(nuevo_envio).execute()
        except Exception as e:
            print(f"Error al insertar: {e}")
        return redirect(url_for('index'))

    # Obtener datos de la empresa/cliente para mostrarlos en el formulario si es necesario
    cliente_res = supabase.table('clientes').select('*').limit(1).execute()
    c_data = cliente_res.data[0] if cliente_res.data else {}

    susc_res = supabase.table('suscripciones').select('*').limit(1).execute()
    s_data = susc_res.data[0] if susc_res.data else {}

    revista_res = supabase.table('revistas').select('*').limit(1).execute()
    r_data = revista_res.data[0] if revista_res.data else {}

    cliente = {
        "suscripcion": s_data.get("no_suscripcion", ""),
        "nombre": c_data.get("nombre", ""),
        "nit": c_data.get("nit", ""),
        "tel_cobro": c_data.get("tel_cobro", ""),
        "dir_cobro": c_data.get("dir_cobro", ""),
        "tel_entrega": s_data.get("tel_entrega", ""),
        "dir_entrega": s_data.get("dir_entrega", ""),
        "revista": r_data.get("nombre_revista", ""),
        "inicio": s_data.get("fecha_inicio", ""),
        "fin": s_data.get("fecha_fin", "")
    }

    # Búsqueda de envíos por empleado
    busqueda = request.args.get('q', '')
    try:
        if busqueda:
            response = supabase.table('envios').select('*').ilike('empleado', f'%{busqueda}%').execute()
        else:
            response = supabase.table('envios').select('*').execute()
        envios = response.data
    except Exception as e:
        envios = []

    return render_template('index.html', cliente=cliente, envios=envios, busqueda=busqueda)

# Ruta para ver el comprobante y guardarlo en PDF
@app.route('/pdf/<int:id>')
def ver_pdf(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    try:
        envio_res = supabase.table('envios').select('*').eq('no_envio', id).execute()
        envio = envio_res.data[0] if envio_res.data else None

        cliente_res = supabase.table('clientes').select('*').limit(1).execute()
        c_data = cliente_res.data[0] if cliente_res.data else {}

        susc_res = supabase.table('suscripciones').select('*').limit(1).execute()
        s_data = susc_res.data[0] if susc_res.data else {}

        revista_res = supabase.table('revistas').select('*').limit(1).execute()
        r_data = revista_res.data[0] if revista_res.data else {}

        cliente = {
            "suscripcion": s_data.get("no_suscripcion", "S/N"),
            "nombre": c_data.get("nombre", "Cliente no registrado"),
            "nit": c_data.get("nit", "C/F"),
            "tel_cobro": c_data.get("tel_cobro", ""),
            "dir_cobro": c_data.get("dir_cobro", ""),
            "tel_entrega": s_data.get("tel_entrega", ""),
            "dir_entrega": s_data.get("dir_entrega", ""),
            "revista": r_data.get("nombre_revista", "Revista General"),
            "inicio": s_data.get("fecha_inicio", ""),
            "fin": s_data.get("fecha_fin", "")
        }
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        envio = None
        cliente = {}

    return render_template('pdf_comprobante.html', envio=envio, cliente=cliente)

# Ruta de Inicio de Sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        
        res = supabase.table('usuarios').select('*').eq('correo', correo).eq('contrasena', contrasena).execute()
        
        if res.data:
            session['usuario'] = correo
            session['es_admin'] = True  # Otorga permisos de administrador
            return redirect(url_for('index'))
        else:
            error = "Correo o contraseña incorrectos."
            
    return render_template('login.html', error=error)

# Ruta para Cerrar Sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Ruta para Editar un Envío y los datos generales

# Ruta para Editar un Envío y los datos generales
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if 'usuario' not in session or not session.get('es_admin'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            no_suscripcion = request.form.get('suscripcion')

            # 1. Actualizar los datos del cliente
            supabase.table('clientes').update({
                "nombre": request.form.get('nombre'),
                "nit": request.form.get('nit'),
                "tel_cobro": request.form.get('tel_cobro'),
                "dir_cobro": request.form.get('dir_cobro')
            }).eq('id', 1).execute()

            # 2. Actualizar la suscripción
            supabase.table('suscripciones').update({
                "tel_entrega": request.form.get('tel_entrega'),
                "dir_entrega": request.form.get('dir_entrega'),
                "fecha_inicio": request.form.get('inicio'),
                "fecha_fin": request.form.get('fin')
            }).eq('no_suscripcion', no_suscripcion).execute()

            # 3. Actualizar la revista
            supabase.table('revistas').update({
                "nombre_revista": request.form.get('revista')
            }).eq('id', 1).execute()

            # 4. Actualizar el envío
            datos_actualizados = {
                "revista_no": int(request.form['revista_no']),
                "fecha_prog": request.form['fecha_prog'],
                "empleado": request.form['empleado'],
                "fecha_ent": request.form['fecha_ent'] or None,
                "obs": request.form['obs']
            }

            resultado = supabase.table('envios').update(
                datos_actualizados
            ).eq('no_envio', id).execute()

            if not resultado.data:
                print("No se encontró el envío para actualizar.")
            else:
                print("Envío actualizado correctamente.")

        except Exception as e:
            print(f"Error al actualizar: {e}")

        return redirect(url_for('index'))

    # Obtener el envío
    res = supabase.table('envios').select('*').eq(
        'no_envio', id
    ).execute()

    envio = res.data[0] if res.data else None

    if not envio:
        return redirect(url_for('index'))

    # Obtener datos generales
    cliente_res = supabase.table('clientes').select('*').limit(1).execute()
    c_data = cliente_res.data[0] if cliente_res.data else {}

    susc_res = supabase.table('suscripciones').select('*').limit(1).execute()
    s_data = susc_res.data[0] if susc_res.data else {}

    revista_res = supabase.table('revistas').select('*').limit(1).execute()
    r_data = revista_res.data[0] if revista_res.data else {}

    cliente = {
        "suscripcion": s_data.get("no_suscripcion", ""),
        "nombre": c_data.get("nombre", ""),
        "nit": c_data.get("nit", ""),
        "tel_cobro": c_data.get("tel_cobro", ""),
        "dir_cobro": c_data.get("dir_cobro", ""),
        "tel_entrega": s_data.get("tel_entrega", ""),
        "dir_entrega": s_data.get("dir_entrega", ""),
        "revista": r_data.get("nombre_revista", ""),
        "inicio": s_data.get("fecha_inicio", ""),
        "fin": s_data.get("fecha_fin", "")
    }

    return render_template(
        'editar.html',
        envio=envio,
        cliente=cliente
    )


# Ruta para Eliminar un Envío
@app.route('/eliminar/<int:id>')
def eliminar(id):
    if 'usuario' not in session or not session.get('es_admin'):
        return redirect(url_for('index'))
        
    supabase.table('envios').delete().eq('no_envio', id).execute()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)