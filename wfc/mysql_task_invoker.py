import io
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Union

from wfc import common_util
from wfc.global_static import PyGlobal


class MysqlTaskInvoker():
    """Do mysql tasks.
    """

    def __init__(self, config_file_path: Union[Path, str]):
        self.c = common_util.get_configuration_yml(config_file_path)
        self.client_bin = self.c.dict_like['ClientBin']
        self.password = self.c.dict_like['MysqlPassword']
        self.user = self.c.dict_like['MysqlUser']
        self.mysql_admin = self.c.dict_like['MysqlAdminBin']

    def do_action(self, action: str, args_ary: List[str]):
        if action == 'FlushLogs':
            common_util.send_lines_to_client(self.invoke_mysql_flushlogs())
        elif action == 'Dump':
            common_util.send_lines_to_client(self.invoke_mysql_dump())
        elif action == 'GetMycnf':
            common_util.send_lines_to_client(self.get_mycnf_file())
        elif action == 'DownloadPublicKey':
            common_util.send_lines_to_client(self.get_openssl_publickey())
        elif action == 'FlushLogFileHash':
            common_util.send_lines_to_client(self.flushlogs_filehash())
        elif action == 'GetVariables':
            common_util.send_lines_to_client(
                self.get_mysql_variables(args_ary))
        else:
            common_util.common_action_handler(action, args_ary)

    def get_openssl_publickey(self):
        openssl_exec = self.c.dict_like["openssl"]
        private_key_file = self.c.dict_like["ServerPrivateKeyFile"]
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            subprocess.call([openssl_exec, 'rsa', '-in',
                             private_key_file, '-pubout', '-out', tf.name])
            return tf.name

    def get_enabled_version(self, lines):
        founded = []
        current_version = None
        for line in lines:
            line = line.strip()
            m = re.match(r'^\[.*?(\d+)-.*\]$', line)
            if m:
                current_version = m.group(1)
            else:
                if line == 'enabled=1' and current_version:
                    founded.append(current_version)
                    current_version = None
        return founded

    def enable_repoversion(self, repo_file, version):
        common_util.backup_localdirectory(repo_file)
        lines = self._enable_repoversion(repo_file, version)
        with io.open(repo_file, 'wb') as opened_file:
            opened_file.writelines(["%s%s" % (line, "\n") for line in lines])

    def _enable_repoversion(self, repo_file, version):
        current_version = None
        with io.open(repo_file, mode='r') as opened_file:
            lines = [line.strip() for line in opened_file.readlines()]
            new_lines = []
        for line in lines:
            m = re.match(r'^\[.*?(\d+)-.*\]$', line)
            if m:
                current_version = m.group(1)
            else:
                m = re.match(r'^\[.*\]$', line)
                if m:
                    current_version = 'others'
                else:
                    m = re.match('^enabled=(0|1)$', line)
                    if m:
                        if current_version == version:
                            line = 'enabled=1'
                        elif current_version != 'others':
                            line = 'enabled=0'
            new_lines.append(line)
        return new_lines

    def invoke_mysql_sql_command(self, sql):  # pylint: disable=W0613
        cmd_array = [
            self.client_bin,
            "-u%s" % self.user,
            "-p%s" % self.password,
            "-X",
            "-e",
            sql
        ]
        return common_util.subprocess_checkout_print_error(cmd_array)

    def get_mysql_variables(self, variable_names=None, plain_password=None):  # pylint: disable=W0613
        result = self.invoke_mysql_sql_command('show variables')
        # result may start with some warning words.
        angle_idx = result.index('<')
        if angle_idx > 0:
            result = result[angle_idx:]
        rows = [(x[0].text, x[1].text) for x in ET.fromstring(
            result)]  # tuple (auto_increment_increment, 1)
        if not variable_names:
            return rows
        if isinstance(variable_names, str):
            result = filter(lambda x: x[0] == variable_names, rows)
            if result:
                return {'name': result[0][0], 'value': result[0][1]}
        else:
            result = filter(lambda x: x[0] in variable_names, rows)
            result = map(lambda t: {'name': t[0], 'value': t[1]}, result)
            return result

    def flushlogs_filehash(self):
        idx_file = self.get_mysql_variables('log_bin_index')['value']
        parent = os.path.split(idx_file)[0]
        with io.open(idx_file, 'rb') as opened_file:
            lines = opened_file.readlines()
            lines = [line.strip() for line in lines]

            def to_file_desc(relative_file):
                ff = os.path.join(parent, relative_file)
                return common_util.get_one_filehash(ff)
            return map(to_file_desc, lines)

    def invoke_mysql_flushlogs(self):
        flush_cmd = [
            self.mysql_admin,
            "-u%s" % self.user,
            "-p%s" % self.password,
            "flush-logs"
        ]
        return_code = subprocess.call(flush_cmd)
        if PyGlobal.verbose:
            print("invoke_mysql_flushlogs subprocess call return %s" % return_code)
        return self.flushlogs_filehash()

    def invoke_mysql_dump(self):
        dumpfile = self.c.dict_like['DumpFilename']
        dump_cmd = [self.c.dict_like['DumpBin'],
                    "-u%s" % self.user,
                    "-p%s" % self.password,
                    '--max_allowed_packet=512M',
                    '--quick',
                    '--events',
                    '--all-databases',
                    '--flush-logs',
                    '--delete-master-logs',
                    '--single-transaction']
        with io.open(dumpfile, 'wb') as opened_file:
            subprocess.call(dump_cmd, stdout=opened_file)

        return common_util.get_one_filehash(dumpfile)

    def enable_logbin(self, mycnf_file, logbin_base_name='hm-log-bin', server_id='1'):
        common_util.backup_localdirectory(mycnf_file)
        with io.open(mycnf_file, 'r') as opened_file:
            lines = [line.strip() for line in opened_file.readlines()]
            lines = common_util.update_block_config_file(
                lines, 'log-bin', logbin_base_name)
            lines = common_util.update_block_config_file(
                lines, 'server-id', server_id)

        with io.open(mycnf_file, 'wb') as opened_file:
            opened_file.writelines(["%s%s" % (line, "\n") for line in lines])

    def get_mycnf_file(self):
        out = subprocess.check_output([self.client_bin, '--help'])
        sio = io.StringIO(out)
        line = sio.readline()
        found = False
        result = None
        while line:
            line = line.strip()
            if found:
                result = line
                break
            if "Default options are read from the following files in the given order:" in line:
                found = True
            line = sio.readline()
        sio.close()
        results = result.split()
        for r in results:
            if os.path.exists(r):
                return r
