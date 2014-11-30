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

import random
import datetime


from google.appengine.api import users

from models import *

JINJA_ENVIRONMENT=jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)



class TemplateRender(webapp2.RequestHandler):
    def render_webpage(self,template_values,template):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render(template_values))

    def get_template(self,template_file):
        return JINJA_ENVIRONMENT.get_template(template_file)

class Index(TemplateRender):

#template_values:
#
#{
#'authorization_season_add':  
#'authorization_payment_view':
#'authorization_match_add': 
#'authorization_payment_add':
#'authenticated': 
#'authorization_player_add':
#'authorization_admin':
#'matches': [
#	{
#	'season': 
#	'list_matches': [
#		{
#		'match_round':
#		'teamA_score':
#		'teamB_score': 
#		'match_date': 
#		'players': []
#		}
#	] 
#	}
#] 
#}

    def get(self):
        user = users.get_current_user()
        if user:
            template_values = UserAuthorization.get_authorization(user.email())
            template_values['authenticated'] = True
        else:
            template_values = {}

        season_id = self.request.query_string
        if season_id == '':
            season = Season.get_season_list()[0]
        else:
            season = season_id.split("=")[1]
        
        matches = []
        #for season in season_list:
        season_dict = {'season': season}
        season_key = Season.get_season_key(season)
        if season_key:
            all_matches_in_season = Match.get_all_matches(season_key)
        else:
            webapp2.abort(404)
        list_matches = []
        for match in all_matches_in_season:
            match_data = {
                'match_round': match.match_round,
                'match_date': match.match_date,
                'teamA_score': match.teamA_score,
                'teamB_score': match.teamB_score,
            }
            teamA = [Player.get_player_by_id(player) for player in match.teamA]
            teamB = [Player.get_player_by_id(player) for player in match.teamB]
            teamA_players = []
            for player in teamA:
                teamA_players.append(player['player_lastname'] + ' ' + player['player_firstname'])
            teamB_players = []
            for player in teamB:
                teamB_players.append(player['player_lastname'] + ' ' + player['player_firstname'])
            match_data['players'] = map(None,teamA_players,teamB_players)
            list_matches.append(match_data)
        season_dict['list_matches'] = list_matches
        matches.append(season_dict)
        template_values['matches'] = matches

        season_list = Season.get_season_list()
        template_values['season_list'] = season_list
        self.render_webpage(template_values,self.get_template('list_match.html'))
        #self.response.write(Season.get_season_key(season))


class AddSeason(TemplateRender):
    def get(self):
        user = users.get_current_user()
        if user:
            template_values = UserAuthorization.get_authorization(user.email())
            template_values['authenticated'] = True
            if template_values['authorization_season_add']:
                season_list = Season.get_season_list()
                template_values['seasons'] = season_list
                self.render_webpage(template_values,self.get_template('add_season.html'))
            else:
                template_values['error_msg_authorization'] = True
                self.render_webpage(template_values,self.get_template('add_season.html'))
        else:
            template_values = {'error_msg_login': True}
            self.render_webpage(template_values,self.get_template('add_season.html'))
 

    def post(self):
        user = users.get_current_user()
        if user:
            user_authorization = UserAuthorization.get_authorization(user.email())
            if user_authorization['authorization_season_add']:
                season_number = self.request.get('season')
                season = Season(id=season_number)
                season.put()       
                self.redirect('add_season')
            else:
                template_values['error_msg_authorization'] = True
                self.render_webpage(template_values,self.get_template('add_season.html'))
        else:
            template_values = {'error_msg_login': True}
            self.render_webpage(template_values,self.get_template('add_season.html'))


class AddPlayer(TemplateRender):

