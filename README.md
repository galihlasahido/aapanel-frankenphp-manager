# aaPanel FrankenPHP Manager

An [aaPanel](https://www.aapanel.com/) plugin to install and manage [FrankenPHP](https://frankenphp.dev/) (a Caddy-based PHP application server) as a standalone service, independent from aaPanel's built-in Nginx-managed websites.

## Features

- **Install**: download an official FrankenPHP release (choose PHP 8.3 / 8.4 / latest), or build from source via [static-php-cli](https://github.com/crazywhalecc/static-php-cli) with a custom PHP version and extension set.
- **Multi-domain management**: add/edit/remove domains, each running in one of three modes:
  - `PHP` — plain Caddy → FrankenPHP
  - `PHP + WAF` — Caddy + Coraza WAF → FrankenPHP
  - `WAF + Load Balancer` — Caddy + Coraza WAF → one or more backend servers (with health checks)
- **WAF (Coraza / OWASP CRS)** per domain:
  - Block or detection-only mode, paranoia level, anomaly score threshold
  - Custom ModSecurity/Coraza rules
  - IP whitelist / blacklist (manual + automatic)
  - Allowed HTTP methods allow-list (including safe handling of Laravel/Symfony-style `_method` override)
  - File upload filter: allow/deny list by extension and/or real MIME type (magic-byte inspection via `@inspectFile`, not the spoofable client `Content-Type` header)
  - CC Defense (request-flood protection) and WAF Auto-Block (repeated-violation IP auto-blacklisting)
  - Force HTTPS (HSTS)
- **PHP configuration**: tune the FrankenPHP-embedded PHP runtime (memory limit, upload size, etc.) from the UI, plus an optional system-wide PHP CLI wrapper (`/usr/bin/php`) so `composer`/`artisan` use FrankenPHP's PHP.
- **Observability**: overview dashboard, per-domain traffic stats, attack map by country (GeoIP), and a searchable/paginated WAF event log (filter by IP, time range, or block reference ID — the same ID returned to blocked clients in the `403` response body for support correlation).

## Installation

Copy this directory to `/www/server/panel/plugin/frankenphp/` on your aaPanel server, then restart the aaPanel service so it picks up the new plugin. Open it from the aaPanel plugin list and click **Install FrankenPHP**.

### Deploy via git

**First install** (directory doesn't exist yet) — clone straight into the `frankenphp` plugin slot:

```bash
cd /www/server/panel/plugin/
git clone https://github.com/galihlasahido/aapanel-frankenphp-manager.git frankenphp
```

**Update an existing install** (already cloned as above) — pull from inside the plugin directory itself:

```bash
cd /www/server/panel/plugin/frankenphp/
git pull
```

Then restart the aaPanel service so it reloads the plugin code.

> Note: `git pull <url> <branch>` only works from *inside* an already-initialized repo, and the branch here is `main` (not `frankenphp`) — use `git clone ... frankenphp` for a first-time deploy into a folder named `frankenphp`.

## License

No license specified yet.
