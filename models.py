from google.appengine.ext import ndb
import datetime

class Season(ndb.Model):
    id = ndb.StringProperty()

    @classmethod
    def get_season_list(cls):
        qry = Season.query().order(-Season.id)
        season_list = []
        for season in qry:
            season_list.append(season.id)
        return season_list

    @classmethod
    def get_season_key(cls,id):
        qry = Season.query(Season.id == id).fetch(1, keys_only = True)
        for season in qry:
            return season

class Player(ndb.Model):
#child od Season
    player_id = ndb.IntegerProperty()
    player_firstname = ndb.StringProperty()
    player_lastname = ndb.StringProperty()

# spodnja procedura velja kadar klices funkcijo znotraj classa brez da prej ustvaris instanco -> klices Playe
    @classmethod
    def get_highest_player_id(cls):
        qry = Player.query().order(-Player.player_id).fetch(1)
        if qry == []:
            return 0
        for player in qry:
            highest_player_id = player.player_id
        return highest_player_id

    @classmethod
    def get_list_of_player_ids(cls):
        qry = Player.query().order(Player.player_id)
        id_list = []
        for player in qry:
            id_list.append(player.player_id)
        return id_list

    @classmethod
    def get_player_by_id(cls,player_id):
        qry = Player.query(Player.player_id == player_id).fetch(1)
        if qry == []:
            return {}
        for player in qry:
            return {
                'player_id': player.player_id,
                'player_firstname': player.player_firstname,
                'player_lastname': player.player_lastname,
                'player_season': player.key.parent().get().id
            }

    @classmethod
    def get_player_key_by_id(cls,player_id):
        qry = Player.query(Player.player_id == player_id).fetch(1, keys_only = True)
        for player in qry:
            return player

    @classmethod
    def get_all_players_from_season(cls,season_key):
        qry = Player.query(ancestor=season_key).fetch()
        return qry

    @classmethod
    def add_player(cls,player_data):
        player = Player(parent=player_data['season_key'])
        player.player_id = player_data['player_id']
        player.player_firstname = player_data['player_firstname']
        player.player_lastname = player_data['player_lastname']
        player_key = player.put()
        return player_key

class Match(ndb.Model):
#child of season
#DODAJ SE KDO JE VOLIL
    match_round= ndb.IntegerProperty()
    match_date = ndb.DateProperty()
    teamA_score = ndb.IntegerProperty()
    teamB_score = ndb.IntegerProperty()
    teamA = ndb.IntegerProperty(repeated=True)
    teamB = ndb.IntegerProperty(repeated=True)

    @classmethod
    def get_highest_match_round(cls,season_key):
        qry = Match.query(ancestor=season_key).order(-Match.match_round).get()
        if qry == None:
            return 0
        else:
            return int(qry.match_round)

    @classmethod
    def get_match_data(cls,match_parameters):
        qry = Match.query(Match.match_round == int(match_parameters['match_round']),ancestor=match_parameters['season_key']).get()
        return qry

    @classmethod
    def get_all_matches(cls,season_key):
        if not season_key:
            qry = Match.query(ancestor=season_key).order(-Match.match_round).fetch()
        else:
            qry = Match.query(ancestor=season_key).order(-Match.match_round).fetch()
        return qry
		
    @classmethod
    def add_match(cls,match_data):
        match = Match(parent=match_data['season_key'])
        match.match_round = match_data['match_round']
        match.match_date = match_data['match_date']
        match.teamA_score = match_data['teamA_score']
        match.teamB_score = match_data['teamB_score']
        match.teamA = match_data['teamA']
        match.teamB = match_data['teamB']
        match_key = match.put()
        return match_key

