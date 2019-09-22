from flask import render_template, flash, redirect, url_for, request, Markup
from app import app, db, charts
from app.forms import LoginForm, AddPlayerForm, AddGameForm, EditGameForm, \
    UploadPlayersForm, UploadGamesForm, FilterPlayerForm
from app.models import Player, Team, Game
from sqlalchemy import or_, distinct
from flask_googlecharts import BarChart, ColumnChart
from io import TextIOWrapper
from datetime import datetime
import csv


@app.route('/')
@app.route('/index')
def index():
    games = Game.query.all()
    return render_template('index.html', title="Home", games=games)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}, password={}'.format(
            form.username.data, form.remember_me.data, form.password.data))
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/addplayer', methods=['GET', 'POST'])
def addplayer():
    form = AddPlayerForm()
    players = Player.query.all()

    if form.validate_on_submit() and 'submit' in request.form:
        player = Player(firstname=form.firstname.data, lastname=form.lastname.data)
        db.session.add(player)
        db.session.commit()

        # If more than 2 players automatically create teams for the newly added player
        if len(Player.query.all()) > 1:
            latest_player = Player.query.order_by(Player.id.desc()).first()
            all_players = Player.query.all()
            created_teams = create_teams(latest_player.id, all_players)
            flash(prepare_flash_message("New player was added and following teams were created: ", created_teams))
        else:
            flash('New player was added')
        return redirect(url_for('addplayer'))

    return render_template('addplayer.html', title='Add new player', form=form, players=players)


def delete_players():
    all_players = Player.query.all()
    for p in all_players:
        db.session.delete(p)
    db.session.commit()


def create_teams(player_id, players):
    new_player = Player.query.get(player_id)
    teams_added = []
    for p in players:
        if new_player.id != p.id:
            if new_player.firstname < p.firstname:
                team_name = new_player.firstname + ' / ' + p.firstname
                player_1 = new_player.id
                player_2 = p.id
            else:
                team_name = p.firstname + ' / ' + new_player.firstname
                player_1 = p.id
                player_2 = new_player.id
            db.session.add(Team(teamname=team_name, player1_id=player_1, player2_id=player_2))
            teams_added.append(team_name)
    db.session.commit()

    return teams_added

def delete_teams():
    all_teams = Team.query.all()
    for t in all_teams:
        db.session.delete(t)
    db.session.commit()


@app.route('/addgame', methods=['GET', 'POST'])
def addgame():
    teams = Team.query.order_by(Team.teamname).all()
    teams_list = [(t.id, t.teamname) for t in teams]
    form = AddGameForm()
    form.team1.choices = teams_list
    form.team2.choices = teams_list
    if form.validate_on_submit():
        date = form.date.data
        team1 = form.team1.data
        team2 = form.team2.data
        score_team1 = form.score_team1.data
        score_team2 = form.score_team2.data
        winner = team1
        loser = team2
        if score_team1 < score_team2:
            winner = team2
            loser = team1

        game = Game(date=date, team1_id=team1, team2_id=team2, score_team1=score_team1, score_team2=score_team2,
                    winner_team_id=winner, loser_team_id=loser)
        db.session.add(game)
        db.session.commit()
        flash('New game was added')
        return redirect(url_for('addgame'))
    return render_template('addgame.html', title='Add new game', form=form)


@app.route('/players', methods=['GET', 'POST'])
def players():
    form = FilterPlayerForm()
    active = 'all'
    if request.method == 'POST' and 'games_2019' in request.form:
        games_2019 = Game.query.filter(Game.date.between('2019-01-01', '2019-12-31')).all()
        player_stats = get_players_stats(games_2019)
        active = '2019'
    elif request.method == 'POST' and 'games_2018' in request.form:
        games_2018 = Game.query.filter(Game.date.between('2018-01-01', '2018-12-31')).all()
        player_stats = get_players_stats(games_2018)
        active = '2018'
    elif request.method == 'POST' and 'all_games' in request.form:
        all_games = Game.query.all()
        player_stats = get_players_stats(all_games)
    else:
        all_games = Game.query.all()
        player_stats = get_players_stats(all_games)
    return render_template('players.html', player_stats=player_stats, form=form, active=active)

