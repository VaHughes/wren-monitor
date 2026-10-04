import contextlib,datetime,importlib.util,io,json,os,pathlib,unittest
from unittest import mock
spec=importlib.util.spec_from_file_location('heartbeat_runner',pathlib.Path(__file__).with_name('independent.py'))
monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)

class HeartbeatTest(unittest.TestCase):
    def report(self,ok=True):
        return {'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ok':ok,'cron_monitored':True}

    def test_manual_dispatch_never_reports(self):
        with mock.patch.dict(os.environ,{'GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_RUN_ID':'100','WREN_MONITOR_ADMIN_TOKEN':'scratch'}),mock.patch.object(monitor.urllib.request,'build_opener') as opener:
            self.assertEqual(monitor.report_heartbeat(self.report()),{'sent':False,'reason':'Not a scheduled run'})
            opener.assert_not_called()

    def test_report_is_bounded_and_contains_no_secret_or_private_status(self):
        for ok in [True,False]:
            with mock.patch.dict(os.environ,{'GITHUB_EVENT_NAME':'schedule','GITHUB_RUN_ID':'100','WREN_MONITOR_ADMIN_TOKEN':'scratch'}),mock.patch.object(monitor.urllib.request,'build_opener') as opener:
                response=opener.return_value.open.return_value.__enter__.return_value
                response.status=200;response.read.return_value=b'{"accepted":true}'
                report=self.report(ok);report['private']='must not send'
                self.assertEqual(monitor.report_heartbeat(report),{'sent':True})
                req=opener.return_value.open.call_args.args[0]
                data=json.loads(req.data)
                self.assertEqual(data['event'],'schedule');self.assertEqual(data['ok'],ok)
                self.assertEqual(set(data),{'event','run_id','ok','checked_at','cron_monitored'})
                self.assertNotIn('scratch',req.data.decode())

    def test_reporting_failure_keeps_sensitive_exception_details_private(self):
        with mock.patch.dict(os.environ,{'GITHUB_EVENT_NAME':'schedule','GITHUB_RUN_ID':'100','WREN_MONITOR_ADMIN_TOKEN':'scratch'}),mock.patch.object(monitor.urllib.request,'build_opener') as opener:
            opener.return_value.open.side_effect=RuntimeError('Bearer scratch')
            result=monitor.report_heartbeat(self.report())
        self.assertEqual(result,{'sent':False,'error':'RuntimeError'})

    def test_missing_secret_and_public_only_cannot_report(self):
        with mock.patch.dict(os.environ,{'GITHUB_EVENT_NAME':'schedule','GITHUB_RUN_ID':'100'},clear=True):
            self.assertIn('error',monitor.report_heartbeat(self.report()))
        with mock.patch.dict(os.environ,{'GITHUB_EVENT_NAME':'schedule','GITHUB_RUN_ID':'100','WREN_MONITOR_ADMIN_TOKEN':'scratch'}):
            report=self.report();report['cron_monitored']=False
            self.assertIn('error',monitor.report_heartbeat(report))

    def test_a_failed_report_fails_the_scheduled_job_without_relabelling_probe_results(self):
        with mock.patch('sys.argv',['independent.py','--report-heartbeat']),mock.patch.object(monitor,'run',return_value=[{'name':'route','ok':True}]),mock.patch.object(monitor,'report_heartbeat',return_value={'sent':False,'error':'TimeoutError'}),contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(monitor.main(),1)
        report=json.loads(output.getvalue());self.assertFalse(report['ok']);self.assertTrue(report['checks'][0]['ok'])

if __name__=='__main__':unittest.main()
