from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.security import generate_password_hash
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_cors import CORS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASS")
db_name = os.environ.get("DB_NAME")
instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")

if os.environ.get('K_SERVICE'):  
    db_url = f"mysql+pymysql://{db_user}:{db_pass}@localhost/{db_name}?unix_socket=/cloudsql/{instance_connection_name}"
else:
    db_host = os.environ.get("DB_HOST", "34.68.71.111")
    db_port = os.environ.get("DB_PORT", "3306")
    db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

logger.info(f"Environment: {'Cloud Run' if os.environ.get('K_SERVICE') else 'Local'}")
logger.info(f"DB User: {db_user}")
logger.info(f"DB Name: {db_name}")
logger.info(f"Instance Connection Name: {instance_connection_name}")

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu_clave_secreta_aqui')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

db = SQLAlchemy(app)

class Participante(db.Model):
    __tablename__ = 'participante'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=True)
    asignado_a_id = db.Column(db.Integer, db.ForeignKey('participante.id'), nullable=True)
    preferences = db.Column(db.Text, nullable=True)

class Grupo(db.Model):
    __tablename__ = 'grupo'
    id = db.Column(db.Integer, primary_key=True)
    groupName = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    maxParticipants = db.Column(db.Integer, nullable=False)
    exchangeDate = db.Column(db.DateTime, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    participantes = db.relationship('Participante', backref='grupo', lazy=True)

def enviar_email(destinatario, asunto, contenido_html):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = asunto
        msg['From'] = GMAIL_USER
        msg['To'] = destinatario

        html_part = MIMEText(contenido_html, 'html')
        msg.attach(html_part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg)
            logger.info(f"Email enviado exitosamente a {destinatario}")
            return True
    except Exception as e:
        logger.error(f"Error enviando email: {str(e)}")
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def registrar_participante():
    try:
        data = request.json
        logger.info(f"Datos de registro recibidos: {data}")
        
        if Participante.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'El email ya está registrado'}), 400
        
        grupo = None
        if 'groupCode' in data and data['groupCode']:
            grupo = Grupo.query.filter_by(codigo=data['groupCode']).first()
            if not grupo:
                return jsonify({'error': 'Código de grupo inválido'}), 400
            if len(grupo.participantes) >= grupo.maxParticipants:
                return jsonify({'error': 'El grupo está lleno'}), 400

        nuevo_participante = Participante(
            name=data['name'],
            email=data['email'],
            preferences=data.get('preferences', ''),
            grupo_id=grupo.id if grupo else None
        )
        
        db.session.add(nuevo_participante)
        db.session.commit()

        contenido_email = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h1 style="color: #d42426;">¡Bienvenido al Intercambio Navideño! 🎄</h1>
            <p>¡Hola {nuevo_participante.name}!</p>
            <p>Tu registro ha sido exitoso.</p>
            
            {f'''
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                <h3>Detalles de tu grupo:</h3>
                <ul>
                    <li>Nombre del grupo: {grupo.groupName}</li>
                    <li>Código: {grupo.codigo}</li>
                    <li>Presupuesto: ${grupo.budget}</li>
                    <li>Fecha de intercambio: {grupo.exchangeDate.strftime('%d/%m/%Y')}</li>
                </ul>
            </div>
            ''' if grupo else ''}
            
            <p>¡Felices fiestas! 🎅🎁</p>
        </body>
        </html>
        """

        enviar_email(
            nuevo_participante.email,
            "¡Bienvenido al Intercambio Navideño! 🎄",
            contenido_email
        )

        return jsonify({
            'success': True,
            'message': 'Registro exitoso',
            'data': {
                'participant_id': nuevo_participante.id,
                'grupo_id': nuevo_participante.grupo_id,
                'grupo_nombre': grupo.groupName if grupo else None
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error en registro: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups', methods=['POST'])
def crear_grupo():
    try:
        data = request.json
        logger.info(f"Datos de grupo recibidos: {data}")
        
        codigo = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
        
        nuevo_grupo = Grupo(
            groupName=data['groupName'],
            codigo=codigo,
            budget=float(data['budget']),
            maxParticipants=int(data['maxParticipants']),
            exchangeDate=datetime.strptime(data['exchangeDate'], '%Y-%m-%d')
        )
        
        db.session.add(nuevo_grupo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Grupo creado exitosamente',
            'data': {
                'groupId': nuevo_grupo.id,
                'groupCode': codigo,
                'groupName': nuevo_grupo.groupName
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creando grupo: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<codigo>/assign', methods=['POST'])
def realizar_sorteo(codigo):
    try:
        grupo = Grupo.query.filter_by(codigo=codigo).first()
        if not grupo:
            return jsonify({'error': 'Grupo no encontrado'}), 404

        participantes = grupo.participantes
        if len(participantes) < 2:
            return jsonify({'error': 'Se necesitan al menos 2 participantes'}), 400

        participantes_list = list(participantes)
        asignados = participantes_list.copy()
        
        while any(p1 == p2 for p1, p2 in zip(participantes_list, asignados)):
            random.shuffle(asignados)

        for giver, receiver in zip(participantes_list, asignados):
            giver.asignado_a_id = receiver.id
            
            contenido_email = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h1 style="color: #d42426;">🎄 ¡Tu amigo secreto ha sido asignado! 🎁</h1>
                <p>¡Hola {giver.name}!</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                    <h3 style="color: #2C5530;">Te ha tocado regalar a:</h3>
                    <p style="font-size: 24px; text-align: center; color: #d42426;">
                        {receiver.name}
                    </p>
                    
                    <h4>Detalles del intercambio:</h4>
                    <ul>
                        <li>Presupuesto: ${grupo.budget}</li>
                        <li>Fecha: {grupo.exchangeDate.strftime('%d/%m/%Y')}</li>
                    </ul>
                    
                    <div style="margin-top: 20px;">
                        <h4>Preferencias de regalo:</h4>
                        <p>{receiver.preferences or 'No especificadas'}</p>
                    </div>
                </div>
                
                <p style="text-align: center;">¡Felices fiestas! 🎅🎄</p>
            </body>
            </html>
            """
            
            enviar_email(
                giver.email,
                "🎄 ¡Tu amigo secreto ha sido asignado! 🎁",
                contenido_email
            )

        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Asignaciones realizadas exitosamente'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error en sorteo: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<codigo>/participants', methods=['GET'])
