# Wren independent monitoring

Checks public Wren routes and search health from GitHub's runners every 30 minutes,
with a second confirmation before failing. Authenticated Cloudflare monitor status
also detects cron silence older than five minutes and failed alert delivery.

The Cloudflare administrator token is a GitHub Actions secret named
`WREN_MONITOR_ADMIN_TOKEN`; no credentials are stored in this repository.

GitHub sends workflow notifications according to the schedule owner's Actions
notification settings. Provider acceptance or a failed workflow does not prove an
email reached an inbox. GitHub schedules can be delayed or dropped, and public
repositories' schedules can be disabled after 60 days without activity. This is
independent of Cloudflare, but cannot alert on its own scheduler being silent.
The existing Cloudflare monitor provides complementary one-minute origin checks.

Sources: [GitHub schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule),
[workflow notifications](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs).

Run `python3 -m unittest discover -p test_independent.py` for detector tests.
Run `python3 independent.py --public-only` without the cron secret to explicitly
limit the check to the public routes.
