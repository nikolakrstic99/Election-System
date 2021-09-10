from email.utils import parseaddr
from re import match

import flask
from flask import Response, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from sqlalchemy import and_
from configuration import Configuration
from adminDecorator import roleCheck
from models import database, User, UserRole

application = flask.Flask(__name__)
application.config.from_object(Configuration)


def provjera_JMBG(jmbg):
    if len(jmbg) != 13:
        return False
    m = 0
    dan = jmbg[0] + jmbg[1]
    if int(dan) > 31 or int(dan) == 0:
        return False
    mjesec = jmbg[2] + jmbg[3]
    if int(mjesec) > 12 or int(mjesec) == 0:
        return False
    m = 11 - ((7 * (int(jmbg[0]) + int(jmbg[6])) + 6 * (int(jmbg[1]) + int(jmbg[7])) + 5 * (
            int(jmbg[2]) + int(jmbg[8])) + 4 * (int(jmbg[3]) + int(jmbg[9])) + 3 * (
                       int(jmbg[4]) + int(jmbg[10])) + 2 * (int(jmbg[5]) + int(jmbg[11]))) % 11)

    if m >= 10:
        return (int(jmbg[12])) == 0
    return (int(jmbg[12])) == m


def is_email_valid(email):
    if len(email) > 256:
        return False
    result = match('[^@]+@.*\.[a-z]{2,}$', email)
    if result is None:
        return False
    return True


@application.route("/register", methods=["POST"])
def register():
    email = flask.request.json.get("email", None)
    password = flask.request.json.get("password", None)
    forename = flask.request.json.get("forename", None)
    surname = flask.request.json.get("surname", None)
    jmbg = flask.request.json.get("jmbg", None)

    if jmbg is None:
        return jsonify(message="Field jmbg is missing."), 400
    elif jmbg == "":
        return jsonify(message="Field jmbg is missing."), 400
    elif forename is None:
        return jsonify(message="Field forename is missing."), 400
    elif forename == "":
        return jsonify(message="Field forename is missing."), 400
    elif surname is None:
        return jsonify(message="Field surname is missing."), 400
    elif surname == "":
        return jsonify(message="Field surname is missing."), 400
    elif email is None:
        return jsonify(message="Field email is missing."), 400
    elif email == "":
        return jsonify(message="Field email is missing."), 400
    elif password is None:
        return jsonify(message="Field password is missing."), 400
    elif password == "":
        return jsonify(message="Field password is missing."), 400

    # JMBG CHECK

    if not provjera_JMBG(jmbg):
        return jsonify(message="Invalid jmbg."), 400
    """
    # END JMBG CHECK
    try:
        valid = validate_email(email)
        email = valid.email
    except EmailNotValidError as e:
        return jsonify(message="Invalid email."), 400
    """
    if not is_email_valid(email):
        return jsonify(message="Invalid email."), 400
    result = parseaddr(email)
    if len(result[1]) == 0:
        return jsonify(message="Invalid email."), 400

    # PASSWORD CHECK
    res = False
    res = any(letter.isdigit() for letter in password)

    res2 = False
    for tmp in password:
        # checking for uppercase character and flagging
        if tmp.isupper():
            res2 = True
            break

    if len(password) < 8 or not res or not res2:
        return jsonify(message="Invalid password."), 400
    # END PASSWORD CHECK

    user = User.query.filter(User.email == email).all()
    if user:
        return jsonify(message="Email already exists."), 400

    user = User(email=email, password=password, forename=forename, surname=surname, jmbg=jmbg)
    database.session.add(user)
    database.session.commit()

    userRole = UserRole(userId=user.id, roleId=2)  # roleId==2 ->izborniZvanicnik
    database.session.add(userRole)
    database.session.commit()

    return Response("Registration successful", status=200)


jwt = JWTManager(application)


@application.route("/login", methods=["POST"])
def login():
    email = flask.request.json.get("email", None)
    password = flask.request.json.get("password", None)

    if email is None:
        return jsonify(message="Field email is missing."), 400
    elif email == "":
        return jsonify(message="Field email is missing."), 400
    elif password is None:
        return jsonify(message="Field password is missing."), 400
    elif password == "":
        return jsonify(message="Field password is missing."), 400

    """try:
        valid = validate_email(email)
        email = valid.email
    except EmailNotValidError as e:
        return jsonify(message="Invalid email."), 400"""
    if not is_email_valid(email):
        return jsonify({'message': 'Invalid email.'}), 400

    result = parseaddr(email)
    if len(result[1]) == 0:
        return jsonify(message="Invalid email."), 400

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if not user:
        return jsonify(message="Invalid credentials."), 400

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": [str(role) for role in user.roles],
        "jmbg": user.jmbg
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)
    return jsonify(accessToken=accessToken, refreshToken=refreshToken), 200
    #return jsonify({'accessToken': accessToken, 'refreshToken': refreshToken}), 200

@application.route("/check", methods=["POST"])
@jwt_required()
def check():
    return "Token is valid!"


@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()
    additionClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"],
        "jmbg": refreshClaims["jmbg"]
    }
    accessToken = create_access_token(identity=identity, additional_claims=additionClaims)
    #return jsonify({'accessToken': accessToken), 200
    return jsonify(accessToken=accessToken), 200


@application.route("/delete", methods=["POST"])
@roleCheck(role="admin")
def delete():
    try:
        email = request.json.get("email", "")
    except:
        return jsonify({'message': 'Field email is missing.'}), 400

    isEmailEmpty = len(email) == 0
    if isEmailEmpty:
        return jsonify({'message': 'Field email is missing.'}), 400
    # emailResultCheck = parseaddr(email);
    if not is_email_valid(email):
        return jsonify({'message': 'Invalid email.'}), 400

    user = User.query.filter(User.email == email).one_or_none()
    if user is None:
        return jsonify({'message': 'Unknown user.'}), 400

    userRole = UserRole.query.filter(UserRole.userId == user.id).first()
    database.session.delete(userRole)
    database.session.commit()
    database.session.delete(user)
    database.session.commit()
    return Response(status=200)

@application.route("/", methods=["GET"])
def a():
    return "radi authentication"


if __name__ == "__main__":
    database.init_app(application)
    #application.run(debug=True, host="0.0.0.0", port=5002)
    application.run(debug=True, host="0.0.0.0", port=5002)
