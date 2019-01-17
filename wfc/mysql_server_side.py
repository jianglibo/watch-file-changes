#!/usr/bin/python

import getopt
import sys
import logging
from pathlib import Path

pr = str(Path(__file__).parent.parent.resolve())
sys.path.append(pr)

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

        file_name = "mysql_configuration.yml"
        project_root = Path(__file__).parent.parent
        config_path = project_root.parent.joinpath(file_name)

        if not config_path.exists():
            config_path = project_root.joinpath('wfc', file_name)
        processor = MysqlTaskInvoker(config_path)
        processor.do_action(action_opt, args)
    except Exception as e:  # pylint: disable=W0703
        logging.error(e, exc_info=True)
    finally:
        pass
