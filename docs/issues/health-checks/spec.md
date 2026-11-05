# Spec: Health checks

Status: ready-for-agent

## Problem Statement

The bot runs unattended on my Raspberry Pi. If the container crash-loops, the Pi loses power or network, the token is revoked, or a second instance starts polling, nothing tells me: I find out when the bot stops answering in the shop. The nightly backup and the copy to Google Drive can fail just as quietly, and I'd only learn it when I need a snapshot that isn't there.

## Solution

An outside dead man's switch, such as healthchecks.io, watches two checks and alerts me (on Telegram) when either goes quiet:

- **Bot alive:** the bot pings a URL every few minutes, but only after Telegram answered a poll successfully. Silence for about 15 minutes means it's down, whatever the reason.
- **Backup ran:** the nightly cron line pings a second URL only when both the backup and the rclone sync succeeded. Silence for about 25 hours means the backup is broken.

Both are optional. Without the settings nothing is pinged and the bot behaves exactly as today.

## User Stories

1. As the user, I want to be alerted when the bot hasn't successfully polled Telegram for about 15 minutes, so that I learn it's down before I rely on it.
2. As the user, I want one alert to cover a crash-loop, a dead or offline Pi, a revoked token and two instances fighting over the token, so that I don't have to think of every failure.
3. As the user, I want to be alerted when a night's backup or Drive sync didn't succeed, so that I never discover a missing backup at restore time.
4. As the user, I want both checks to be optional settings, so that the bot still runs with only a token and an allow-list.
5. As the user, I want a failing ping (healthchecks.io down, no network) to be logged and otherwise ignored, so that monitoring can never stop the bot.
6. As the user, I want the README to walk me through creating both checks and pointing their alerts at Telegram, so that setup takes minutes.

## Implementation Decisions

- A new optional setting, `BTW_HEARTBEAT_URL`, in `.env.example`. Empty means no heartbeat.
- A small heartbeat unit, given the URL, an interval (5 minutes) and an injectable clock and ping function, decides when a ping is due: the first successful poll pings straight away, later ones at most once per interval.
- The polling loop calls it after every successful `getUpdates`, and never after a failed one. Polling errors (including 401 and 409) therefore surface as silence.
- The ping is a plain HTTP GET with the standard library and a short timeout (about 10 seconds). Any error is logged as a warning without the URL (it identifies the check, so anyone holding it can ping it), and polling carries on.
- The backup check needs no code. The README's cron line gains `&& curl -fsS -m 10 --retry 3 <ping URL> > /dev/null` after `rclone sync`, so it pings only when everything before it succeeded. The URL lives in the crontab, not in `.env`: cron runs on the host.
- Suggested check settings for the README: bot alive with a 5-minute period and 10-minute grace; backup with a 1-day period and 1-hour grace, or a cron schedule matching the crontab line.

## Testing Decisions

- The heartbeat unit is tested with a fake clock and a recording ping function: the first beat pings, beats within the interval don't, a beat after the interval does, and a ping that raises is swallowed.
- The polling loop's wiring, the real HTTP ping and the healthchecks.io setup are verified by hand: run the bot with a real check URL, watch the check turn green, stop the container, watch the alert arrive.

## Out of Scope

- Alerts sent by the bot itself (it can't report its own death).
- Docker health checks: they detect problems but tell no one.
- Pinging a check's failure endpoint for faster alerts on specific errors.
- Monitoring the VPS or the Pi beyond what the two checks reveal.
