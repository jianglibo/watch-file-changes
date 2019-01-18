import subprocess
import os
import sys
import pytest


class TestSubprocesses:

    def test_shell_false(self):
        # because echo is a builtin command. If invoke directly as executable, it will fail.
        with pytest.raises(FileNotFoundError):
            if 'nux' in sys.platform:
                cmd_ary = ['alias', 'lsls=ls']
            else:
                cmd_ary = ['echo', '%path%']
            subprocess.run(cmd_ary,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           check=True)

    def test_shell_true(self):
        if 'nux' in sys.platform:
            cmd_ary = ['alias', 'lsls=ls']
        else:
            cmd_ary = ['echo', '%path%']
        cp = subprocess.run(cmd_ary,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=True,
                            shell=True)
        assert cp.returncode == 0
        # universal_newlines wasn't setted.
        assert isinstance(cp.stdout, bytes)

        cp = subprocess.run(['echo', '%path%'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=True,
                            shell=True,
                            universal_newlines=True)
        assert isinstance(cp.stdout, str)
    
    def test_var_expand(self):
        new_env = {
            **os.environ,
            "HOME_T": "E:"
        }

        if 'nux' in sys.platform:
            var_name = '$HOME_T'
        else:
            var_name = '%HOME_T%'

        assert new_env['HOME_T'] == 'E:'

        # under linux box, if shell=True, will cause echo output empty string.
        # expand environment variables depend on shell is not a good idea.
        cp = subprocess.run(['echo', var_name],
                            stdout=subprocess.PIPE,
                            env=new_env,
                            stderr=subprocess.PIPE,
                            check=True,
                            shell=True,
                            universal_newlines=True)

        assert 'E:' == cp.stdout.strip()