class PlayerStat(ndb.Model):
#child of player
    number_of_games_played = ndb.IntegerProperty()
    wins = ndb.FloatProperty()
    wins_percentage = ndb.FloatProperty()
    goals_for = ndb.IntegerProperty()
    goals_against = ndb.IntegerProperty()
    goals_diff = ndb.IntegerProperty()
    participation = ndb.FloatProperty()
    on_table = ndb.BooleanProperty()


    @classmethod
    def get_last_player_stat(cls,player_key):
        qry = PlayerStat.query(ancestor=player_key).order(-PlayerStat.match_round).get()
        if qry == None:
            return {
                'wins': 0,
                'goals_for': 0,
                'goals_against': 0,
                'number_of_games': 0,
            }
        else:
            return {
                'wins': qry.wins,
                'goals_for': qry.goals_for,
                'goals_against': qry.goals_against,
                'number_of_games': qry.number_of_games,
            }

    @classmethod
    def init_player_stat(cls,player_key):
        new_player_stat = PlayerStat(parent=player_key)
        new_player_stat.number_of_games_played = 0
        new_player_stat.wins = 0
        new_player_stat.wins_percentage = 0
        new_player_stat.goals_for = 0
        new_player_stat.goals_against = 0
        new_player_stat.goals_diff = 0
        new_player_stat.participation = 0
        new_player_stat.on_table = False
        new_player_stat.put()


    @classmethod
    def update_player_stat(cls,player_key,match_data,season_games):
        player_stat = PlayerStat.query(ancestor=player_key).get()
        player_stat.number_of_games_played = player_stat.number_of_games_played + match_data['played']
        player_stat.wins = player_stat.wins + match_data['win']
        player_stat.goals_for = player_stat.goals_for + match_data['goals_for']
        player_stat.goals_against = player_stat.goals_against + match_data['goals_against']
        player_stat.goals_diff = player_stat.goals_for - player_stat.goals_against 
        if player_stat.number_of_games_played == 0:
            player_stat.wins_percentage = 0
        else:
            player_stat.wins_percentage = 100 * player_stat.wins / float(player_stat.number_of_games_played)
        player_stat.participation = 100 * player_stat.number_of_games_played / float(season_games)
        player_stat.on_table = True if player_stat.participation >= (200/3.0) else False
        player_stat.put()

    @classmethod
    def get_player_stat(cls,season_key):
        qry = PlayerStat.query(ancestor=season_key).order(-PlayerStat.wins_percentage).order(-PlayerStat.goals_diff).order(-PlayerStat.wins).fetch()
        return qry

class UserAuthorization(ndb.Model):
#root 
    user_email = ndb.StringProperty()
    authorization_payment_view = ndb.BooleanProperty()
    authorization_payment_add = ndb.BooleanProperty()
    authorization_season_add = ndb.BooleanProperty()
    authorization_player_add = ndb.BooleanProperty()
    authorization_match_add = ndb.BooleanProperty()
    authorization_admin = ndb.BooleanProperty()

    @classmethod
    def is_admin(cls,user_email):
        qry = UserAuthorization.query(UserAuthorization.user_email == user_email).get()
        if qry != None:
            return qry.authorization_admin
    
    @classmethod
    def get_authorization(cls,user_email):
        qry = UserAuthorization.query(UserAuthorization.user_email == user_email).get()
        if qry != None:
            return {
                'authorization_payment_view': qry.authorization_payment_view,
                'authorization_payment_add': qry.authorization_payment_add,
                'authorization_season_add': qry.authorization_season_add,
                'authorization_player_add': qry.authorization_player_add,
                'authorization_match_add': qry.authorization_match_add,
                'authorization_admin': qry.authorization_admin,
            }
        else:
            return {
                'authorization_payment_view': False,
                'authorization_payment_add': False,
                'authorization_season_add': False,
                'authorization_player_add': False,
                'authorization_match_add': False,
                'authorization_admin': False,
            }


class PlayerPayments(ndb.Model):

    date = ndb.DateProperty()
    payment = ndb.FloatProperty()
    debt = ndb.FloatProperty()

    @classmethod
    def add_payment(cls,payment_data):
        payment = PlayerPayments(parent=payment_data['player_key'])
        payment.date = payment_data['date']
        payment.payment = payment_data['payment']
        payment.debt = payment_data['debt']
        payment_key = payment.put()
        return payment_key

    @classmethod
    def get_all_payments_for_player(cls,player_key):
        qry = PlayerPayments.query(ancestor=player_key).fetch()
        return qry

    @classmethod
    def calculate_payment_data(cls,player_key):
        qry = PlayerPayments.query(ancestor=player_key).fetch()
        player_payments = 0
        player_debt = 0
        if qry:
            for payment in qry:
                player_payments = player_payments + payment.payment
                player_debt = player_debt + payment.debt
        return {'player_payments': player_payments, 'player_debt': player_debt}
