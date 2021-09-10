from dateutil import parser
import flask
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from sqlalchemy import and_
from configuration import Configuration
from models import Participant, database, Election, ElectionParticipant, Vote
from adminDecorator import roleCheck
import numpy as np
import os
import time

os.environ['TZ'] = 'Europe/Belgrade'
time.tzset()
application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route("/createParticipant", methods=["POST"])
@roleCheck(role="admin")
def createParticipant():
    name = flask.request.json.get("name", None)
    individual = flask.request.json.get("individual", None)

    msg = ""
    if name is None:
        msg = msg + "Field name is missing."
    elif len(name) == 0:
        msg = msg + "Field name is missing."
    elif individual is None:
        msg = msg + "Field individual is missing."
    if msg != "":
        return jsonify(message=msg), 400

    participant = Participant(name=name, individual=individual)
    database.session.add(participant)
    database.session.commit()

    return jsonify(id=participant.id), 200


@application.route("/getParticipants", methods=["GET"])
@roleCheck(role="admin")
def getParticipants():
    list = []
    participants = Participant.query.all()

    for participant in participants:
        tmp = {"id": participant.id, "name": participant.name, "individual": participant.individual}
        list.append(tmp)

    return jsonify(participants=list), 200


@application.route("/createElection", methods=["POST"])
@roleCheck(role="admin")
def createElection():
    start = flask.request.json.get("start", None)
    end = flask.request.json.get("end", None)
    individual = flask.request.json.get("individual", None)
    participants = flask.request.json.get("participants", None)
    # YYYY-MM-DDThh:mmTZD

    msg = ""
    if start is None or len(start) == 0:
        msg = msg + "Field start is missing."
    elif end is None or len(end) == 0:
        msg = msg + "Field end is missing."
    elif individual is None:
        msg = msg + "Field individual is missing."
    elif participants is None:
        msg = msg + "Field participants is missing."

    if msg != "":
        return jsonify(message=msg), 400
    try:
        startDateTime = parser.parse(start)
        endDateTime = parser.parse(end)
    except ValueError:
        msg = msg + "Invalid date and time."
        return jsonify(message=msg), 400

    # provera datuma pa participantsa
    if endDateTime < startDateTime:
        msg = msg + "Invalid date and time."
    elif len(participants) == 0 or len(participants) == 1:
        msg = msg + "Invalid participants."
    if msg != "":
        return jsonify(message=msg), 400

    elections = Election.query.all()

    for election in elections:
        if ((election.start <= startDateTime <= election.end) or
                (election.start <= endDateTime <= election.end) or
                (startDateTime <= election.start and endDateTime >= election.end)):
            return jsonify(message="Invalid date and time."), 400

    if isinstance(participants[0], int):
        for p in participants:
            participant = Participant.query.filter(Participant.id == p).first()
            if individual != participant.individual:
                return jsonify(message="Invalid participants."), 400
    else:
        return jsonify(message="Invalid participants."), 400

    election = Election(start=startDateTime, end=endDateTime, individual=individual)
    database.session.add(election)
    database.session.commit()
    pollNumber = 1
    pollNumbers = []
    for i in participants:
        ep = ElectionParticipant(electionId=election.id, participantId=i, pollNumber=pollNumber)
        pollNumbers.append(pollNumber)
        pollNumber = pollNumber + 1
        database.session.add(ep)
        database.session.commit()

    return jsonify(pollNumbers=pollNumbers), 200


@application.route("/getElections", methods=["GET"])
@roleCheck(role="admin")
def getElections():
    elections = [{
        "id": item.id,
        "start": str(item.start),
        "end": str(item.end),
        "individual": bool(item.individual),
        "participants": [{
            "id": it.id,
            "name": it.name
        } for it in item.participants]
    } for item in Election.query.all()]

    return jsonify(elections=elections), 200


@application.route("/getResults", methods=["GET"])
@roleCheck(role="admin")
def getresult():
    listParticipan = []
    invalidVotes = []
    id = request.args.get('id', None)
    if id is None:
        return jsonify(message="Field id is missing."), 400
    if id == "":
        return jsonify(message="Field id is missing."), 400
    election = Election.query.filter(Election.id == id).first()
    if election is None:
        return jsonify(message="Election does not exist."), 400

    numOfVotes = len(election.votes)
    arrayOfVotes = np.arange(len(election.participants) + 1)
    mandati = np.arange(len(election.participants) + 1)
    i = 0
    while i < len(arrayOfVotes):
        arrayOfVotes[i] = 0
        mandati[i] = 0
        i += 1

    badVotes = []
    goodVotes = []
    badVotes = Vote.query.filter(and_(Vote.electionId == id, Vote.invalid == True)).all()
    goodVotes = Vote.query.filter(and_(Vote.electionId == id, Vote.invalid == False)).all()
    print("Broj vazecih glasova je:")
    print(len(goodVotes))
    numOfVotes = len(goodVotes)
    for vote in badVotes:
        invalidVotes.append(
            {"electionOfficialJmbg": vote.jmbg, "ballotGuid": vote.guid, "pollNumber": int(vote.voteFor),
             "reason": vote.reasonWhy})

    for vote in goodVotes:
        arrayOfVotes[int(vote.voteFor)] += 1

    if election.individual:
        i = 1
        while i < len(arrayOfVotes):
            electionParticipant = ElectionParticipant.query.filter(
                and_(ElectionParticipant.electionId == id, ElectionParticipant.pollNumber == i)).first()
            participant = Participant.query.filter(Participant.id == electionParticipant.participantId).first()
            if arrayOfVotes[i] != 0 and numOfVotes != 0:
                listParticipan.append({"pollNumber": i, "name": participant.name,
                                       "result": float("{:.2f}".format(arrayOfVotes[i] / numOfVotes))})
            else:
                listParticipan.append(
                    {"pollNumber": i, "name": participant.name, "result": 0})
            i += 1
    else:
        # parlamentarni
        q = 1
        while q < len(arrayOfVotes):
            if arrayOfVotes[q] < numOfVotes * 0.05:
                arrayOfVotes[q] = 0
            q += 1

        numOfMandata = 250

        while numOfMandata != 0:
            index = 2
            maxIndex = 1
            max = arrayOfVotes[1] / (mandati[1] + 1)
            while index < len(arrayOfVotes):
                tmpMax = arrayOfVotes[index] / (mandati[index] + 1)
                if tmpMax > max:
                    maxIndex = index
                    max = tmpMax
                index += 1

            mandati[maxIndex] += 1
            numOfMandata -= 1

        for participant in election.participants:
            electionParticipant = ElectionParticipant.query.filter(ElectionParticipant.electionId == id,
                                                                   ElectionParticipant.participantId == participant.id).first()
            tmp = {"pollNumber": int(electionParticipant.pollNumber), "name": participant.name,
                   "result": int(mandati[electionParticipant.pollNumber])}
            listParticipan.append(tmp)

    return jsonify(participants=listParticipan, invalidVotes=invalidVotes), 200


@application.route("/", methods=["GET"])
def a():
    return "radi admin"


if __name__ == "__main__":
    os.environ['TZ'] = 'Europe/Belgrade';
    time.tzset()
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5003)
