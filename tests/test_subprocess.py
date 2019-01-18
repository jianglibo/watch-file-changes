import subprocess
import os


class TestSubprocesses:
    def test_shell_true(self):
        cp = subprocess.run(['echo', '%HOME%'], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=True)
        assert cp.returncode == 0
        assert isinstance(cp.stdout, bytes)
        cp = subprocess.run(['echo', '%HOME%'], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=True, universal_newlines=True)
        assert isinstance(cp.stdout, str)
        assert 'HOME' in cp.stdout

        new_env = {
            **os.environ
        }

        try:
            cp = subprocess.run(['dir', '%HOME%'], stdout=subprocess.PIPE, env=new_env,
                                stderr=subprocess.PIPE, check=True, universal_newlines=True, shell=True)
        except subprocess.CalledProcessError as err:
            print(err)

        assert 'HOME' not in cp.stdout
