
from pathlib import Path
from wfc import common_util
from wfc.global_static import Configuration
from wfc.mysql_task_invoker import MysqlTaskInvoker


def get_default_config() -> Configuration:
    return common_util.get_configuration_yml(
        Path(__file__).parent.joinpath("mysql_configuration.2.yml"))


class TestMysqlInvoker:
    def test_mysql_show_variables(self):
        c: Configuration = get_default_config()
        mti: MysqlTaskInvoker = MysqlTaskInvoker(c)
        assert "mysql.exe" in mti.client_bin
        assert "123456>4" == mti.password
        assert 'aa' == mti.get_mysql_variables('datadir')
