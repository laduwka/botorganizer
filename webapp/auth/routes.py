from flask import Blueprint, current_app, url_for, session, redirect, request
from webapp.db import mongo
import google_auth_oauthlib.flow

blueprint = Blueprint('auth', __name__, url_prefix='/auth')


@blueprint.route('/<userid>')
def auth(userid):
    # Create flow instance to manage
    # the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        current_app.config.get('CLIENT_CONFIG_DATA'),
        scopes=current_app.config.get('SCOPES')
        )

    # The URI created here must exactly match one of
    # the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console.
    # If this value doesn't match an authorized URI,
    # you will get a 'redirect_uri_mismatch' error.
    flow.redirect_uri = url_for('auth.oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you canflask
        # re-prompting the user for permission.flask
        # Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')
    print("STATE: ", state)
    # Store the state so the callback can verify the auth server response.
    session['state'] = state
    session['user_id'] = userid
    return redirect(authorization_url)


@blueprint.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    if 'state' in session:
        state = session['state']
        print("STATE: ", session['state'])
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        current_app.config.get('CLIENT_CONFIG_DATA'),
        scopes=current_app.config.get('SCOPES'),
        state=state
        )
    flow.redirect_uri = url_for('auth.oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in db
    credentials = flow.credentials
    mongo.db.google_credentials.insert_one(
        {
            '_id': session['user_id'],
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'default_calendar': None
        }
        )
    return redirect(url_for('main.index'))


@blueprint.route('/clear')
def clear_credentials():
    if 'credentials' in session:
        del session['credentials']
    return ('Креды удалены.<br><br>')