#template_values:
#
#{
#'authorization_season_add':  
#'authorization_payment_view':
#'authorization_match_add': 
#'authorization_payment_add':
#'authenticated': 
#'authorization_player_add':
#'authorization_admin':
#'players': [
#	{
#	'season': 
#	'player_list': [
#		{
#		'player_id':
#		'player_firstname':
#		'player_lastname': 
#		}
#	] 
#	}
#] 
#}


    def get(self):
        user = users.get_current_user()
        if user:
            template_values = UserAuthorization.get_authorization(user.email())
            template_values['authenticated'] = True
            if template_values['authorization_player_add']:
                season_list = Season.get_season_list()
                player_data_season = []
                for season in season_list:
                    player_list = Player.get_all_players_from_season(Season.get_season_key(season))
                    player_data = []
                    for player in player_list:
                        player_dict = {
                            'player_id': player.player_id,
                            'player_firstname': player.player_firstname,
                            'player_lastname': player.player_lastname,
                        }
                        player_data.append(player_dict)
                    player_data_season.append({'season': season, 'player_list': player_data})
                template_values['players'] = player_data_season
                self.render_webpage(template_values,self.get_template('add_player.html'))
            else:
                template_values['error_msg_authorization'] = True
                self.render_webpage(template_values,self.get_template('add_player.html'))
        else:
            template_values = {'error_msg_login': True}
            self.render_webpage(template_values,self.get_template('add_player.html'))

    def post(self):
        user = users.get_current_user()
        if user:
            template_values = UserAuthorization.get_authorization(user.email())
            if template_values['authorization_player_add']:
                player_id = int(Player.get_highest_player_id() + 1)
                player_firstname = self.request.get('firstname')
                player_lastname = self.request.get('lastname')
                player_season = self.request.get('season')
                season_key = Season.get_season_key(player_season)
                player_data = {
                    'player_id': player_id,
                    'player_firstname': player_firstname,
                    'player_lastname': player_lastname,
                    'season_key': season_key
                }
                player_key = Player.add_player(player_data)
                PlayerStat.init_player_stat(player_key)
                self.redirect('add_player')
            else:
                template_values['error_msg_authorization'] = True
                self.render_webpage(template_values,self.get_template('add_player.html'))
        else:
            template_values = {'error_msg_login': True}
            self.render_webpage(template_values,self.get_template('add_player.html'))


class AddMatch(TemplateRender):
    def get(self):
        user = users.get_current_user()
        if user:
            template_values = UserAuthorization.get_authorization(user.email())
            template_values['authenticated'] = True
            if template_values['authorization_match_add']:
                season = self.request.query_string
                if season == '':
                    season_list = Season.get_season_list()
                    template_values['seasons'] = season_list
                else:
                    season = season.split("=")[1]
                    season_key = Season.get_season_key(season)
                    players = Player.get_all_players_from_season(season_key)
                    player_list = []
                    for player in players:
                        player_list.append({
                            'player_id': player.player_id,
                            'player_firstname': player.player_firstname,
                            'player_lastname': player.player_lastname,
                        })
                    template_values['season'] = season
                    template_values['player_list'] = player_list
                    template_values['add_match_block'] = True
                self.render_webpage(template_values,self.get_template('add_match.html'))

            else:
                template_values['error_msg_authorization'] = True
                self.render_webpage(template_values,self.get_template('add_match.html'))
        else:
            template_values = {'error_msg_login': True}
            self.render_webpage(template_values,self.get_template('add_match.html'))

    def post(self):
        user = users.get_current_user()
        if user:
            template_values = UserAuthorization.get_authorization(user.email())
            if template_values['authorization_match_add']:
                request_data = self.request.body.split('&')
                season = request_data[0].split('=')[1]
                season_key = Season.get_season_key(season)
                match_date = request_data[1].split('=')[1].split('-')
                teamA_score = int(request_data[2].split('=')[1])
                teamB_score = int(request_data[3].split('=')[1])
                match_round = Match.get_highest_match_round(season_key) + 1
                teamA = []
                teamB = []
                for player in request_data[4:]:
                    player_split = player.split('=')
                    if not player_split[1] == '':
                        if player[4] == 'A':
                            teamA.append(int(player_split[1]))
                        elif player[4] == 'B':
                            teamB.append(int(player_split[1]))
                match_data = {
                    'season_key': season_key,
                    'match_round': match_round,
                    'match_date': datetime.date(int(match_date[0]),int(match_date[1]),int(match_date[2])),
                    'teamA_score': teamA_score,
                    'teamB_score': teamB_score,
                    'teamA': teamA,
                    'teamB': teamB,
                }
                Match.add_match(match_data)
                
                players = Player.get_all_players_from_season(season_key)
                for player in players:
                    if player.player_id in teamA+teamB:
                        match_data = {'played': 1}
                        if teamA_score > teamB_score:
                            if player.player_id in teamA:
                                match_data['win'] = 1
                            elif player.player_id in teamB:
                                match_data['win'] = 0
                        elif teamA_score == teamB_score:
                            match_data['win'] = 0.5
                        else:
                            if player.player_id in teamA:
                                match_data['win'] = 0
                            elif player.player_id in teamB:
                                match_data['win'] = 1
                        if player.player_id in teamA:
                            match_data['goals_for'] = teamA_score
                            match_data['goals_against'] = teamB_score
                        else:
                            match_data['goals_for'] = teamB_score
                            match_data['goals_against'] = teamA_score
                    else:
                        match_data = {'played': 0, 'win': 0, 'goals_for': 0, 'goals_against': 0}
                    PlayerStat.update_player_stat(player.key,match_data,match_round)
                self.redirect('add_match')


            else:
                template_values['error_msg_authorization'] = True
                self.render_webpage(template_values,self.get_template('add_match.html'))
        else:
            template_values = {'error_msg_login': True}
            self.render_webpage(template_values,self.get_template('add_match.html'))

