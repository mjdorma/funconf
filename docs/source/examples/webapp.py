import bottle
import begin
import funconf

@bottle.route('/hello')
def hello():
    return "Hello World!"

config = funconf.Config(['webapp.conf',
                         '~/.webapp.conf'])

@begin.start(env_prefix="WEBAPP_")
@config.web
def main(host='127.0.0.1', port=8080, debug=False):
    print(config)
    bottle.run(host=host, port=port, debug=debug)
