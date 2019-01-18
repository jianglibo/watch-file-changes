import subprocess
import os
import pytest


class TestSubprocesses:
    def test_shell_true(self):
        # because echoe is a built in command.
        with pytest.raises(FileNotFoundError):
            cp = subprocess.run(['echo', '%path%'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=True)

        cp = subprocess.run(['echo', '%path%'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=True,
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
        assert '%path%' not in cp.stdout

        new_env = {
            **os.environ,
            "HOME": "E:"
        }


        cp = subprocess.run(['echo', '%HOME%'],
                            stdout=subprocess.PIPE,
                            env=new_env,
                            stderr=subprocess.PIPE,
                            check=True,
                            universal_newlines=True,
                            shell=True)

        assert 'E:' == cp.stdout.strip()