def obtener_participantes(codigo):
    try:
        grupo = Grupo.query.filter_by(codigo=codigo).first()
        if not grupo:
            return jsonify({'error': 'Grupo no encontrado'}), 404

        participantes = [{
            'id': p.id,
            'name': p.name,
            'email': p.email,
            'registrationDate': p.fecha_registro.strftime('%Y-%m-%d %H:%M:%S'),
            'preferences': p.preferences
        } for p in grupo.participantes]

        return jsonify({
            'group': {
                'id': grupo.id,
                'groupName': grupo.groupName,
                'code': grupo.codigo,
                'budget': grupo.budget,
                'exchangeDate': grupo.exchangeDate.strftime('%Y-%m-%d'),
                'maxParticipants': grupo.maxParticipants,
                'currentParticipants': len(participantes),
                'participants': participantes
            }
        }), 200

    except Exception as e:
        logger.error(f"Error obteniendo participantes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/placeholder/<width>/<height>')
def placeholder_image(width, height):
    if not os.path.exists('static'):
        os.makedirs('static')
    return send_from_directory('static', 'placeholder.png')

@app.route('/test-email', methods=['POST'])
def test_email():
    try:
        data = request.json
        resultado = enviar_email(
            data['email'],
            "Prueba de Email - Intercambio Navideño",
            """
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h1 style="color: #d42426;">🎄 Prueba de Email 🎁</h1>
                <p>Este es un email de prueba del sistema de intercambio navideño.</p>
                <p>Si estás recibiendo este mensaje, la configuración de email está funcionando correctamente.</p>
                <p>¡Felices fiestas! 🎅</p>
            </body>
            </html>
            """
        )
        
        if resultado:
            return jsonify({'success': True, 'message': 'Email enviado correctamente'}), 200
        else:
            return jsonify({'error': 'No se pudo enviar el email'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups', methods=['GET'])
def get_all_groups():
    try:
        groups = Grupo.query.all()
        return jsonify([{
            'id': g.id,
            'groupName': g.groupName,
            'code': g.codigo,
            'budget': g.budget,
            'maxParticipants': g.maxParticipants,
            'exchangeDate': g.exchangeDate.strftime('%Y-%m-%d'),
            'creationDate': g.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            'participants': [{
                'id': p.id,
                'name': p.name,
                'email': p.email,
                'registrationDate': p.fecha_registro.strftime('%Y-%m-%d %H:%M:%S'),
                'preferences': p.preferences
            } for p in g.participantes]
        } for g in groups])
    except Exception as e:
        logger.error(f"Error obteniendo grupos: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<grupo_id>', methods=['GET'])
def get_group(grupo_id):
    try:
        group = Grupo.query.get(grupo_id)
        if not group:
            return jsonify({'error': 'Grupo no encontrado'}), 404

        return jsonify({
            'id': group.id,
            'groupName': group.groupName,
            'code': group.codigo,
            'budget': group.budget,
            'maxParticipants': group.maxParticipants,
            'exchangeDate': group.exchangeDate.strftime('%Y-%m-%d'),
            'creationDate': group.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            'participants': [{
                'id': p.id,
                'name': p.name,
                'email': p.email,
                'registrationDate': p.fecha_registro.strftime('%Y-%m-%d %H:%M:%S'),
                'preferences': p.preferences
            } for p in group.participantes]
        })
    except Exception as e:
        logger.error(f"Error obteniendo grupo: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/participants', methods=['GET'])
def get_all_participants():
    try:
        participants = Participante.query.all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'email': p.email,
            'registrationDate': p.fecha_registro.strftime('%Y-%m-%d %H:%M:%S'),
            'preferences': p.preferences,
            'group': p.grupo.groupName if p.grupo else None
        } for p in participants])
    except Exception as e:
        logger.error(f"Error obteniendo participantes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_data():
    try:
        Participante.query.delete()
        Grupo.query.delete()
        db.session.commit()
        return jsonify({'message': 'Datos eliminados correctamente'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error eliminando datos: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/healthcheck', methods=['GET'])
def healthcheck():
    try:
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }), 200
    except Exception as e:
        logger.error(f"Error en healthcheck: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }), 500

with app.app_context():
    try:
        db.create_all()
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error inicializando la base de datos: {str(e)}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)