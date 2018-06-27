from collections import namedtuple
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

index_vars = {
    'errors': None,
    'overlay': 'none',
    'username_taken': False,
    'invalid_uname_or_pass': False
}


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        User = namedtuple('User', 'id, username, password')
        if not self.get_secure_cookie('site_user'):
            return None
        else:
            conn = sql.connect('cards.db')
            cur = conn.cursor()
            cur.execute('select * from users where id = ?', (self.get_secure_cookie('site_user'),))
            user = User(*cur.fetchone())
            conn.close()
            return user

    def sign_up(self, username, password):
        """Sign up routines.
        :returns True if sign up was successful else returns index_vars dict
        """
        disallowed = filter(lambda x: x not in ['-', '_'], list(string.punctuation))
        disallowed.append(' ')
        valid_username = True
        valid_password = True
        log(debug, 'Index vars: %s' % index_vars)
        d = index_vars
        log(debug, 'The sign up dict: %s' % d)
        conn = sql.connect('cards.db')
        cur = conn.cursor()
        # log(debug, 'DB connected!')
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

        username_conditions = [
            not all(map(lambda x: x not in disallowed, list(username))),
            cur.fetchone() is not None
        ]
        # log(debug, conditions)
        if any(username_conditions):
            valid_username = False

        # validate password
        password_conditions = [
            not all(map(lambda x: x not in disallowed, list(password))),
            len(password) < 8
            # TODO add check if both password values are equal
        ]
        # log(debug, conditions)
        if any(password_conditions):
            valid_password = False

        if valid_password and valid_username:
            cur.execute('insert into users (username, password) values (?, ?)', (username, password))
            conn.commit()
            id = cur.execute('select id from users where username = ?', (username, )).fetchone()
            conn.close()
            self.set_secure_cookie('site_user', str(id))
            log(info, 'Successfully signed Up user: %s' % username)
            return True
        else:
            log(info, 'Failed to sign up user: %s' % username)
            log(info, 'Valid username: %s || Valid pass: %s' % (valid_username, valid_password))
            d['errors'] = []
            # Specify error
            d['overlay'] = 'block'  # Inform template to persist sign up overlay
            if username_conditions[1]:  # username already exists
                d['username_taken'] = True
            elif username_conditions[0]:   # username contained illegal characters
                d['errors'].append('username')

            if not valid_password:
                d['errors'].append('password')

            return d

    def login(self, username, password):
        """
        Attempt to login a user by checking submitted credentials against database.
        :param username: Username entered by user
        :param password: Password entered by user
        :return: True on success | index dict on false
        """
        conn = sql.connect('cards.db')
        cur = conn.cursor()
        cur.execute('select * from users where username = ? and password = ?', (username, password,))
        res = cur.fetchone()

        if res:
            self.set_secure_cookie('site_user', str(res[0]))
            log(info, 'Successful login for user: %s' % res[1])
            return True
        else:
            d = dict()
            d.update(index_vars)
            d['invalid_uname_or_pass'] = True
            return d


class HomePage(BaseHandler):
    """Landing page handler"""

    def get(self):
        self.render('index.html', **index_vars)

    def post(self):
        auth = self.login(self.get_body_argument('username'), self.get_body_argument('password'))
        if auth is True:
            self.redirect(self.get_argument('next', '/dashboard'))
        else:
            log(debug, auth)
            self.render('index.html', **auth)


class Dashboard(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('start.html', username=self.current_user.username)


class SignUp(BaseHandler):
    """Sign up handler"""

    def post(self):
        auth = self.sign_up(self.get_body_argument('username'), self.get_body_argument('password'))
        if auth is True:
            self.redirect(self.get_argument('next', '/dashboard'))
        else:
            log(debug, auth)
            self.render('index.html', **auth)


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
        autoescape=None,
        login_url='/',
    )

    application = tornado.web.Application([
        (r"/", HomePage),
        (r"/create_card.html", CreateCard),
        (r"/sign_up", SignUp),
        (r"/dashboard", Dashboard)
    ], **settings)

    application.listen(int(os.environ.get('PORT', 5000)))

    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__": main()
