import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from wfc import common_util
import json


class Holder():
    def __init__(self):
        self.i = 0
    def myfunc(self):
        self.i += 1

class TestApSchedulerFunction:
    def test_interval(self):
        hd = Holder()
        scheduler = BackgroundScheduler()
        job = scheduler.add_job(hd.myfunc, 'interval', seconds=2)
        scheduler.start()
        time.sleep(5)
        assert hd.i > 0

    def test_cron(self):
        """Like Java quartz cron.
        Second, minute, hour, day, month, week_day, year
        year='*', month='*', day=1, week='*', day_of_week='*', hour='*', minute=20, second=0
        """
        hd = Holder()
        scheduler = BackgroundScheduler()
        ds = "year='*', month='*', day=*, week='*', day_of_week='*', hour='*', minute=*, second=*"
        job = scheduler.add_job(hd.myfunc, 'cron', **common_util.parse_pair(ds, ',')) # min star
        scheduler.start()
        time.sleep(3)
        assert hd.i > 0

    def test_cron_1(self):
        hd = Holder()
        scheduler = BackgroundScheduler()
        job = scheduler.add_job(hd.myfunc, 'cron', second='*') # min star
        scheduler.start()
        time.sleep(3)
        assert hd.i > 0

    def test_cron_parser(self):
        ds = "year=*; month=*; day=1; week=\"*\"; day_of_week='55';\
             hour=*; minute=20; second=0; 'kk'=33"
        d = common_util.parse_pair(ds)
        assert d['year'] == '*'
        assert d['minute'] == 20
        assert isinstance(d['minute'], int)
        assert isinstance(d['second'], int)
        assert isinstance(d['day_of_week'], str)
        assert d['week'] == '*'
        assert d['kk'] == 33

# jobstores = {
#     'mongo': MongoDBJobStore(),
#     'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
# }
# executors = {
#     'default': ThreadPoolExecutor(20),
#     'processpool': ProcessPoolExecutor(5)
# }
# job_defaults = {
#     'coalesce': False,
#     'max_instances': 3
# }
# scheduler = BackgroundScheduler(
#     jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)