@app.route('/player/<firstname>')
def player(firstname):
    all_games = Game.query.all()
    player = Player.query.filter_by(firstname=firstname).first_or_404()
    teams = player.teams.all()

    # Get stats for all players
    all_players_table = get_players_stats(all_games)

    # Get stats only for one player
    player_table = next(item for item in all_players_table if item['name'] == player.firstname)
    player_table['players'] = len(all_players_table)
    player_table['rounds'] = 0
    player_table['round_wins'] = 0

    # Round stats for player
    # Filter out games for a specific player
    player_games = []
    for g in all_games:
        if(g.winner.player1.firstname == player.firstname or g.winner.player2.firstname == player.firstname or
        g.loser.player1.firstname == player.firstname or g.loser.player2.firstname == player.firstname):
            player_games.append(g)

    # Find dates a player has played
    dates = {}
    for g in player_games:
        dates[g.date] = g.date

    # For each date get table
    player_round_stats = []
    for d in dates:
        round_games = Game.query.filter_by(date=d).all()
        all_player_round_stats = get_players_stats(round_games)
        # only keep players stats
        for p in all_player_round_stats:
            if p['name'] == player.firstname:
                player_round_stats.append(p)
        player_round_stats[-1]['date'] = d
        player_round_stats[-1]['players'] = len(all_player_round_stats)

    for p in player_round_stats:
        player_table['rounds'] += 1
        if p['rank'] == 1:
            player_table['round_wins'] += 1

    # sort round stats by date
    player_round_stats = sorted(player_round_stats, key=lambda i: i['date'], reverse=True)

    # getting teams table
    all_teams_table = get_team_stats(all_games)
    teams_table = []
    for row in all_teams_table:
        for t in teams:
            if row['name'] == t.teamname:
                teams_table.append(row)

    return render_template('player.html', player=player, player_table=player_table,
                           player_round_stats=player_round_stats, player_games=player_games,
                           teams_table=teams_table)


@app.route('/team/<teamid>')
def team(teamid):
    team = Team.query.filter_by(id=teamid).first_or_404()
    games = Game.query.all()
    team_games = Game.query.filter(or_(Game.team1_id == teamid, Game.team2_id == teamid)).order_by(Game.date.desc())

    all_teams_stats = get_team_stats(games)
    # filter out correct team
    team_stats = next(item for item in all_teams_stats if item['name'] == team.teamname)
    # set number of active teams
    team_stats['teams'] = len(all_teams_stats)

    # get all dates a team has played
    dates = {}
    for g in team_games:
        dates[g.date] = g.date

    # for each date return the stats table and only store relevant team stats
    team_round_stats = []
    for d in dates:
        round_games = Game.query.filter_by(date=d).all()
        all_teams_stats = get_team_stats(round_games)
        team_round_stats.append(next(item for item in all_teams_stats if item['name'] == team.teamname))
        team_round_stats[-1]['date'] = d
        team_round_stats[-1]['teams'] = len(all_teams_stats)

    return render_template('team.html', team=team, team_stats=team_stats,
                           team_games=team_games, team_round_stats=team_round_stats)


@app.route('/teams')
def teams():
    games = Game.query.all()
    team_stats = get_team_stats(games)
    chart = ColumnChart('teams', options={'legend': 'none', 'isStacked': 'percent', 'height': '400',
                                          'series': 'color: green'})
    chart.add_column('string', 'Team')
    chart.add_column('number', 'Wins')
    chart.add_column('number', 'Losses')

    for t in team_stats:
        chart.add_rows([[t['name'], t['w'], t['l']]])

    charts.register(chart)
    return render_template('teams.html', teams=teams, team_stats=team_stats)

