#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import os
import datetime

from google.appengine.api import users

from models import *

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

DEBUG = False

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


FIRST_ADMIN = 'admin@localhost'


def add_admin(admin_email):
    ua = UserAuthorization(
        email=admin_email,
        season_add=True,
        player_add=True,
        match_add=True,
        admin=True)

    ua.put()


def update_player_state(season=None):
    if season:
        pass


class Helper(webapp2.RequestHandler):

    def get_template(self, template):
        return JINJA_ENVIRONMENT.get_template(template)


    def render_webpage(self, values, template):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render(values))


    def get_authentication(self):

        # # Upload purposes
        # values = dict(authenticated=True)
        # values['email'] = FIRST_ADMIN
        # values.update(UserAuthorization.get_authorization(values['email']))

        user = users.get_current_user()
        if user:
            values = dict(authenticated=True)
            values['email'] = user.email()
            values.update(UserAuthorization.get_authorization(values['email']))
        else:
            values = dict(authenticated=False, email='')
        return values

    def get_authorization(self, auth, authorization):
        authorized = True
        if auth.get('authenticated') is False:
            auth['error_msg_login'] = True
            self.render_webpage(auth, self.template)
            authorized = False
        elif not auth[authorization]:
            auth['error_msg_authorization'] = True
            self.render_webpage(auth, self.template)
            authorized = False
        return authorized


    def init(self, entity):
        params = dict()

        if hasattr(self, 'TEMPLATE'):
            self.template = self.get_template(self.TEMPLATE)
        auth = self.get_authentication()

        authrz = 'authorization_{}_add'.format(entity.lower())

        if not self.get_authorization(auth, authrz):
            return

        params.update(auth)
        return params

class Login(Helper):
    def get(self):
        self.redirect(users.create_login_url('/'))


class Logout(Helper):
    def get(self):
        self.redirect(users.create_logout_url('/'))


class Index(Helper):

    def get(self):
        values = self.get_authentication()

        qry_str = self.request.query_string
        if qry_str == '':
            season = Season.get_last_season()
        else:
            try:
                season = Season.get_season(qry_str.split("=")[1])
            except Exception:
                season = None

        if season is None:
            return

        season_dict = dict(season=season.id)
        matches = Match.get_all_matches_season(season.key)
        players = Player.get_players_dict()

        match_round = 1
        list_matches = list()
        for match in matches:
            match_data = {
                'match_round': match_round,
                'match_date': str(match.date),
                'teamA_score': match.scoreA,
                'teamB_score': match.scoreB,
            }

            teamA = []
            for player in match.teamA:
                player_name = players[player].name
                teamA.append(player_name)
            teamB = []
            for player in match.teamB:
                player_name = players[player].name
                teamB.append(player_name)
            match_data['players'] = map(None, teamA, teamB)

            list_matches.append(match_data)
            match_round += 1

        list_matches.reverse()
        season_dict['list_matches'] = list_matches

        """
        values = {
            'matches': [
                {
                    'list_matches': [
                        {
                            match_round:
                            match_date:
                            teamA_score:
                            teamB_score:
                            teamA: []
                            teamB: []
                        }
                    ]
                }
            ],
            'season_list': [
                '2018/2019',
                '2017/2016',
                ...
            ]
        }
        """

        values['matches'] = list()
        values['matches'].append(season_dict)
        values['season_list'] = Season.get_seasons_ids()
        template = self.get_template('list_match.html')
        self.render_webpage(values, template)


class ListStat(Helper):

    def get(self):

        def sorter_percentage(ps):
            return ps.percentage

        def sorter_position(ps):
            return int(ps['position'].replace('.', ''))

        values = self.get_authentication()

        values['season_list'] = Season.get_seasons_ids()

        query_string = self.request.query_string
        if query_string == '':
            season_id = Season.get_last_season().id
        else:
            season_id = query_string.split("=")[1]

        values['season'] = season_id
        season = Season.get_season(season_id)

        values['table'] = list()
        values['notable'] = list()

        player_stats = PlayerStat.get_players_stat_nonzero(season.key)
        player_stats = sorted(player_stats, key=sorter_percentage, reverse=True)

        for ps in player_stats:
            player_data = dict()
            player = ps.key.parent().get()
            player_data['id'] = Player.get_id(player)
            player_data['name'] = Player.get_name(player)
            player_data['won'] = ps.won
            player_data['played'] = ps.played
            player_data['percentage'] = round(ps.percentage, 2)
            player_data['goals_for'] = ps.goals_for
            player_data['goals_against'] = ps.goals_against
            player_data['goals_diff'] = ps.goals_diff
            player_data['streak'] = ps.streak
            if len(player_data['streak']) >= 5:
                player_data['streak'] = player_data['streak'][:5]
            player_data['participation'] = round(ps.participation, 2)

            if ps.ontable is True:
                player_data['position'] = str(ps.position) + '.'
                values['table'].append(player_data)
            else:
                values['notable'].append(player_data)

        values['table'] = sorted(values['table'], key=sorter_position)

        template = self.get_template('list_stat.html')
        self.render_webpage(values, template)


