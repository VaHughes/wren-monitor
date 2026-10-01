import datetime,importlib.util,json,pathlib,unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('independent',pathlib.Path(__file__).with_name('independent.py'))
monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)
class IndependentTest(unittest.TestCase):
    def test_public_only_omits_cron_even_with_token_present(self):
        with patch.dict('os.environ',{'WREN_MONITOR_ADMIN_TOKEN':'sensitive'}),patch.object(monitor,'probe',side_effect=lambda name,url,kind,token=None:{'name':name,'ok':token is None}) as probe:
            result=monitor.run(False)
            self.assertEqual(len(result),3);self.assertTrue(all(r['ok'] for r in result))
            self.assertTrue(all(call.args[3] is None for call in probe.call_args_list))
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
