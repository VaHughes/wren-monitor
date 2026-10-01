#!/usr/bin/env python3
"""Public-route and Cloudflare cron checks, runnable on a non-Cloudflare host."""
import argparse, concurrent.futures, datetime, json, os, time, urllib.request

TARGETS=[('public-search','https://wren.is/health.php','health'),
         ('origin-search','https://origin.wren.is/health.php','health'),
         ('public-bot-route','https://wren.is/bot','identity')]
MAX_BODY=65536
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def validate(kind,raw,now=None):
    if len(raw)>MAX_BODY:raise ValueError('Oversized response')
    if kind=='identity':
        if b'WrenBot' not in raw:raise ValueError('Missing WrenBot identity')
        return
    body=json.loads(raw)
    if kind=='health':
        if body.get('status')!='ok' or body.get('search') is not True:raise ValueError('Search is degraded')
    elif kind=='cron':
        now=now or datetime.datetime.now(datetime.timezone.utc)
        for key in ['origin','worker-health','worker-identity']:
            stamp=datetime.datetime.fromisoformat(body[key]['checkedAt'].replace('Z','+00:00'))
            age=(now-stamp).total_seconds()
            if age < -60 or age > 300:raise ValueError('Cloudflare monitor cron is stale')
            if body[key].get('deliveryError'):raise ValueError('Cloudflare alert delivery failed')
    else:raise ValueError('Unknown probe type')

def probe(name,url,kind,token=None):
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'WrenIndependentMonitor/1.0','Cache-Control':'no-cache',**({'Authorization':'Bearer '+token} if token else {})})
        with urllib.request.build_opener(NoRedirect).open(request,timeout=12) as response:
            if response.status!=200:raise ValueError('HTTP '+str(response.status))
            validate(kind,response.read(MAX_BODY+1))
        return {'name':name,'ok':True}
    except Exception as error:
        # Never echo request headers, response bodies or credential-bearing URLs.
        return {'name':name,'ok':False,'reason':type(error).__name__+': '+str(error).split('\n')[0][:120]}

def run(require_cron=True):
    targets=[(*row,None) for row in TARGETS]
    token=os.environ.get('WREN_MONITOR_ADMIN_TOKEN')
    if token:targets.append(('cloudflare-cron','https://wren-monitor.fond-books.workers.dev/status','cron',token))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        checks=list(executor.map(lambda row:probe(*row),targets))
    if require_cron and not token:checks.append({'name':'cloudflare-cron','ok':False,'reason':'Missing configured monitor secret'})
    return checks

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public-only',action='store_true',help='Explicitly omit cron-silence monitoring')
    parser.add_argument('--confirm-delay',type=int,default=15)
    args=parser.parse_args()
    if not 0<=args.confirm_delay<=30:parser.error('Confirmation delay must be 0–30 seconds')
    checks=run(not args.public_only)
    if any(not c['ok'] for c in checks):
        time.sleep(args.confirm_delay)
        confirmation=run(not args.public_only)
    else:confirmation=checks
    report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'confirmation':confirmation,
        'ok':all(c['ok'] for c in confirmation),'cron_monitored':not args.public_only}
    print(json.dumps(report,indent=2))
    return 0 if report['ok'] else 1
if __name__=='__main__':raise SystemExit(main())