class ListPlayerStat(Helper):

    def get(self):

        def sorter(stat):
            return stat['season']

        values = self.get_authentication()

        player_id = self.request.query_string.split('=')[1]
        player = Player.get_player_by_id(player_id)

        values['player'] = player.name

        all_stat = PlayerStat.get_player_stat_all(player.key)

        values['all'] = dict()
        values['all']['won'] = float()
        values['all']['played'] = int()
        values['all']['percentage'] = float()
        values['all']['goals_for'] = int()
        values['all']['goals_against'] = int()
        values['all']['goals_diff'] = int()

        values['stats'] = list()
        for k, v in all_stat.items():
            stat_data = dict()
            stat_data['season'] = k
            stat_data['position'] = str(v.position) + '.'
            if v.position is None:
                stat_data['position'] = ''
            stat_data['won'] = v.won
            stat_data['played'] = v.played
            stat_data['percentage'] = round(v.percentage, 2)
            stat_data['goals_for'] = v.goals_for
            stat_data['goals_against'] = v.goals_against
            stat_data['goals_diff'] = v.goals_diff
            stat_data['participation'] = round(v.participation, 2)
            values['stats'].append(stat_data)

            values['all']['won'] += v.won
            values['all']['played'] += v.played
            values['all']['goals_for'] += v.goals_for
            values['all']['goals_against'] += v.goals_against
            values['all']['goals_diff'] += v.goals_diff

        values['all']['percentage'] = round(
            float(100 * (values['all']['won']) / values['all']['played']), 2)

        values['stats'] = sorted(values['stats'], key=sorter)

        values['players'] = [x['player_name'] for x in Player.get_players_list()]
        values['players'] = sorted(values['players'])
        values['players'].remove(values['player'])

        matches = Match.get_all_matches()
        headup = dict()
        headup_all = dict()
        for m in matches:

            season = m.key.parent().get().id

            if m.scoreA > m.scoreB:
                points = (1.0, 0.0)
            elif m.scoreB > m.scoreA:
                points = (0.0, 1.0)
            else:
                points = (0.5, 0.5)

            if player.key in m.teamA:
                team = m.teamA
                score = m.scoreA
                scoreagg = m.scoreB
                won = points[0]
            elif player.key in m.teamB:
                team = m.teamB
                score = m.scoreB
                scoreagg = m.scoreA
                won = points[1]
            else:
                continue

            team.remove(player.key)

            for k in team:
                opponent = k.get().name
                empty_dict = dict(won=0.0,
                                  played=0,
                                  percentage=0.0,
                                  goals_for=0,
                                  goals_against=0,
                                  goals_diff=0)
                if opponent not in headup_all:
                    headup_all[opponent] = empty_dict.copy()
                if opponent not in headup:
                    headup[opponent] = dict()
                if season not in headup[opponent]:
                    headup[opponent][season] = empty_dict.copy()

                hoa = headup_all[opponent]
                ho = headup[opponent][season]
                hoa['won'] += won
                ho['won'] += won
                hoa['played'] += 1
                ho['played'] += 1
                hoa['percentage'] = round(100 * (hoa['won'] / hoa['played']), 2)
                ho['percentage'] = round(100 * (ho['won'] / ho['played']), 2)
                hoa['goals_for'] += score
                ho['goals_for'] += score
                hoa['goals_against'] += scoreagg
                ho['goals_against'] += scoreagg
                hoa['goals_diff'] = hoa['goals_for'] - hoa['goals_against']
                ho['goals_diff'] = ho['goals_for'] - ho['goals_against']

        values['seasons'] = Season.get_seasons_ids()
        values['headup'] = headup
        values['headup_all'] = headup_all


        template = self.get_template('list_player_stat.html')
        self.render_webpage(values, template)


