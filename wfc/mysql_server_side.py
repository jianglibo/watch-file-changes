#!/usr/bin/python

import getopt
import sys
from wfc.mysql_task_invoker import MysqlTaskInvoker

from wfc.global_static import PyGlobal

def usage():
    print("usage message printed.")

# "ho:" mean -h doesn't need a argument, but -o needs.

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hv:a:", ["help", "action=", "notclean", "verbose"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like "option -a not recognized"
        sys.exit(2)
    verbose = False
    clean = True
    action_opt = None
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o == '--notclean':
            clean = False
        elif o == '--verbose':
            PyGlobal.verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("--action", '-a'):
            action_opt = a
        else:
            assert False, "unhandled option"
    try:
        if action_opt is None:
            raise ValueError('no action.')
        processor = MysqlTaskInvoker("borg_configuration.yml")
        processor.do_action(action_opt, args)
    except Exception as e:  # pylint: disable=W0703
        print(type(e))
        print(e)
    finally:
        pass
