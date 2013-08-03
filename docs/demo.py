import begin
import funconf


config = funconf.Config('my.conf')


@begin.subcommand
@config.foo.wraps
def foo(**k):
    """This is the foo code"""
    print(k)


@begin.subcommand
@config.bread.wraps
def bread(**k):
    """This is the bread code"""
    print(k)


@begin.start
@config.wraps
def main(**k):
    """teeeehiii"""
    print(k)


