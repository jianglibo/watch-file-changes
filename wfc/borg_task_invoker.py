import os
from typing import Union

from . import common_util

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


class BorgTaskInvoker():
    """Do borg tasks."""

    def __init__(self, config_file_path: Union[Path, str]):
        self.c = common_util.get_configuration_yml(config_file_path)
        self.borg_bin = self.c.dict_like['BorgBin']
        self.repo_path = self.c.dict_like['BorgRepoPath']

    def main(self, action, args_ary):
        if action == 'Archive':
            self.send_to_client(self.new_borg_archive())
        elif action == 'Prune':
            self.send_to_client(self.invoke_prune())
        elif action == 'InitializeRepo':
            self.send_to_client(self.init_borg_repo())
        elif action == 'DownloadPublicKey':
            self.send_to_client(self.get_openssl_publickey())
        elif action == 'Install':
            self.send_to_client(self.install_borg())
        else:
            common_util.common_action_handler(action, args_ary)

    def send_to_client(self, content):
        common_util.send_lines_to_client(content)

    def get_openssl_publickey(self):
        openssl_exec = self.c.dict_like["openssl"]
        private_key_file = self.c.dict_like["ServerPrivateKeyFile"]
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            subprocess.call([openssl_exec, 'rsa', '-in',
                             private_key_file, '-pubout', '-out', tf.name])
            return tf.name

    def install_borg(self):
        if os.path.exists(self.borg_bin):
            common_util.send_lines_to_client("AlreadyInstalled")
        else:
            common_util.get_software_packages(self.c.package_dir,
                                              self.c.softwares)
            pk = common_util.get_software_package_path(
                self.c.package_dir, self.c.softwares)
            shutil.copy(pk, self.borg_bin)
            subprocess.call(['chmod', '755', self.borg_bin])
            common_util.send_lines_to_client("Install Success.")

    def new_borg_archive(self):
        bout = subprocess.check_output(
            [self.borg_bin, 'list', '--json', self.repo_path])
        result_json = json.loads(bout)
        archives = result_json['archives']
        if archives:
            archive_name = str(int(archives[-1]['name']) + 1)
        else:
            archive_name = "1"
        create_cmd = self.c.dict_like['BorgCreate'] % (
            self.borg_bin, self.repo_path, archive_name)
        return subprocess.check_output(create_cmd, shell=True)

    def invoke_prune(self):
        prune_cmd = self.c.dict_like['BorgPrune'] % (
            self.borg_bin, self.repo_path)
        subprocess.check_output(prune_cmd, shell=True)
        list_cmd = self.c.dict_like['BorgList'] % (
            self.borg_bin, self.repo_path)
        return subprocess.check_output(list_cmd, shell=True)

    def init_borg_repo(self):
        # init_cmd = [borg_bin, 'init', '--encryption=none', repo_path]
        borg_init = self.c.dict_like['BorgInit']
        init_cmd = borg_init % (self.borg_bin, self.repo_path)
        init_cmd = init_cmd.split()
        try:
            out_put = subprocess.check_output(init_cmd, stderr=subprocess.STDOUT)
            return out_put
        except subprocess.CalledProcessError as cpe:
            return "%s, %s, %s, %s, %s" % (
                cpe.cmd, cpe.returncode, cpe.output, cpe.stdout, cpe.stderr)
