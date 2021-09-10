import io
import os
from datetime import time

from flask import Flask, Response, jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt, JWTManager
from configuration import Configuration
from applications.models import database
from applications.admin.adminDecorator import roleCheck
import csv
from redis import Redis

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route("/vote", methods=["POST"])
@roleCheck(role="user")
def vote():
    try:
        f = request.files.get("file", None)
    except:
        return jsonify(message="Field file is missing."), 400

    if f is None:
        return jsonify(message="Field file is missing."), 400

    content = request.files["file"].stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)

    cnt = 0
    guidList = []
    voteForList = []
    for row in reader:
        try:
            if len(row) != 2:
                msg = "Incorrect number of values on line "
                msg = msg + str(cnt)
                msg = msg + "."
                return jsonify(message=msg), 400
            elif row[1] == "" or row[0] == "":
                raise Exception()
            else:
                    num = int(row[1])
                    if num < 0:
                        raise Exception()
        except:
            return jsonify(message="Incorrect poll number on line " + str(cnt) + "."), 400

        guidList.append(row[0])
        voteForList.append(row[1])
        cnt = cnt + 1

    verify_jwt_in_request()
    claims = get_jwt()

    if "sub" in claims:
        jmbg = claims["jmbg"]
    c = 0
    print("pre stavljanja")
    with Redis(Configuration.REDIS_HOST, port=6379, decode_responses=True) as redis:
        while c != cnt:
            redis.publish(Configuration.REDIS_VOTE_LIST, jmbg + "," + guidList[c] + "," + voteForList[c])
            c += 1

    return Response(status=200)


"""
@application.route("/vote", methods=["POST"])
@roleCheck(role="user")
def vote():
    try:
        f = request.files.get("file", None)
    except:
        return jsonify(message="Field file is missing."), 400

    if f is None:
        return jsonify(message="Field file is missing."), 400

    content = request.files["file"].stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)

    cnt = 0
    for row in reader:
        try:
            if len(row) != 2:
                msg = "Incorrect number of values on line "
                msg = msg + str(cnt)
                msg = msg + "."
                return jsonify(message=msg), 400
            elif row[1] == "" or row[0] == "":
                raise Exception()
            else:
                num = int(row[1])
                if num < 0:
                    raise Exception()
        except:
            return jsonify(message="Incorrect poll number on line " + str(cnt) + "."), 400

        cnt = cnt + 1

    verify_jwt_in_request()
    claims = get_jwt()
    stream.seek(0)
    reader = csv.reader(stream)

    if "sub" in claims:
        jmbg = claims["jmbg"]

    with Redis(host="redis") as redis:
        for row in reader:
            redis.rpush("voteList", row[0] + ";" + row[1] + ";" + jmbg)

    return Response(status=200)
"""

@application.route("/", methods=["GET"])
def a():
    return "radi zvanicnik"


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5004)
