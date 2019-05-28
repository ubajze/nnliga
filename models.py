from google.appengine.ext import ndb


class Season(ndb.Model):
    id = ndb.StringProperty()

    @classmethod
    def get_seasons(cls):
        seasons = Season.query().order(-Season.id).fetch()
        return seasons

    @classmethod
    def get_season(cls, id):
        season = Season.query(Season.id == id).get()
        return season

    @classmethod
    def get_seasons_ids(cls):
        seasons = Season.get_seasons()
        seasons_ids = list()
        for season in seasons:
            seasons_ids.append(season.id)
        return seasons_ids

    @classmethod
    def get_last_season(cls):
        season = Season.get_seasons()
        if season:
            return season[0]

    @classmethod
    def add_season(cls, id):
        season = cls(id=id)
        return season.put()


class Player(ndb.Model):
    pid = ndb.IntegerProperty()
    name = ndb.StringProperty()

    @classmethod
    def get_players(cls):
        players = Player.query().order(Player.name).fetch()
        return players

    @classmethod
    def get_players_list(cls):
        all_players = Player.get_players()
        players = list()
        for player in all_players:
            player_data = dict(player_name=player.name, player_id=player.pid)
            players.append(player_data)
        return players

    @classmethod
    def get_players_dict(cls):
        all_players = Player.get_players()
        players = dict()
        for player in all_players:
            players[player.key] = player
        return players

    @classmethod
    def get_name(cls, player):
        return player.name

    @classmethod
    def get_id(cls, player):
        return player.pid

    @classmethod
    def get_highest_player_id(cls):
        qry = Player.query().order(-Player.pid).get()
        if qry is None:
            return 0
        return qry.pid

    @classmethod
    def get_player_by_name(cls, name):
        player = Player.query(Player.name == name).get()
        return player

    @classmethod
    def get_player_by_id(cls, pid):
        player = Player.query(Player.pid == int(pid)).get()
        return player

    @classmethod
    def add_player(cls, name):
        pid = Player.get_highest_player_id() + 1
        player = Player(pid=pid, name=name)
        return player.put()


class Match(ndb.Model):

    date = ndb.DateProperty()
    scoreA = ndb.IntegerProperty()
    scoreB = ndb.IntegerProperty()
    teamA = ndb.KeyProperty(repeated=True)
    teamB = ndb.KeyProperty(repeated=True)

    @classmethod
    def get_all_matches(cls):
        matches = Match.query().order(Match.date).fetch()
        return matches

    @classmethod
    def get_all_matches_season(cls, season_key):
        matches = Match.query(ancestor=season_key).order(Match.date).fetch()
        return matches

    @classmethod
    def get_match_data_season(cls, season_key):
        matches = Match.query(ancestor=season_key).order(Match.date).fetch()
        match_list = list()
        for match in matches:
            match_data = dict()
            match_data['date'] = str(match.date)
            match_data['scoreA'] = str(match.scoreA)
            match_data['scoreB'] = str(match.scoreB)
            match_data['teamA'] = [x.get().name for x in match.teamA]
            match_data['teamB'] = [x.get().name for x in match.teamB]
            match_list.append(match_data)
        return match_list

    @classmethod
    def add_match(cls, match_data):
        season = match_data.get('season')
        if season is None:
            return
        match = Match(parent=season)
        match.date = match_data.get('date')
        match.scoreA = match_data.get('scoreA')
        match.scoreB = match_data.get('scoreB')
        match.teamA = match_data.get('teamA')
        match.teamB = match_data.get('teamB')
        key = match.put()
        return key

    @classmethod
    def delete_match(cls, match_date):
        match = Match.query(Match.date == match_date).fetch()
        if match:
            match[0].key.delete()


