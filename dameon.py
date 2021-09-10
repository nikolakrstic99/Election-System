from redis import Redis
from flask import Flask
from sqlalchemy import and_
from dateutil import parser
from datetime import datetime, timedelta
from configuration import Configuration
from applications.models import database, Election, Vote
import os
import time

os.environ['TZ'] = 'Europe/Belgrade'
time.tzset()
application = Flask(__name__)
application.config.from_object(Configuration)
database.init_app(application)
application.app_context().push()

cnt = 1
idElection = -1
print("poceo demon")
"""
#with application.app_context() as context:
while True:
    elections = Election.query.all()
    if len(elections) >= 2:
        print("broj izbora je")
        print(len(elections))
        break
    print("nema")
"""
with Redis(Configuration.REDIS_HOST) as redis:
    sub = redis.pubsub()
    sub.subscribe(Configuration.REDIS_VOTE_LIST)
    mess = sub.get_message(timeout=1000)["data"]

    while True:
        mess = sub.get_message(timeout=1000)["data"].decode('UTF-8').split(",")
        #print(cnt)
        cnt += 1
        jmbg = mess[0]
        guid = mess[1]
        vote_for = mess[2]

        idElection = -1
        my_date = parser.parse(str(datetime.now() + timedelta(seconds=2)))# Added to overcome time lag

        election = Election.query.filter(and_(Election.start <= my_date, Election.end >= my_date)).first()
        if election is not None:
            idElection = election.id
        if idElection != -1:
            tmpVote = Vote.query.filter(Vote.guid == guid).first()
            if tmpVote is not None:
                vote = Vote(guid=guid, jmbg=jmbg, voteFor=vote_for, electionId=idElection, invalid=True,
                            reasonWhy="Duplicate ballot.")
            elif int(vote_for) > len(election.participants):
                vote = Vote(guid=guid, jmbg=jmbg, voteFor=vote_for, electionId=idElection, invalid=True,
                            reasonWhy="Invalid poll number.")
            else:
                vote = Vote(guid=guid, jmbg=jmbg, voteFor=vote_for, electionId=idElection, invalid=False)
            database.session.add(vote)
            database.session.commit()
        """
        else:
            print(my_date)
            print("nisam nasao")
        """
"""
while True:
    # try:
    with Redis(host="redis") as redis:
        while True:
            bytesStream = redis.blpop("voteList")[1]
            line = bytesStream.decode("utf-8")
            data = line.split(";")
            print(cnt)
            cnt += 1
            guid = data[0]
            vote_for = data[1]
            jmbg = data[2]
            elections = Election.query.all()
            if elections is None:
                print("nema ih")
            else:
                print(len(elections))
            #############
                my_date = parser.parse(str(datetime.now()))
                election = Election.query.filter(and_(Election.start <= my_date, Election.end >= my_date)).first()
                if election is not None:
                    idElection = election.id
                if idElection != -1:
                    tmpVote = Vote.query.filter(Vote.guid == guid).first()
                    if tmpVote is not None:
                        vote = Vote(guid=guid, jmbg=jmbg, voteFor=vote_for, electionId=idElection, invalid=True,
                                    reasonWhy="Duplicate ballot.")
                    elif int(vote_for) > len(election.participants):
                        vote = Vote(guid=guid, jmbg=jmbg, voteFor=vote_for, electionId=idElection, invalid=True,
                                    reasonWhy="Invalid poll number.")
                    else:
                        vote = Vote(guid=guid, jmbg=jmbg, voteFor=vote_for, electionId=idElection, invalid=False)
                    idElection = -1
                    database.session.add(vote)
                    database.session.commit()
                else:
                    print("nisam nasao")
                ###########
# except Exception as error:
# print(error)
"""