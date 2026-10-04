# Wren independent monitoring

Requests checks of public Wren routes and search health from GitHub's runners every 30 minutes,
with a second confirmation before failing. Authenticated Cloudflare monitor status
also detects cron silence older than five minutes and failed alert delivery.

The Cloudflare administrator token is a GitHub Actions secret named
`WREN_MONITOR_ADMIN_TOKEN`; no credentials are stored in this repository.

GitHub sends workflow notifications according to the schedule owner's Actions
notification settings. Provider acceptance or a failed workflow does not prove an
email reached an inbox. GitHub schedules can be delayed or dropped, and public
repositories' schedules can be disabled after 60 days without activity. This is
independent of Cloudflare. Its observed October 2–4 schedule gaps were 156–411 minutes,
so the configured interval is not a guarantee of coverage.

Scheduled runs report their check result directly to the authenticated Cloudflare
monitor using the existing secret. No anonymous GitHub API polling is required.
Manual dispatch does not send a scheduled heartbeat. Duplicate reports cannot renew
the clock, and reporting failure fails the scheduled job. Cloudflare retains a
scheduler incident until two successful scheduled reports occur within 90 minutes;
one isolated success cannot produce repeated recovery/outage emails.
The existing Cloudflare monitor provides complementary one-minute origin checks.

Sources: [GitHub schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule),
[workflow notifications](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs).

Run `python3 -m unittest discover -p 'test*.py'` for detector tests.
Run `python3 independent.py --public-only` without the cron secret to explicitly
limit the check to the public routes.
