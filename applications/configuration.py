from datetime import timedelta
import os
databaseUrl = os.environ["DATABASE_URL"]


class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseUrl}/elections"
    #SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@localhost/elections"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRED = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRED = timedelta(days=30)
    REDIS_HOST = "localhost"
    REDIS_JMBG_LIST = "jmbg_list"
    REDIS_VOTE_FOR_LIST = "vote_for_list"
    REDIS_GUID_LIST = "guid_list"
    REDIS_ELECTION_ID = "election_id_list"

    REDIS_VOTE_LIST = "voteList"