class PlayerStat(ndb.Model):
    # Child of player
    # Multiple entries - one per season
    # season can be None, it means all
    season = ndb.KeyProperty()
    played = ndb.IntegerProperty()
    won = ndb.FloatProperty()
    percentage = ndb.FloatProperty()
    goals_for = ndb.IntegerProperty()
    goals_against = ndb.IntegerProperty()
    goals_diff = ndb.IntegerProperty()
    streak = ndb.StringProperty()
    participation = ndb.FloatProperty()
    position = ndb.IntegerProperty()
    ontable = ndb.BooleanProperty(default=False)

    @classmethod
    def zerorize(cls, stat):
        stat.played = 0
        stat.won = 0.0
        stat.percentage = 0.0
        stat.goals_for = 0
        stat.goals_against = 0
        stat.goals_diff = 0
        stat.streak = ''
        stat.participation = 0.0
        stat.position = None
        stat.ontable = False

    @classmethod
    def get_players_stat(cls, season_key):
        qry = PlayerStat.query(PlayerStat.season == season_key)
        player_stat = dict()
        for player in qry:
            key = player.key.parent().get().key
            player_stat[key] = player
        return player_stat

    @classmethod
    def get_players_stat_nonzero(cls, season_key):
        qry = PlayerStat.query(PlayerStat.season == season_key)
        return qry.filter(PlayerStat.played != 0).fetch()

    @classmethod
    def get_player_stat_all(cls, player_key):
        stat = PlayerStat.query(ancestor=player_key).order(PlayerStat.season)
        player_stat = dict()
        for s in stat:
            player_stat[s.season.get().id] = s
        return player_stat

    @classmethod
    def get_player_stat(cls, player_key, season_key):
        stat = PlayerStat.query(ancestor=player_key)
        return stat.filter(PlayerStat.season == season_key).fetch()

    @classmethod
    def add_empty_stats(cls, player_key, season_key):
        stat = PlayerStat(parent=player_key)
        stat.season = season_key
        PlayerStat.zerorize(stat)
        stat.put()

    @classmethod
    def add_empty_stats_all(cls, season_key):
        players = Player.get_players()
        for player in players:
            PlayerStat.add_empty_stats(player.key, season_key)

    @classmethod
    def add_empty_stats_all_seasons(cls, player_key):
        seasons = Season.get_seasons()
        for season in seasons:
            PlayerStat.add_empty_stats(player_key, season.key)


    @classmethod
    def update_players_stat(cls, season_key):

        def streak(point):
            if point == 1:
                return 'Z'
            if point == 0:
                return 'P'
            return 'N'

        def update(stat, point, sfor, sagainst):
            stat.played += 1
            stat.won += point
            stat.percentage = 100 * (stat.won / stat.played)
            stat.goals_for += sfor
            stat.goals_against += sagainst
            stat.goals_diff = stat.goals_for - stat.goals_against
            stat.streak = '{}{}'.format(streak(point), stat.streak)

        def sorter_percentage(ps):
            return ps.percentage

        def sorter_goals_against(ps):
            return ps.goals_against

        def sorter_goals_for(ps):
            return ps.goals_for

        def sorter_goals_diff(ps):
            return ps.goals_diff

        def sorter_won(ps):
            return ps.won

        matches = Match.get_all_matches_season(season_key)
        player_stats = PlayerStat.get_players_stat(season_key)

        for p in player_stats:
            PlayerStat.zerorize(player_stats[p])

        for match in matches:
            teamA_score = int(match.scoreA)
            teamB_score = int(match.scoreB)
            if teamA_score > teamB_score:
                points = [1, 0]
            elif teamA_score < teamB_score:
                points = [0, 1]
            else:
                points = [0.5, 0.5]

            for player in match.teamA:
                ps = player_stats[player]
                update(ps, points[0], teamA_score, teamB_score)

            for player in match.teamB:
                ps = player_stats[player]
                update(ps, points[1], teamB_score, teamA_score)

        player_stats_list = list()
        for k, v in player_stats.items():
            player_stats_list.append(v)
        player_stats_list = sorted(player_stats_list, key=sorter_goals_against, reverse=False)
        player_stats_list = sorted(player_stats_list, key=sorter_goals_for, reverse=True)
        player_stats_list = sorted(player_stats_list, key=sorter_goals_diff, reverse=True)
        player_stats_list = sorted(player_stats_list, key=sorter_won, reverse=True)
        player_stats_list = sorted(player_stats_list, key=sorter_percentage, reverse=True)

        position = 1
        for stat in player_stats_list:
            stat.participation = stat.played / float(len(matches))
            if stat.participation >= 2.0 / 3.0:
                stat.ontable = True
                stat.position = position
                position += 1
            stat.participation = 100 * stat.participation

        ndb.put_multi(player_stats_list)


class UserAuthorization(ndb.Model):

    email = ndb.StringProperty()
    season_add = ndb.BooleanProperty()
    player_add = ndb.BooleanProperty()
    match_add = ndb.BooleanProperty()
    admin = ndb.BooleanProperty()

    @classmethod
    def is_admin(cls, email):
        qry = UserAuthorization.query(UserAuthorization.email == email)
        result = qry.get()
        if result is not None:
            return qry.admin

    @classmethod
    def get_authorization(cls, email):
        qry = UserAuthorization.query(UserAuthorization.email == email)
        result = qry.get()
        return_data = dict(
            authorization_season_add=False,
            authorization_player_add=False,
            authorization_match_add=False,
            authorization_admin=False
        )
        if result is not None:
            return_data['authorization_season_add'] = result.season_add
            return_data['authorization_player_add'] = result.player_add
            return_data['authorization_match_add'] = result.match_add
            return_data['authorization_admin'] = result.admin
        return return_data
