
from pathlib import Path
from wfc import common_util
from wfc.global_static import Configuration
from wfc.mysql_task_invoker import MysqlTaskInvoker


def get_default_config() -> Configuration:
    return common_util.get_configuration_yml(
        Path(__file__).parent.joinpath("mysql_configuration.2.yml"))

# set password for 用户名@localhost = password('新密码');

class TestMysqlInvoker:

    # def test_escape(self):
    #     c: Configuration = get_default_config()
    #     mti: MysqlTaskInvoker = MysqlTaskInvoker(c)
    #     if 'nux' in sys.platform:
    #         pass_var = "$mysql_pass"
    #     else:
    #         # escaping special characters by surrounding double quotes.
    #         pass_var = '%mysql_pass%'
    #     new_env = {
    #         **os.environ,
    #         "mysql_pass": f'"-p{mti.password}"'
    #     }
    #     r = subprocess.run([mti.client_bin, '-uroot', pass_var, '-X', '-e', 'show variables'],
    #                        env=new_env,
    #                        stdout=subprocess.PIPE,
    #                        stderr=subprocess.STDOUT,
    #                        shell=True,
    #                        universal_newlines=True)
    #     assert r.returncode == 0

    def test_mysql_show_variables(self):
        c: Configuration = get_default_config()
        mti: MysqlTaskInvoker = MysqlTaskInvoker(c)

        assert isinstance(mti.get_mysql_variables('datadir'), dict)
        assert mti.get_mysql_variables('datadir')['datadir']

    def test_enable_log_bin(self):
        c: Configuration = get_default_config()
        mti: MysqlTaskInvoker = MysqlTaskInvoker(c)
        mycnf_file = mti.get_mycnf_file()
        # assert "abc" in mycnf_file
        MysqlTaskInvoker.enable_logbin(mycnf_file)


    def test_dump(self):
        c: Configuration = get_default_config()
        mti: MysqlTaskInvoker = MysqlTaskInvoker(c)
        fh = mti.invoke_mysql_dump()
        assert fh.Algorithm == "SHA256"

    def test_flush(self):
        c: Configuration = get_default_config()
        mti: MysqlTaskInvoker = MysqlTaskInvoker(c)
        fh = mti.invoke_mysql_flushlogs()
        assert next(fh).Algorithm == "SHA256"
