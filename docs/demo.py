import begin
import funconf

config = funconf.Config('my.conf')

@begin.subcommand
@config.foo
def foo(**k):
    """This is the foo code"""
    print("Foo got %s" % k)
    print("Config is:")
    print(config)

@begin.subcommand
@config.bread
def bread(**k):
    """This is the bread code"""
    print("Bread got %s" % k)
    print("Config is:")
    print(config)

@begin.subcommand
@config
def run(**k):
    """This is the run command that controls all"""
    print("Run got %s" % k)
    print("Config is:")
    print(config)

@begin.start
def entry():
    pass