class ListStat(TemplateRender):

#template_values:
#
#{
#'authorization_season_add':  
#'authorization_payment_view':
#'authorization_match_add': 
#'authorization_payment_add':
#'authenticated': 
#'authorization_player_add':
#'authorization_admin':
#'players_stat': [
#	{
#	'season': 
#	'player_list': [
#		{
#		'player_id':
#		'player_firstname':
#		'player_lastname': 
#		}
#	] 
#	}
#] 
#}

    def get(self):
        user = users.get_current_user()
        if user:
            template_values = UserAuthorization.get_authorization(user.email())
            template_values['authenticated'] = True
        else:
            template_values = {}

        season_id = self.request.query_string
        if season_id == '':
            season = Season.get_season_list()[0]
        else:
            season = season_id.split("=")[1]


        stat_list = []
        #for season in season_list:
        season_key = Season.get_season_key(season)
        if season_key:
            player_stat_for_season = PlayerStat.get_player_stat(Season.get_season_key(season))
        else:
            webapp2.abort(404)
        
        all_players_data = []
        counter = 1
        for player_stat in player_stat_for_season:
            player = player_stat.key.parent().get()
            player_data = {
                'player_id': player.player_id,
                'player_firstname': player.player_firstname,
                'player_lastname': player.player_lastname,
                'player_ontable': player_stat.on_table,
                'player_number_of_games_played': player_stat.number_of_games_played,
                'player_wins': player_stat.wins,
                'player_wins_percentage': format(player_stat.wins_percentage,'.2f'),
                'player_goals_for': player_stat.goals_for,
                'player_goals_against': player_stat.goals_against,
                'player_goals_diff': player_stat.goals_diff,
                'player_participation': format(player_stat.participation, '.2f'), 
            }
            if player_stat.on_table:
                player_data['player_position'] = counter
                counter = counter + 1
            else:
                player_data['player_position'] = 0
            all_players_data.append(player_data)
        stat_list.append({'season': season, 'player_stat': all_players_data})
        template_values['stat_list'] = stat_list

        season_list = Season.get_season_list()
        template_values['season_list'] = season_list

        ## Za per player statistiko

        all_players = Player.get_all_players_from_season(season_key)
        all_matches = Match.get_all_matches(season_key)
        player_position_in_matrix = {}
        matrix_data = {
            'wins': 0,
            'matches': 0,
            'percentage': 0.0,
            'goals_for': 0,
            'goals_against': 0,
            'goals_diff': 0,
        }
        matrix = [[matrix_data for x in range(len(all_players))] for x in range(len(all_players))]
        counter = 0
        for player in all_players:
            player_position_in_matrix[player.player_id] = counter
            counter = counter + 1

        for match in all_matches:
            teamA = match.teamA
            teamB = match.teamB
            teamA_score = match.teamA_score
            teamB_score = match.teamB_score

            for player in teamA:
                if teamA_score > teamB_score:
                    wins = 1
                elif teamA_score == teamB_score:
                    wins = 0.5
                else:
                    wins = 0

                for player2 in teamA:
                    if player != player2:
                        current_data = matrix[player_position_in_matrix[player]][player_position_in_matrix[player2]].copy()
                        current_data['wins'] = current_data['wins'] + wins
                        current_data['matches'] = current_data['matches'] + 1
                        current_data['percentage'] = format(100*current_data['wins']/float(current_data['matches']),'.2f')
                        current_data['goals_for'] = current_data['goals_for'] + teamA_score
                        current_data['goals_against'] = current_data['goals_against'] + teamB_score
                        current_data['goals_diff'] = current_data['goals_for'] - current_data['goals_against']
                        matrix[player_position_in_matrix[player]][player_position_in_matrix[player2]] = current_data
                    else:
                        matrix[player_position_in_matrix[player]][player_position_in_matrix[player2]] = None

            for player in teamB:
                if teamA_score > teamB_score:
                    wins = 0
                elif teamA_score == teamB_score:
                    wins = 0.5
                else:
                    wins = 1

                for player2 in teamB:
                    if player != player2:
                        current_data = matrix[player_position_in_matrix[player]][player_position_in_matrix[player2]].copy()
                        current_data['wins'] = current_data['wins'] + wins
                        current_data['matches'] = current_data['matches'] + 1
                        current_data['percentage'] = format(100*current_data['wins']/float(current_data['matches']),'.2f')
                        current_data['goals_for'] = current_data['goals_for'] + teamB_score
                        current_data['goals_against'] = current_data['goals_against'] + teamA_score
                        current_data['goals_diff'] = current_data['goals_for'] - current_data['goals_against']
                        matrix[player_position_in_matrix[player]][player_position_in_matrix[player2]] = current_data
                    else:
                        matrix[player_position_in_matrix[player]][player_position_in_matrix[player2]] = None

        player_index_list = range(len(all_players))
        for player_key in player_position_in_matrix.keys():
            player = Player.get_player_by_id(player_key)
            player_index_list[player_position_in_matrix[player_key]] = player['player_lastname'] + ' ' + player['player_firstname']
        template_values['player_index_list'] = player_index_list
        template_values['per_player_stat'] = matrix
        self.render_webpage(template_values,self.get_template('list_stat.html'))


