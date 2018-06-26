import tornado.web, tornado.ioloop
import ui
import os
import sqlite3 as sql
import logging
import re
import string

# Logger set up
log_level = os.environ.get('LOG_LEVEL', 'DEBUG')
log_level = getattr(logging, log_level.upper(), 10)
logging.basicConfig(
    filename='main_log.log',
    level=log_level,
    format='%(asctime)s:%(levelname)s:%(funcName)s:%(lineno)d:%(message)s',
    datefmt='%m/%d/%Y %I:%M:%S'
)
# Making my life easier
log = logging.log
debug = logging.DEBUG
info = logging.INFO
warning = logging.WARNING
error = logging.ERROR
log(info, 'Initializing logger')


class BaseHandler(tornado.web.RequestHandler):
    def sign_up(self, username, password):
        disallowed = filter(lambda x: x not in ['-', '_'], list(string.punctuation))
        valid_username = True
        valid_password = True

        conn = sql.connect('cards.db')
        cur = conn.cursor()
        log(debug, 'DB connected!')
        cur.executescript(
            """
            create table if not exists users (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                username TEXT UNIQUE,
                password TEXT UNIQUE
            );
            """
        )
        conn.commit()

        # validate username
        cur.execute('select username from users where username = ?', (username,))

        conditions = [
            not all(map(lambda x: x not in disallowed, list(username))),
            cur.fetchone() is not None
        ]
        log(debug, conditions)
        if any(conditions):
            valid_username = False

        # validate password
        conditions = [
            not all(map(lambda x: x not in disallowed, list(password))),
            len(password) < 8
        ]
        log(debug, conditions)
        if any(conditions):
            valid_password = False

        if valid_password and valid_username:
            cur.execute('insert into users (username, password) values (?, ?)', (username, password))
            conn.commit()
            conn.close()
            self.render('index.html')
        else:
            self.write('Uh Oh! Username: %s|| Password: %s' % (username, password))


class SignUp(BaseHandler):
    """Sign up handler"""

    def post(self):
        self.sign_up(
            self.get_body_argument('username'),
            self.get_body_argument('password')
        )


class HomePage(BaseHandler):
    """Landing page handler"""

    def get(self):
        self.render('index.html')


class CreateCard(BaseHandler):
    """Create card page handler"""

    def get(self):
        self.render("create_card.html")


def main():
    settings = dict(
        ui_modules=ui,
        cookie_secret=str(os.urandom(45)),
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        xsrf_cookies=True,
        autoreload=True,
        gzip=True,
        debug=True,
        autoescape=None
    )

    application = tornado.web.Application([
        (r"/", HomePage),
        (r"/create_card.html", CreateCard),
        (r"/sign_up", SignUp)
    ], **settings)

    application.listen(int(os.environ.get('PORT', 5000)))

    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__": main()
