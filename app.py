import spotipy
import json
import time
from flask import Flask, request, redirect, url_for, session, render_template

app = Flask(__name__)

# secret_key is required for sessions. This is a random string.
# The app.json file contains the app_secret, client_id and client_secret.
app.secret_key = json.loads(open('app.json').read())['app_secret']
app.config['SESSION_COOKIE_NAME'] = 'spotify_session'


# This is the start page that redirect us to the spotify login page.
@app.route('/', methods=['GET', 'POST'])
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    print(auth_url)
    return redirect(auth_url)


@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')


# This is the page that we get redirected to after the spotify login.
@app.route('/authorize')
def authorize():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect("/index")


# This is the main page that takes some input from the user and redirects according to them.
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        term = request.form.get('term')
        if request.form.get('get_top_tracks') == 'Top Tracks':
            return redirect(url_for('top_tracks', term=term))
        elif request.form.get('get_top_artists') == 'Top Artists':
            return redirect(url_for('top_artists', term=term))
    else:
        return render_template('/index.html')


# This is the page that shows the top tracks of the user.
@app.route('/top_tracks', methods=['GET', 'POST'])
def top_tracks():
    if request.method == 'POST':
        if request.form.get("back") == "Back":
            return redirect(url_for('index'))
    else:
        session['token_info'], authorized = get_token()
        session.modified = True

        # We are controlling the user if he is authorized or not.
        if not authorized:
            return redirect('/')

        # We are getting the top tracks of the user according to their input.
        time_range = request.args.get('term')
        sp = spotipy.Spotify(auth=session['token_info']['access_token'])
        list = sp.current_user_top_tracks(
            limit=50, offset=0, time_range=time_range)['items']

        result = []
        for i in range(50):
            if i == len(list):
                break
            result.append(str(i+1) + '. ' +
                          list[i]['name'] + ' - ' + list[i]['artists'][0]['name'])
        return render_template('/list.html', list=result)


# This is the page that shows the top artists of the user.
@app.route('/top_artists', methods=['GET', 'POST'])
def top_artists():
    if request.method == 'POST':
        if request.form.get("back") == "Back":
            return redirect(url_for('index'))
    else:
        session['token_info'], authorized = get_token()
        session.modified = True

        if not authorized:
            return redirect('/')

        time_range = request.args.get('term')
        sp = spotipy.Spotify(auth=session['token_info']['access_token'])
        list = sp.current_user_top_artists(
            limit=50, offset=0, time_range=time_range)['items']

        result = []
        for i in range(50):
            if i == len(list):
                break
            result.append(str(i+1) + '. ' + list[i]['name'])
        return render_template('/list.html', list=result)


# This is the function that we use to get the token and validity of that token.
def get_token():
    token_valid = False
    token_info = session.get('token_info', {})

    if not session.get('token_info', False):
        token_valid = False
        return token_info, token_valid

    now = int(time.time())
    is_token_expired = session.get(
        'token_info').get('expires_at', 0) - now < 60

    if is_token_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(
            session.get('token_info').get('refresh_token'))

    token_valid = True
    return token_info, token_valid


# This is the function that we use to create the spotify oauth object.
def create_spotify_oauth():
    sp_oauth = spotipy.oauth2.SpotifyOAuth(
        client_id=json.loads(open('app.json').read())['client_id'],
        client_secret=json.loads(open('app.json').read())['client_secret'],
        redirect_uri=url_for('authorize', _external=True),
        scope='user-top-read',
    )
    return sp_oauth