@app.route('/rounds')
def rounds():
    players = Player.query.all()
    game_dates = db.session.query(Game.date).order_by(Game.date.desc()).distinct()
    round_stats = {}
    for g in game_dates:
        games = Game.query.filter_by(date=g.date).all()
        round_stats[str(g.date)] = len(games)
    return render_template('rounds.html', table=round_stats, players=players)

@app.route('/round/<round_date>')
def round(round_date):
    games = Game.query.filter_by(date=round_date).first_or_404()
    round_games = Game.query.filter_by(date=round_date).all()
    player_round_stats = get_players_stats(round_games)
    team_round_stats = get_team_stats(round_games)
    return render_template('round.html', round_games=round_games,
                           player_round_stats=player_round_stats, games=games, team_round_stats=team_round_stats)

def get_players_stats(games):
    players_stats = []
    active_players = get_active_players(games)

    # Creating structure of list of dictionaries
    for k, v in active_players.items():
        players_stats.append({'name': v, 'rank': 0, 'pld': 0, 'w': 0, 'l': 0, 'wr': 0.0})

    # Adding wins and losses to dictionary
    for g in games:
        for p in players_stats:
            if p['name'] == g.winner.player1.firstname or p['name'] == g.winner.player2.firstname:
                p['w'] += 1
            elif p['name'] == g.loser.player1.firstname or p['name'] == g.loser.player2.firstname:
                p['l'] += 1

    # Adding totals and win ratio to dictionary
    for p in players_stats:
        p['pld'] = p['w'] + p['l']
        if p['pld'] > 0:
            p['wr'] = float(p['w']) / float(p['pld'])

    # Sorting list of dictionary
    players_stats = sorted(players_stats, key=lambda i: i['wr'], reverse=True)

    # Adding rank
    i = 0
    rank = 1
    for p in players_stats:
        if i > 0 and p['wr'] == players_stats[i-1]['wr']:
            p['rank'] = rank - 1
        else:
            p['rank'] = rank

        i += 1
        rank += 1

    return players_stats


def get_team_stats(games):
    team_stats = []
    active_teams = get_active_teams(games)

    # Creating structure of list of dictionaries
    for k, v in active_teams.items():
        team_stats.append({'id': k, 'name': v, 'rank': 0, 'pld': 0, 'w': 0, 'l': 0, 'wr': 0.0})

    # Adding wins and losses to dictionary
    for g in games:
        for t in team_stats:
            if t['name'] == g.winner.teamname:
                t['w'] += 1
            elif t['name'] == g.loser.teamname:
                t['l'] += 1

    # Adding totals and win ratio to dictionary
    for t in team_stats:
        t['pld'] = t['w'] + t['l']
        t['wr'] = float(t['w']) / float(t['pld'])

    # Sorting list of dictionary
    team_stats = sorted(team_stats, key=lambda i: i['wr'], reverse=True)

    # Adding rank
    rank = 1
    for t in team_stats:
        t['rank'] = rank
        rank += 1

    return team_stats


def get_active_teams(games):
    active_teams = {}
    for g in games:
        active_teams[g.winner.id] = g.winner.teamname
        active_teams[g.loser.id] = g.loser.teamname
    return active_teams


def get_active_players(games):
    active_players = {}
    for g in games:
        active_players[g.winner.player1.id] = g.winner.player1.firstname
        active_players[g.winner.player2.id] = g.winner.player2.firstname
        active_players[g.loser.player1.id] = g.loser.player1.firstname
        active_players[g.loser.player2.id] = g.loser.player2.firstname
    return active_players




@app.route('/games')
def games():
    game_dates = db.session.query(Game.date).distinct().count()
    games_played = db.session.query(Game).count()
    games = Game.query.all()

    chart = ColumnChart("games", options={'legend': 'none'})
    chart.add_column("string", "Date")
    chart.add_column("number", "Games")
    chart.add_rows([["2019-05-17", games_played]])
    charts.register(chart)

    return render_template('games.html', title="Home", games=games, game_dates=game_dates, games_played=games_played)


