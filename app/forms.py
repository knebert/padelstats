from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField, DateField, FileField
from wtforms.validators import DataRequired, ValidationError
from flask_wtf.file import FileField, FileRequired
from app.models import Player, Team
from datetime import datetime


class LoginForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Sign In')


class AddPlayerForm(FlaskForm):
	firstname = StringField('First name', validators=[DataRequired()])
	lastname = StringField('Last name', validators=[DataRequired()])
	submit = SubmitField('Add Player')
	delete = SubmitField('Delete All')


class AddGameForm(FlaskForm):
	date = DateField('Date', format='%Y-%m-%d', default=datetime.today, validators=[DataRequired()])
	team1 = SelectField('Team 1', coerce=int, validators=[DataRequired()])
	team2 = SelectField('Team 2', coerce=int, validators=[DataRequired()])
	score_team1 = IntegerField('Score Team 1')
	score_team2 = IntegerField('Score Team 2')
	SubmitField = SubmitField('Add Game')


class EditGameForm(FlaskForm):
	date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
	team1 = SelectField('Team 1', coerce=int, validators=[DataRequired()])
	team2 = SelectField('Team 2', coerce=int, validators=[DataRequired()])
	score_team1 = IntegerField('Score Team 1')
	score_team2 = IntegerField('Score Team 2')
	submit = SubmitField('Update Game')
	cancel = SubmitField('Cancel')
	delete = SubmitField('Delete')


class UploadPlayersForm(FlaskForm):
	file = FileField()
	submit = SubmitField('Upload')
	save = SubmitField('Export to CSV')
	delete = SubmitField('Delete All Players')


class UploadGamesForm(FlaskForm):
	file = FileField()
	submit = SubmitField('Upload')
	save = SubmitField('Export to CSV')
	delete = SubmitField('Delete All Games')


class FilterPlayerForm(FlaskForm):
	all_games = SubmitField('All')
	games_2018 = SubmitField('2018')
	games_2019 = SubmitField('2019')
