import begin
import funconf

config = funconf.Config('demo.conf')

@begin.subcommand
@config.foo
def foo(*a, **k):
    "This is the foo code"
    print("Foo got a=%s k=%s" % (a, k))
    print("Config is:")
    print(config)

@begin.subcommand
@config.bread
def bread(*a, **k):
    "This is the bread code"
    print("Bread got a=%s k=%s" % (a, k))
    print("Config is:")
    print(config)

@begin.subcommand
@config
def run(*a, **k):
    "This is the run command that controls all"
    print("Run got a=%s k=%s" % (a, k))
    print("Config is:")
    print(config)

@begin.start
def entry():
    "This is a super dooper program..."
    pass

