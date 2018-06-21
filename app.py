import tornado.web, tornado.ioloop
import ui
import os


class HomePage(tornado.web.RequestHandler):
    """Landing page handler"""

    def get(self):
        self.render('index.html')


class CreateCard(tornado.web.RequestHandler):
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
        (r"/create_card.html", CreateCard)
    ], **settings)

    application.listen(int(os.environ.get('PORT', 5000)))

    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__": main()