# Updated and Delete Game
@app.route('/game/<gameid>', methods=['GET', 'POST'])
def game(gameid):
    game = Game.query.filter_by(id=gameid).first_or_404()
    form = EditGameForm()

    teams = Team.query.order_by(Team.teamname).all()
    teams_list = [(t.id, t.teamname) for t in teams]
    form.team1.choices = teams_list
    form.team2.choices = teams_list

    if form.validate_on_submit():
        if 'submit' in request.form:
            game.date = form.date.data
            game.team1_id = form.team1.data
            game.team2_id = form.team2.data
            game.score_team1 = form.score_team1.data
            game.score_team2 = form.score_team2.data
            if game.score_team1 > game.score_team2:
                game.winner = game.team1
                game.loser = game.team2
            else:
                game.winner = game.team2
                game.loser = game.team1

            db.session.commit()
            flash('Game UPDATED! Your changes have been saved.')
            return redirect(url_for('games'))

        elif 'delete' in request.form:
            db.session.delete(game)
            db.session.commit()
            flash('Game DELETED! Your changes have been saved.')
            return redirect(url_for('games'))

        elif 'cancel' in request.form:
            flash('CANCELLED! Your changes have not been saved!')
            return redirect(url_for('games'))

    elif request.method == 'GET':
        form.date.data = game.date
        form.team1.data = game.team1_id
        form.team2.data = game.team2_id
        form.score_team1.data = game.score_team1
        form.score_team2.data = game.score_team2

    return render_template('game.html', game=game, form=form)


@app.route('/uploadplayers', methods=['GET', 'POST'])
def uploadplayers():
    form = UploadPlayersForm()
    if request.method == 'POST' and 'submit' in request.form:
        players = []
        file = form.file.data
        file = TextIOWrapper(file, encoding='utf-8')
        csv_reader = csv.reader(file, delimiter=';')
        next(csv_reader, None)
        for row in csv_reader:
            player = Player(firstname=row[0], lastname=row[1])
            db.session.add(player)
            db.session.commit()
            players.append(row[0] + ' ' + row[1])

            # If more than 2 players automatically create teams for the newly added player
            if len(Player.query.all()) > 1:
                latest_player = Player.query.order_by(Player.id.desc()).first()
                all_players = Player.query.all()
                created_teams = create_teams(latest_player.id, all_players)

        flash(prepare_flash_message("Players added to the database:", players))
        return redirect(url_for('uploadplayers'))

    # If save-button is clicked export all players
    elif request.method == 'POST' and 'save' in request.form:
        exportplayers()
        flash('Database of players has been saved to file')
        return redirect(url_for('uploadplayers'))

    # Delete all players if delete button is clicked
    elif request.method == 'POST' and 'delete' in request.form:
        delete_teams()
        delete_players()
        flash('All players and teams were deleted')

        return redirect(url_for('uploadplayers'))

    return render_template('uploadplayers.html', form=form)