class AddPayment(TemplateRender):
    def get(self):
        user = users.get_current_user()
        if user:
            template_values = UserAuthorization.get_authorization(user.email())
            template_values['authenticated'] = True
            if template_values['authorization_payment_add']:
                season_list = Season.get_season_list()
                for season in season_list:
                    player_list = Player.get_all_players_from_season(Season.get_season_key(season))

                season_string = self.request.query_string
                if season_string == '':
                    season_list = Season.get_season_list()
                    template_values['seasons'] = season_list
                else:
                    season = season_string.split("=")[1]
                    season_key = Season.get_season_key(season)
                    players = Player.get_all_players_from_season(season_key)
                    player_list = []
                    for player in players:
                        player_list.append({
                            'player_id': player.player_id,
                            'player_firstname': player.player_firstname,
                            'player_lastname': player.player_lastname,
                        })
                    template_values['season'] = season
                    template_values['player_list'] = player_list
                    template_values['add_payment_block'] = True
                self.render_webpage(template_values,self.get_template('add_payment.html'))

            else:
                template_values['error_msg_add_payment'] = True
                self.render_webpage(template_values,self.get_template('add_payment.html'))
        else:
            template_values = {'error_msg_login': True}
            self.render_webpage(template_values,self.get_template('add_payment.html'))

    def post(self):
        user = users.get_current_user()
        if user:
            template_values = UserAuthorization.get_authorization(user.email())
            if template_values['authorization_payment_add']:
                request_data = self.request.body.split('&')
                season = request_data[0].split('=')[1]
                match_date = request_data[1].split('=')[1].split('-')
                number_of_entries = len(request_data[2:])/3
                for i in range(number_of_entries):
                    player_data = {
                       'player_key': Player.get_player_key_by_id(int(request_data[2 + i*3].split('=')[1])),
                       'date': datetime.date(int(match_date[0]),int(match_date[1]),int(match_date[2])),
                       'payment': float(request_data[3 + i*3].split('=')[1]),
                       'debt': float(request_data[4 + i*3].split('=')[1]),
                    }
                    payment_key = PlayerPayments.add_payment(player_data)
                
                self.redirect('add_payment')

            else:
                template_values['error_msg_authorization'] = True
                self.render_webpage(template_values,self.get_template('add_match.html'))
        else:
            template_values = {'error_msg_login': True}
            self.render_webpage(template_values,self.get_template('add_match.html'))