class AddSeason(Helper):

    TEMPLATE = 'add_season.html'

    def get(self):
        params = self.init('season')
        if params is None:
            webapp2.abort(404)
        params['seasons'] = Season.get_seasons_ids()
        self.render_webpage(params, self.template)


    def post(self):
        params = self.init('season')
        if params is None:
            webapp2.abort(401)
        season_key = Season.add_season(self.request.get('season'))
        PlayerStat.add_empty_stats_all(season_key)
        self.redirect('add_season')


class AddPlayer(Helper):

    TEMPLATE = 'add_player.html'

    def get(self):
        params = self.init('player')
        if params is None:
            webapp2.abort(404)
        params['player_list'] = Player.get_players_list()
        self.render_webpage(params, self.template)

    def post(self):
        params = self.init('player')
        if params is None:
            webapp2.abort(401)
        name = self.request.get('name')
        player_key = Player.add_player(name=name)
        PlayerStat.add_empty_stats_all_seasons(player_key)
        self.redirect('add_player')


class AddMatch(Helper):

    TEMPLATE = 'add_match.html'

    def get(self):
        params = self.init('match')
        query_string = self.request.query_string
        if query_string == '':
            params['seasons'] = Season.get_seasons_ids()
        else:
            season_id = str()
            query_params = query_string.split('&')
            for qp in query_params:
                qp_elem = qp.split('=')
                if len(qp_elem) != 2:
                    continue
                if qp_elem[0] == 'season':
                    season_id = qp_elem[1]
            season = Season.get_season(season_id)
            params['matches'] = Match.get_match_data_season(season.key)
            params['season'] = season_id
            params['player_list'] = Player.get_players_list()
            params['add_match_block'] = True
        self.render_webpage(params, self.template)


    def post(self):
        params = self.init('player')
        if params is None:
            webapp2.abort(401)
        match = dict()
        # Parse season
        delete = self.request.get('delete')
        if delete:
            self.delete(self.request.get('date'))
            self.redirect('add_match')
            return

        season = self.request.get('season')
        season_entry = Season.get_season(season)
        if season_entry is None:
            webapp2.abort(404)

        match['season'] = season_entry.key
        date = self.request.get('match_date')
        match['date'] = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        match['scoreA'] = int(self.request.get('teamA_score'))
        match['scoreB'] = int(self.request.get('teamB_score'))
        match['teamA'] = list()
        match['teamB'] = list()

        for i in range(1, 10):
            playerA = self.request.get('teamA_{}'.format(str(i)))
            playerB = self.request.get('teamB_{}'.format(str(i)))

            if playerA == '' and playerB == '':
                break

            if playerA != '':
                playerA_obj = Player.get_player_by_name(name=playerA)
                if playerA_obj is not None:
                    match['teamA'].append(playerA_obj.key)
                else:
                    webapp2.abort(404)

            if playerB != '':
                playerB_obj = Player.get_player_by_name(name=playerB)
                if playerB_obj is not None:
                    match['teamB'].append(playerB_obj.key)
                else:
                    webapp2.abort(404)

        Match.add_match(match)
        PlayerStat.update_players_stat(season_key=season_entry.key)
        self.redirect('add_match')

    def delete(self, date):
        params = self.init('match')
        if params['authorization_match_add'] is True:
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            Match.delete_match(date)


class UpdateStat(Helper):

    def get(self):
        params = self.init('match')
        if params['authorization_match_add'] is not True:
            webapp2.abort(401)

        season = self.request.get('season')
        season_entry = Season.get_season(season)
        if season_entry is None:
            webapp2.abort(404)

        PlayerStat.update_players_stat(season_key=season_entry.key)
        self.redirect('add_match')



class Test(Helper):

    def get(self):
        season = Season.get_season('2012/2013')
        PlayerStat.update_players_stat(season_key=season.key)


app = webapp2.WSGIApplication([
    ('/', Index),
    ('/list_stat', ListStat),
    ('/list_player_stat', ListPlayerStat),
    ('/login', Login),
    ('/logout', Logout),
    ('/add_season', AddSeason),
    ('/add_player', AddPlayer),
    ('/add_match', AddMatch),
    ('/update_stat', UpdateStat),
], debug=DEBUG)

if DEBUG:
    add_admin(FIRST_ADMIN)