# Export all players from the database
def exportplayers():
    with open('exports/players.csv', 'w') as csvfile:
        all_players = Player.query.all()
        filewriter = csv.writer(csvfile, delimiter=';',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow(['Firstname', 'Lastname'])
        for p in all_players:
            filewriter.writerow([p.firstname, p.lastname])


@app.route('/uploadgames', methods=['POST', 'GET'])
def uploadgames():
    form = UploadGamesForm()
    if request.method == 'POST' and 'submit' in request.form:
        games_string = []
        team_initials = get_team_initials()
        file = form.file.data
        file = TextIOWrapper(file, encoding='utf-8')
        csv_reader = csv.reader(file, delimiter=';')
        next(csv_reader, None)
        for row in csv_reader:
            date = datetime.date(datetime.strptime(row[0], "%Y-%m-%d"))
            team1_id = team_initials[row[1]]
            team2_id = team_initials[row[2]]
            score_team1 = int(row[3])
            score_team2 = int(row[4])
            if score_team1 > score_team2:
                winner_team_id = team1_id
                loser_team_id = team2_id
            else:
                winner_team_id = team2_id
                loser_team_id = team1_id
            game = Game(date=date, team1_id=team1_id, team2_id=team2_id, score_team1=score_team1,
                        score_team2=score_team2, winner_team_id=winner_team_id,
                        loser_team_id=loser_team_id)
            db.session.add(game)
            db.session.commit()

            # friendly names
            team1 = Team.query.get(team1_id)
            team2 = Team.query.get(team2_id)
            games_string.append(team1.teamname + ' vs. ' + team2.teamname + ': ' + row[3] + '-' + row[4])

        flash(prepare_flash_message("Games added to the database:", games_string))

        return redirect(url_for('uploadgames'))

    elif request.method == 'POST' and 'save' in request.form:
        with open('exports/games.csv', 'w') as csvfile:
            all_games = Game.query.all()
            filewriter = csv.writer(csvfile, delimiter=';',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            filewriter.writerow(['Date', 'Team 1', 'Team 2',
                                 'Score Team 1', 'Score Team 2'])
            for g in all_games:
                team1 = Team.query.get(g.team1_id)
                team1_initials = team1.player1.firstname[:2] + team1.player2.firstname[:2]
                team2 = Team.query.get(g.team2_id)
                team2_initials = team2.player1.firstname[:2] + team2.player2.firstname[:2]
                filewriter.writerow([g.date, team1_initials, team2_initials,
                                     g.score_team1, g.score_team2])

        flash('Database of players has been saved to file')
        return redirect(url_for('uploadgames'))

    elif request.method == 'POST' and 'delete' in request.form:
        all_games = Game.query.all()
        with open('exports/games.csv', 'w') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=';',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            filewriter.writerow(['Date', 'Team 1 ID', 'Team 2 ID',
                                 'Score Team 1', 'Score Team 2'])
            for g in all_games:
                team1 = Team.query.get(g.team1_id)
                team1_initials = team1.player1.firstname[:2] + team1.player2.firstname[:2]
                team2 = Team.query.get(g.team2_id)
                team2_initials = team2.player1.firstname[:2] + team2.player2.firstname[:2]
                filewriter.writerow([g.date, team1_initials, team2_initials,
                                     g.score_team1, g.score_team2])
        i = 0
        for game in all_games:
            db.session.delete(game)
            i += 1
        db.session.commit()
        flash(str(i) + ' games deleted from the database. A CSV-file with all games was saved!')
        return redirect(url_for('uploadgames'))

    return render_template('uploadgames.html', form=form)


def get_team_initials():
    all_teams = Team.query.all()
    team_list = {}
    initial = ""
    for t in all_teams:
        initial = t.player1.firstname[0] + t.player2.firstname[0]
        team_list[initial] = t.id
        initial = t.player2.firstname[0] + t.player1.firstname[0]
        team_list[initial] = t.id
        initial = t.player1.firstname[:2] + t.player2.firstname[:2]
        team_list[initial] = t.id
        initial = t.player2.firstname[:2] + t.player1.firstname[:2]
        team_list[initial] = t.id
    return team_list


def prepare_flash_message(start, middle):
    # Flash message
    string1 = "<p>" + start + "</p><ol>"
    string2 = ''
    string3 = "</ol>"
    for m in middle:
        string2 = string2 + "<li>" + m + "</li>"
    complete_str = string1 + string2 + string3
    flash_string = Markup(complete_str)

    return flash_string











# JUST FOR TESTING
@app.route('/chart')
def chart():
    players = Player.query.all()
    games = Game.query.all()
    unique_dates = []
    for g in games:
        if g.date not in unique_dates:
            unique_dates.append(g.date)
    my_chart = ColumnChart("dfs")
    my_chart.add_column("string", "Competitor")
    my_chart.add_column("number", "Hot Dogs")
    my_chart.add_rows([["Matthew Stonie", 62],
                            ["Joey Chestnut", 60],
                            ["Eater X", 35.5],
                            ["Erik Denmark", 33],
                            ["Adrian Morgan", 31]])
    charts.register(my_chart)

    return render_template('chart.html', players=players, games=games, unique_dates=unique_dates)