class ListPayments(TemplateRender):
    def get(self):
        user = users.get_current_user()

        if user:
            template_values = UserAuthorization.get_authorization(user.email())
            template_values['authenticated'] = True
            if template_values['authorization_payment_view']:
                request_player_id = self.request.query_string
                if request_player_id == '':
                    template_values['payments_list_block'] = True
                    season_list = Season.get_season_list()
                    payments = []
                    for season in season_list:
                        player_list = Player.get_all_players_from_season(Season.get_season_key(season))
                        payment_for_player_season = []
                        for player in player_list:
                            player_payments_data = PlayerPayments.calculate_payment_data(player.key)
                            player_payments_data['player_owe'] = player_payments_data['player_debt'] - player_payments_data['player_payments']
                            player_payments_data['player_id'] = player.player_id
                            player_payments_data['player_firstname'] = player.player_firstname
                            player_payments_data['player_lastname'] = player.player_lastname
                            payment_for_player_season.append(player_payments_data)
                        payments.append({'season': season, 'player_payment_data': payment_for_player_season})
                    template_values['payments'] = payments
                    
                else:
                    player_id = int(request_player_id.split('=')[1])
                    player_key = Player.get_player_key_by_id(player_id)
                    player_data = player_key.get()
                    template_values['player_firstname'] = player_data.player_firstname
                    template_values['player_lastname'] = player_data.player_lastname
                    player_payments = PlayerPayments.get_all_payments_for_player(player_key)
                    payments = []
                    if player_payments:
                        for payment in player_payments:
                            payments.append({
                                'payment_date': payment.date,
                                'payment_payment': payment.payment,
                                'payment_debt': payment.debt,
                            })
                    template_values['payments'] = payments
                self.render_webpage(template_values,self.get_template('list_payments.html'))
            else:
                template_values['error_msg_list_payments'] = True
                self.render_webpage(template_values,self.get_template('list_payments.html'))
        else:
            template_values = {'error_msg_login': True}
            self.render_webpage(template_values,self.get_template('list_payments.html'))

class Login(TemplateRender):
    def get(self):
        self.redirect(users.create_login_url('/'))

class Logout(TemplateRender):
    def get(self):
        self.redirect(users.create_logout_url('/'))


class Authorization(TemplateRender):
    def get(self):
        template_values = {}
        self.render_webpage(template_values,self.get_template('authorization.html'))


    def post(self):
        user_email = self.request.get('email')
        user_admin = True if self.request.get('admin') == 'on' else False
        user_season = True if self.request.get('season') == 'on' else False
        user_player = True if self.request.get('player') == 'on' else False
        user_match = True if self.request.get('match') == 'on' else False
        user_payment_add = True if self.request.get('payment_add') == 'on' else False
        user_payment_view = True if self.request.get('payment_view') == 'on' else False
        userauthorization = UserAuthorization(
            user_email = user_email,
            authorization_payment_view = user_payment_view,
            authorization_payment_add = user_payment_add,
            authorization_season_add = user_season,
            authorization_player_add = user_player,
            authorization_match_add = user_match,
            authorization_admin = user_admin)
        userauthorization.put()
        self.response.write(userauthorization)
    
