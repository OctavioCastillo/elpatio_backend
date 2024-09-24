from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity , decode_token
from jwt import ExpiredSignatureError, InvalidTokenError, DecodeError
from models import mongo, init_db
from config import Config
from bson.json_util import ObjectId 
from flask_bcrypt import Bcrypt
from datetime import timedelta
from mail import Mail
from flask import current_app

app = Flask(__name__)
app.config.from_object(Config)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

init_db(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if mongo.db.users.find_one({'email':email}):
        return jsonify({"msg":"Este correo ya está registrado"}), 401
    
    hashed_pwd = bcrypt.generate_password_hash(password).decode('utf-8')
    
    temp_user = {
        "username": username.title(),
        "email": email,
        "password": hashed_pwd,
        "puntos": "0",
        "is_verified": False,
        "type": "user"
    }
    result = mongo.db.temp_users.insert_one(temp_user)

    if result.acknowledged:
        token = create_access_token(identity=email, expires_delta=timedelta(hours=24))
        
        verification_link = f"http://localhost:5000/verify_email/{token}"
        mail = Mail()
        mail.send_verification_email(email, verification_link)
        mail.close()
        print(token)
        print(decode_token(token))

        return jsonify({"msg": "Por favor verifica tu correo para completar el registro"}), 200
    else:
        return jsonify({"msg": "Error al crear usuario temporal"}), 401

@app.route('/verify_email/<token>', methods=['GET'])
def verify_email(token):
    
    try:

        data = decode_token(token)
        email = data['sub']

        temp_user = mongo.db.temp_users.find_one({"email": email})

        if mongo.db.users.find_one({'email':email}):
            return jsonify({"msg":"Este correo ya está registrado"}), 401
        
        if not temp_user:
            return jsonify({"msg": "No se encontró usuario temporal"}), 404
        
        
        mongo.db.users.insert_one({
            "username": temp_user['username'],
            "email": temp_user['email'],
            "password": temp_user['password'],
            "puntos": temp_user['puntos'],
            "user_type": "user"
        })

        mongo.db.temp_users.delete_many({"email": email})

        return jsonify({"msg": "Usuario verificado y registrado"}), 200
    
    except ExpiredSignatureError:
        return jsonify({"msg": "El token ha expirado"}), 400
    except InvalidTokenError:
        return jsonify({"msg": "Token inválido"}), 400
    except DecodeError:
        return jsonify({"msg": "Error al decodificar el token"}), 400
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

    
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = mongo.db.users.find_one({"email": email})
    
    if user and bcrypt.check_password_hash(user['password'], password):
        access_token = create_access_token(identity=str(user["_id"]), expires_delta=timedelta(weeks=60))
        return jsonify(access_token=access_token), 200
    
    else:
        return jsonify({"msg": "Credenciales incorrectas"}), 401

@app.route('/perfil', methods=['GET'])
@jwt_required()
def perfil():
    current_user = get_jwt_identity()
    current_user = ObjectId(current_user)
    
    usuario = mongo.db.users.find_one({"_id":current_user})

    if usuario:
        usuario["_id"] = str(usuario["_id"])
        return jsonify({"msg":"Usuario encontrado", "Usuario":usuario}), 200
    else:
        return jsonify({"msg":"Usuario no encontrado"}), 404

@app.route('/agregar_puntos', methods=['PUT'])
@jwt_required()
def agregar_puntos():
    data = request.get_json()
    puntos_añadidos = int(data.get('puntos'))

    current_user = get_jwt_identity()
    current_user = ObjectId(current_user)

    usuario = mongo.db.users.find_one({"_id":current_user})

    if not usuario:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    puntos_actuales = int(usuario['puntos'])
    puntos_nuevos = puntos_actuales + puntos_añadidos

    print(current_user)

    mongo.db.users.update_one({"_id": current_user}, {"$set": {"puntos": str(puntos_nuevos)}})

    return jsonify({"msg": "Puntos actualizados", "nuevos_puntos": puntos_nuevos}), 200

@app.route('/obtener_cupones', methods=['GET'])
@jwt_required()
def obtener_cupones():
    lista_cupones = mongo.db.cupones.find()
    cupones = []

    for cupon in lista_cupones:
        cupon['_id'] = str(cupon['_id'])
        cupones.append(cupon)

    if len(cupones) == 0:
        return jsonify({"msg":"No hay cupones registrados"}), 400
    
    return jsonify(cupones), 200

@app.route('/canjear_cupon', methods=['PUT'])
@jwt_required()
def canjear_cupon():
    data = request.get_json()
    cupon_nombre = data.get('cupon_nombre')

    current_user = get_jwt_identity()
    current_user = ObjectId(current_user)

    # Busca el usuario en la base de datos
    usuario = mongo.db.users.find_one({"_id": current_user})

    if not usuario:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    puntos_actuales = int(usuario['puntos'])

    cupon = mongo.db.cupones.find_one({"nombre": cupon_nombre})

    if not cupon:
        return jsonify({"msg": "Cupón no encontrado"}), 404

    puntos_necesarios = int(cupon['puntos'])
    
    if puntos_actuales < puntos_necesarios:
        return jsonify({"msg": "No tienes suficientes puntos para canjear este cupón"}), 400

    nuevos_puntos = puntos_actuales - puntos_necesarios
    mongo.db.users.update_one({"_id": current_user}, {"$set": {"puntos": nuevos_puntos}})

    # Agrega el canje a la colección 'cupones_canjeados'
    mongo.db.cupones_canjeados.insert_one({
        "user_id": current_user,
        "username": usuario['username'],
        "email": usuario['email'],
        "cupón_nombre": cupon_nombre
    })

    return jsonify({"msg": "Cupón canjeado exitosamente", "nuevos_puntos": nuevos_puntos}), 200

if __name__ == '__main__':
    app.run(debug=True)
