from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from database import init_db, get_db
from auth import bp as auth_bp
from game import bp as game_bp

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',  # Change this to a random value in production
        DATABASE=os.path.join(app.instance_path, 'game.db'),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize the database
    init_db(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)

    # Home page route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Game route
    @app.route('/game')
    def game_redirect():
        return redirect(url_for('game.game'))

    # Leaderboard route
    @app.route('/leaderboard')
    def leaderboard():
        db = get_db()
        leaders = db.execute(
            'SELECT username, high_score FROM users ORDER BY high_score DESC LIMIT 10'
        ).fetchall()
        return render_template('leaderboard.html', leaders=leaders)

    return app

if __name__ == '__main__':
    app = create_app()
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))