class Test(TemplateRender):
    def get(self):

        all_seasons = Season.get_season_list()
        season_key = Season.get_season_key(all_seasons[0])
        all_players = Player.get_all_players_from_season(season_key)
        all_matches = Match.get_all_matches(season_key)
        player_position_in_matrix = {}
        matrix_data = {
            'wins': 0,
            'matches': 0,
            'percentage': 0.0,
            'goals_for': 0,
            'goals_against': 0,
            'goals_diff': 0,
        }
        matrix = [[matrix_data for x in range(len(all_players))] for x in range(len(all_players))]
        counter = 0
        for player in all_players:
            player_position_in_matrix[player.player_id] = counter
            counter = counter + 1

        for match in all_matches:
            teamA = match.teamA
            teamB = match.teamB
            teamA_score = match.teamA_score
            teamB_score = match.teamB_score

            for player in teamA:
                #self.response.write(player)
                if teamA_score > teamB_score:
                    wins = 1
                elif teamA_score == teamB_score:
                    wins = 0.5
                else:
                    wins = 0

                self.response.write(player)
                for player2 in teamA:
                    
                    self.response.write(player2)
                    if player != player2:
                        current_data = matrix[player_position_in_matrix[player]][player_position_in_matrix[player2]].copy()
                        #self.response.write(current_data)
                        
                        current_data['wins'] = current_data['wins'] + wins
                        #self.response.write(current_data)
                        #self.response.write(matrix)
                        self.response.write('<br>')
                        current_data['matches'] = current_data['matches'] + 1
                        current_data['percentage'] = format(current_data['wins']/float(current_data['matches']),'.2f')
                        current_data['goals_for'] = current_data['goals_for'] + teamA_score
                        current_data['goals_against'] = current_data['goals_against'] + teamB_score
                        current_data['goals_diff'] = current_data['goals_for'] - current_data['goals_against']
                        matrix[player_position_in_matrix[player]][player_position_in_matrix[player2]] = current_data
                    else:
                        matrix[player_position_in_matrix[player]][player_position_in_matrix[player2]] = None

            for player in teamB:
                #self.response.write(player)
                if teamA_score > teamB_score:
                    wins = 0
                elif teamA_score == teamB_score:
                    wins = 0.5
                else:
                    wins = 1

                self.response.write(player)
                for player2 in teamB:
                    
                    self.response.write(player2)
                    if player != player2:
                        current_data = matrix[player_position_in_matrix[player]][player_position_in_matrix[player2]].copy()
                        #self.response.write(current_data)
                        
                        current_data['wins'] = current_data['wins'] + wins
                        #self.response.write(current_data)
                        #self.response.write(matrix)
                        self.response.write('<br>')
                        current_data['matches'] = current_data['matches'] + 1
                        current_data['percentage'] = format(current_data['wins']/float(current_data['matches']),'.2f')
                        current_data['goals_for'] = current_data['goals_for'] + teamB_score
                        current_data['goals_against'] = current_data['goals_against'] + teamA_score
                        current_data['goals_diff'] = current_data['goals_for'] - current_data['goals_against']
                        matrix[player_position_in_matrix[player]][player_position_in_matrix[player2]] = current_data
                    else:
                        matrix[player_position_in_matrix[player]][player_position_in_matrix[player2]] = None
 
        self.response.write('<br>')
        self.response.write('<br>')
        self.response.write(player_position_in_matrix)   
        self.response.write('<br>')
        self.response.write('<br>')
        self.response.write('<table border="1" style="width:100%"><tr><td>')
        for i in matrix:
            for j in i:
                self.response.write(j)
                self.response.write('<br>')
            self.response.write('<br>')
        self.response.write('</td></tr></table>')       
        # self.response.write(matrix)
        #self.response.write(all_players)
        #self.response.write(all_matches)
        #self.response.write(player_position_in_matrix)
        #self.response.write(len(all_players))


        #self.render_webpage(template_values,self.get_template('list_stat.html'))


app = webapp2.WSGIApplication([
    ('/', Index),
    ('/add_season', AddSeason),
    ('/add_player', AddPlayer),
    ('/add_match', AddMatch),
    ('/list_stat', ListStat),
    ('/add_payment', AddPayment),
    ('/list_payments', ListPayments),
    ('/authorization', Authorization),
    ('/login', Login),
    ('/logout', Logout),
    ('/test', Test),
], debug=False)

