from datetime import datetime
from app import db
from sqlalchemy import and_, or_

class Player(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	firstname = db.Column(db.String(32), index=True)
	lastname = db.Column(db.String(32), index=True)
	teams = db.relationship('Team', primaryjoin="or_(Player.id==Team.player1_id, Player.id==Team.player2_id)", lazy='dynamic')

	def __repr__(self):
		return '<Player {}>'.format(self.firstname)


class Team(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	teamname = db.Column(db.String(64), index=True, unique=True)
	player1_id = db.Column(db.Integer, db.ForeignKey('player.id'))
	player2_id = db.Column(db.Integer, db.ForeignKey('player.id'))

	player1 = db.relationship("Player", foreign_keys=[player1_id])
	player2 = db.relationship("Player", foreign_keys=[player2_id])

	#games = db.relationship('Game', primaryjoin='or_(Team.id==Game.team1_id, Team.id==Game.team2_id)', lazy='dynamic')

	def __repr__(self):
		return '<Team {}>'.format(self.teamname)

class Game(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.Date)
	team1_id = db.Column(db.Integer, db.ForeignKey('team.id'))
	team2_id = db.Column(db.Integer, db.ForeignKey('team.id'))
	score_team1 = db.Column(db.Integer)
	score_team2 = db.Column(db.Integer)
	winner_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
	loser_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

	team1 = db.relationship('Team', foreign_keys=[team1_id])
	team2 = db.relationship('Team', foreign_keys=[team2_id])
	winner = db.relationship('Team', foreign_keys=[winner_team_id])
	loser = db.relationship('Team', foreign_keys=[loser_team_id])

	def __repr__(self):
		return '<Game {} vs. {}: {}-{}>'.format(self.team1, self.team2, self.score_team1, self.score_team2)

	def get_team_result_table(self, teamid):
		winning_games = Game.query.filter_by(winner_team_id=teamid)
		losing_games = Game.query.filter_by(loser_team_id=teamid)

		stats = {}
		stats['Wins'] = winning_games.count()
		stats['Losses'] = losing_games.count()
		stats['Total'] = stats['Wins'] + stats['Losses']
		stats['Win Ratio'] = stats['Wins'] / stats['Total']
		return stats

	def get_player_result_table(self, teams):
		winning_games = 0
		losing_games = 0
		for t in teams:
			winning_games += Game.query.filter_by(winner_team_id=t).count()
			losing_games += Game.query.filter_by(loser_team_id=t).count()

		stats = {}
		stats['Wins'] = winning_games
		stats['Losses'] = losing_games
		stats['Total'] = stats['Wins'] + stats['Losses']
		stats['Win Ratio'] = stats['Wins'] / stats['Total']

		return stats

	def get_players_result_table(self):
		players = Player.query.all()
		table = {}

		for p in players:
			teams = p.teams.all()
			team_ids = []
			for t in teams:
				team_ids.append(t.id)

			table_player = {}
			winning_games = 0
			losing_games = 0

			for t in team_ids:
				winning_games += Game.query.filter_by(winner_team_id=t).count()
				losing_games += Game.query.filter_by(loser_team_id=t).count()

			table_player['ID'] = p.id
			table_player['W'] = winning_games
			table_player['L'] = losing_games
			table_player['PLD'] = table_player['W'] + table_player['L']
			if table_player['PLD'] > 0:
				table_player['WR'] = table_player['W'] / table_player['PLD']
			else:
				table_player['WR'] = 0.0

			table[p.firstname] = table_player

		# sort dictionary based on win ratio
		table_sorted = sorted(table.items(), key=lambda k: k[1]['WR'], reverse=True)

		# add rank
		i = 1
		for t in table_sorted:
			t[1]['RANK'] = i
			i = i + 1
		return table_sorted

	def get_teams_result_table(self):
		teams = Team.query.all()
		table = {}

		for t in teams:
			table_team = {}
			winning_games = Game.query.filter_by(winner_team_id=t.id).count()
			losing_games = Game.query.filter_by(loser_team_id=t.id).count()

			table_team['ID'] = t.id
			table_team['PLD'] = winning_games + losing_games
			table_team['W'] = winning_games
			table_team['L'] = losing_games
			if table_team['PLD'] > 0:
				table_team['WR'] = table_team['W'] / table_team['PLD']
			else:
				table_team['WR'] = 0.0

			table[t.teamname] = table_team

		# sort dictionary based on win ratio
		table_sorted = sorted(table.items(), key=lambda k: k[1]['WR'], reverse=True)

		# add rank
		i = 1
		for t in table_sorted:
			t[1]['RANK'] = i
			i = i + 1

		return table_sorted