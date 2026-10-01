import datetime,importlib.util,json,pathlib,unittest
spec=importlib.util.spec_from_file_location('independent',pathlib.Path(__file__).with_name('independent.py'))
monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)
class IndependentTest(unittest.TestCase):
    def test_health_is_strict(self):
        monitor.validate('health',b'{"status":"ok","search":true}')
        for raw in [b'<html>maintenance</html>',b'{"status":"ok","search":"true"}',b'{"status":"degraded","search":false}']:
            with self.assertRaises((ValueError,json.JSONDecodeError)):monitor.validate('health',raw)
    def test_stale_and_future_cron_fail(self):
        now=datetime.datetime(2026,10,1,21,0,tzinfo=datetime.timezone.utc)
        data={key:{'checkedAt':'2026-10-01T20:59:00Z'} for key in ['origin','worker-health','worker-identity']}
        monitor.validate('cron',json.dumps(data).encode(),now)
        for stamp in ['2026-10-01T20:54:00Z','2026-10-01T21:05:00Z']:
            data['origin']['checkedAt']=stamp
            with self.assertRaises(ValueError):monitor.validate('cron',json.dumps(data).encode(),now)
    def test_identity_and_size(self):
        monitor.validate('identity',b'<h1>WrenBot</h1>')
        with self.assertRaises(ValueError):monitor.validate('identity',b'other worker')
        with self.assertRaises(ValueError):monitor.validate('identity',b'WrenBot'+b'x'*65536)
if __name__=='__main__':unittest.main()
