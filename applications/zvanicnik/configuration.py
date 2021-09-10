import os


class Configuration:
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    REDIS_HOST = os.environ["REDIS_HOST"]
    REDIS_JMBG_LIST = "jmbg_list"
    REDIS_VOTE_FOR_LIST = "vote_for_list"
    REDIS_GUID_LIST = "guid_list"
    REDIS_ELECTION_ID = "election_id_list"
    REDIS_VOTE_LIST = "voteList"