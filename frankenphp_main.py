#!/usr/bin/python
# coding: utf-8
import sys, os, json, time, re, sqlite3, socket

os.chdir("/www/server/panel")
sys.path.append("class/")
import public


class frankenphp_main:
    __install_dir = "/www/server/frankenphp"
    __bin = __install_dir + "/bin/frankenphp"
    __config_file = __install_dir + "/config.json"
    __caddyfile = __install_dir + "/Caddyfile"
    __install_log = "/tmp/frankenphp_install.log"
    __plugin_dir = "/www/server/panel/plugin/frankenphp"
    __service = "frankenphp"
    __stats_db_file = __install_dir + "/data/stats.db"
    __stats_service = "frankenphp-statscollect"
    __stats_intervals = (1, 5, 15, 30, 60)
    __geoip_dir = __install_dir + "/data/geoip"
    __geoip_csv_v4 = __geoip_dir + "/dbip-country-ipv4.csv"
    __geoip_csv_v6 = __geoip_dir + "/dbip-country-ipv6.csv"
    # request_log (per-request mentah, buat drill-down "lihat daftar request status 2xx/3xx/dst")
    # jauh lebih besar volumenya dari tabel agregat lain, jadi dibatasi 30 hari (beda dari
    # keputusan retensi tak terbatas utk data agregat) supaya stats.db tidak membengkak tanpa batas.
    __request_log_retention_days = 30

    # ---- i18n ----
    __lang_file = __install_dir + "/data/lang.json"
    __langs = ("en", "id")

    __i18n = {
        "en": {
            "not_installed": "FrankenPHP is not installed",
            "already_installed": "FrankenPHP is already installed",
            "gh_token_too_short": "Invalid token (too short)",
            "gh_token_saved": "GitHub token saved",
            "gh_token_removed": "GitHub token removed",
            "spc_version_invalid": "Invalid static-php-cli version format (e.g. 2.8.5)",
            "spc_refresh_fetch_failed": "Failed to fetch/parse config/ext.json for version {version} - check whether that release tag actually exists in static-php-cli",
            "spc_refresh_too_few": "Result has too few extensions ({count}) - the URL/version is likely wrong, not applied",
            "spc_refresh_success": "Extension list updated to static-php-cli {version} ({count} extensions total)",
            "spc_refresh_added": ". New: {list}",
            "spc_refresh_removed": ". Removed: {list}",
            "more_suffix": " and more",
            "php_version_invalid": "Invalid PHP version format (e.g. 8.2 or 8.2.28)",
            "pick_min_1_ext": "Select at least 1 extension",
            "unknown_extensions": "Unknown extension(s): {list}",
            "conflicting_extensions": "Extension conflict: {hook} already includes {pdo} - static-php-cli does not allow enabling both together. Remove {pdo} from the list (or disable {hook}) and try again.",
            "custom_build_started": "Custom build started in the background (can take 15-40+ minutes, static-php-cli {spc_version}) - safe to leave, progress also appears in aaPanel's Task menu",
            "unknown_php_version_choice": "Unknown PHP version choice: {version}",
            "internal_release_tag_invalid": "Internal release tag is invalid",
            "install_started": "Installation started in the background - safe to leave, progress also appears in aaPanel's Task menu",
            "uninstalled": "FrankenPHP has been removed",
            "port_invalid": "Invalid port",
            "port_range": "Port must be between 1-65535",
            "root_dir_not_found": "Root directory not found: {root}",
            "port_in_use": "Port {port} is already used by another process",
            "domain_format_invalid": "Invalid domain format: {domain}",
            "domain_already_registered": "Domain {domain} is already registered",
            "domain_not_found": "Domain {domain} not found",
            "domain_required": "Domain is required",
            "domain_not_found_or_not_lb": "Domain not found or not in WAF + Load Balancer mode",
            "cc_waf_autoblock_not_enabled": "Neither CC Defense nor WAF Auto-Block is enabled for this domain",
            "interval_must_be_number": "Interval must be a number",
            "interval_unknown": "Unknown interval: {value}",
            "php_config_read_failed": "Failed to read PHP configuration from the FrankenPHP binary",
            "memory_limit_invalid": "Invalid memory_limit (e.g. 256M, 1G, -1)",
            "size_value_invalid": "{key} is invalid (e.g. 20M, 512K)",
            "seconds_value_invalid": "{key} must be a number (seconds), -1 = unlimited",
            "seconds_range_invalid": "{key} must be between -1 and 86400",
            "timezone_invalid": "Invalid date.timezone (e.g. Asia/Jakarta, UTC)",
            "display_errors_invalid": "display_errors must be On or Off",
            "no_changes_submitted": "No changes submitted",
            "wrapper_created_but_failed": "Wrapper created but failed to run: {detail}",
            "no_ip_over_threshold": "No IP currently exceeds the threshold",
            "ip_auto_blocked": "{count} IP(s) automatically blocked ({detail})",
            "no_autoblock_to_clear": "No auto-blocked IPs to clear",
            "autoblock_cleared": "{count} auto-blocked IP(s) cleared",
            "log_lines_processed": "{count} new log line(s) processed",
            "php_cli_wrapper_active": "The 'php' command now runs FrankenPHP's embedded PHP",
            "mode_unknown": "Unknown mode: {mode}",
            "email_format_invalid": "Invalid email format: {email}",
            "waf_engine_unknown": "Unknown WAF engine mode: {engine}",
            "paranoia_must_be_number": "Paranoia level must be a number",
            "paranoia_range": "Paranoia level must be 1-4",
            "anomaly_threshold_must_be_number": "Anomaly threshold must be a number",
            "anomaly_threshold_range": "Anomaly threshold must be 1-1000",
            "custom_rule_no_backtick": "Custom rule must not contain a backtick character (`)",
            "custom_rule_id_reserved": "Rule IDs 900000-900999 are used internally by OWASP CRS & this system (900500) - use a different ID, >= 1000000 recommended, to avoid a silent WAF conflict",
            "upload_filter_mode_unknown": "Unknown upload filter mode: {mode}",
            "upload_filter_empty_list": "Upload filter is enabled but the extension/MIME list is still empty",
            "cc_threshold_must_be_number": "CC Defense: threshold must be a number",
            "cc_threshold_range": "CC Defense: threshold must be 5-100000",
            "cc_window_must_be_number": "CC Defense: window must be a number",
            "cc_window_range": "CC Defense: window must be 5-3600 seconds",
            "autoblock_threshold_must_be_number": "WAF Auto-Block: threshold must be a number",
            "autoblock_threshold_range": "WAF Auto-Block: threshold must be 2-1000",
            "autoblock_window_must_be_number": "WAF Auto-Block: window must be a number",
            "autoblock_window_range": "WAF Auto-Block: window must be 1-1440 minutes",
            "lb_backend_required": "At least 1 backend server (host:port format) is required for load balancer mode",
            "lb_policy_unknown": "Unknown LB policy: {policy}",
            "health_path_must_start_slash": "Health check path must start with /",
            "health_interval_must_be_number": "Health check interval must be a number",
            "health_interval_range": "Health check interval must be 5-3600 seconds",
            "worker_script_required": "Worker script path is required when worker mode is enabled",
            "worker_script_must_be_absolute": "Worker script path must be absolute (start with /)",
            "worker_script_must_be_php": "Worker script must be a .php file",
            "worker_script_not_found": "Worker script file not found: {path}",
            "worker_num_must_be_number": "Number of workers must be a number",
            "worker_num_range": "Number of workers must be 1-64",
            "worker_env_format_invalid": "Invalid worker env format (must be KEY=VALUE): {value}",
            "worker_env_key_invalid": "Invalid env var name (letters/numbers/underscore, cannot start with a number): {value}",
            "worker_env_value_empty": "Env var {key} value cannot be empty",
            "backend_format_invalid": "Invalid backend format (must be host:port): {value}",
            "ip_cidr_invalid": "Invalid IP/CIDR format: {value}",
            "http_method_unsupported": "Unsupported HTTP method: {value}",
            "upload_filter_entry_invalid": "Invalid entry: '{value}' (must be an extension like 'php' or a MIME type like 'image/jpeg')",
            "config_invalid_not_applied": "Invalid configuration, changes NOT applied: {detail}",
            "site_added": "Domain {domain} added. Caddy will automatically request a Let's Encrypt certificate (make sure this domain's DNS already points to the server & ports 80/443 are open).",
            "site_removed": "Domain {domain} removed from FrankenPHP (files in the document root were not deleted)",
            "no_log_for_domain": "(no log for this domain yet - it hasn't received any requests)",
            "config_saved_restarted": "Configuration saved, service restarted",
            "domain_config_updated": "Configuration for domain {domain} updated & service restarted",
            "php_config_saved_restarted": "PHP configuration saved, service restarted",
            "lang_invalid": "Unknown language: {lang}",
            "lang_saved": "Language saved",
        },
        "id": {
            "not_installed": "FrankenPHP belum terinstall",
            "already_installed": "FrankenPHP sudah terinstall",
            "gh_token_too_short": "Token tidak valid (terlalu pendek)",
            "gh_token_saved": "Token GitHub disimpan",
            "gh_token_removed": "Token GitHub dihapus",
            "spc_version_invalid": "Format versi static-php-cli tidak valid (contoh: 2.8.5)",
            "spc_refresh_fetch_failed": "Gagal mengambil/parse config/ext.json untuk versi {version} - cek apakah tag rilis tsb benar-benar ada di static-php-cli",
            "spc_refresh_too_few": "Hasil terlalu sedikit ({count} extension) - kemungkinan URL/versi salah, tidak diterapkan",
            "spc_refresh_success": "Daftar extension diperbarui ke static-php-cli {version} ({count} extension total)",
            "spc_refresh_added": ". Baru: {list}",
            "spc_refresh_removed": ". Hilang: {list}",
            "more_suffix": " dst",
            "php_version_invalid": "Format versi PHP tidak valid (contoh: 8.2 atau 8.2.28)",
            "pick_min_1_ext": "Pilih minimal 1 extension",
            "unknown_extensions": "Extension tidak dikenal: {list}",
            "conflicting_extensions": "Extension bentrok: {hook} sudah menyediakan {pdo} - static-php-cli tidak mengizinkan keduanya aktif bersamaan. Hapus {pdo} dari daftar (atau nonaktifkan {hook}) lalu coba lagi.",
            "custom_build_started": "Build custom dimulai di background (bisa 15-40+ menit, static-php-cli {spc_version}) - aman ditinggal, progress juga muncul di menu Task aaPanel",
            "unknown_php_version_choice": "Pilihan versi PHP tidak dikenal: {version}",
            "internal_release_tag_invalid": "Tag rilis internal tidak valid",
            "install_started": "Instalasi dimulai di background - aman ditinggal, progress juga muncul di menu Task aaPanel",
            "uninstalled": "FrankenPHP telah dihapus",
            "port_invalid": "Port tidak valid",
            "port_range": "Port harus di antara 1-65535",
            "root_dir_not_found": "Direktori root tidak ditemukan: {root}",
            "port_in_use": "Port {port} sudah dipakai proses lain",
            "domain_format_invalid": "Format domain tidak valid: {domain}",
            "domain_already_registered": "Domain {domain} sudah terdaftar",
            "domain_not_found": "Domain {domain} tidak ditemukan",
            "domain_required": "Domain wajib diisi",
            "domain_not_found_or_not_lb": "Domain tidak ditemukan atau bukan mode WAF + Load Balancer",
            "cc_waf_autoblock_not_enabled": "CC Defense maupun WAF Auto-Block belum diaktifkan untuk domain ini",
            "interval_must_be_number": "Interval harus angka",
            "interval_unknown": "Interval tidak dikenal: {value}",
            "php_config_read_failed": "Gagal membaca konfigurasi PHP dari binary FrankenPHP",
            "memory_limit_invalid": "memory_limit tidak valid (contoh: 256M, 1G, -1)",
            "size_value_invalid": "{key} tidak valid (contoh: 20M, 512K)",
            "seconds_value_invalid": "{key} harus angka (detik), -1 = unlimited",
            "seconds_range_invalid": "{key} harus antara -1 sampai 86400",
            "timezone_invalid": "date.timezone tidak valid (contoh: Asia/Jakarta, UTC)",
            "display_errors_invalid": "display_errors harus On atau Off",
            "no_changes_submitted": "Tidak ada perubahan dikirim",
            "wrapper_created_but_failed": "Wrapper dibuat tapi gagal dijalankan: {detail}",
            "no_ip_over_threshold": "Tidak ada IP yang melebihi threshold saat ini",
            "ip_auto_blocked": "{count} IP diblokir otomatis ({detail})",
            "no_autoblock_to_clear": "Tidak ada IP auto-block untuk dibersihkan",
            "autoblock_cleared": "{count} IP auto-block dibersihkan",
            "log_lines_processed": "{count} baris log baru diproses",
            "php_cli_wrapper_active": "Command 'php' sekarang menjalankan PHP embedded FrankenPHP",
            "mode_unknown": "Mode tidak dikenal: {mode}",
            "email_format_invalid": "Format email tidak valid: {email}",
            "waf_engine_unknown": "Mode WAF engine tidak dikenal: {engine}",
            "paranoia_must_be_number": "Paranoia level harus angka",
            "paranoia_range": "Paranoia level harus 1-4",
            "anomaly_threshold_must_be_number": "Anomaly threshold harus angka",
            "anomaly_threshold_range": "Anomaly threshold harus 1-1000",
            "custom_rule_no_backtick": "Custom rule tidak boleh mengandung karakter backtick (`)",
            "custom_rule_id_reserved": "ID rule 900000-900999 dipakai internal oleh OWASP CRS & sistem ini (900500) - pakai ID lain, disarankan >= 1000000, supaya tidak bentrok dan WAF gagal diam-diam",
            "upload_filter_mode_unknown": "Mode filter upload tidak dikenal: {mode}",
            "upload_filter_empty_list": "Filter upload aktif tapi daftar ekstensi/MIME masih kosong",
            "cc_threshold_must_be_number": "CC Defense: threshold harus angka",
            "cc_threshold_range": "CC Defense: threshold harus 5-100000",
            "cc_window_must_be_number": "CC Defense: window harus angka",
            "cc_window_range": "CC Defense: window harus 5-3600 detik",
            "autoblock_threshold_must_be_number": "WAF Auto-Block: threshold harus angka",
            "autoblock_threshold_range": "WAF Auto-Block: threshold harus 2-1000",
            "autoblock_window_must_be_number": "WAF Auto-Block: window harus angka",
            "autoblock_window_range": "WAF Auto-Block: window harus 1-1440 menit",
            "lb_backend_required": "Minimal 1 backend server (format host:port) wajib diisi untuk mode load balancer",
            "lb_policy_unknown": "LB policy tidak dikenal: {policy}",
            "health_path_must_start_slash": "Health check path harus diawali /",
            "health_interval_must_be_number": "Health check interval harus angka",
            "health_interval_range": "Health check interval harus 5-3600 detik",
            "worker_script_required": "Path worker script wajib diisi kalau worker mode diaktifkan",
            "worker_script_must_be_absolute": "Path worker script harus absolut (diawali /)",
            "worker_script_must_be_php": "Worker script harus file .php",
            "worker_script_not_found": "File worker script tidak ditemukan: {path}",
            "worker_num_must_be_number": "Jumlah worker harus angka",
            "worker_num_range": "Jumlah worker harus 1-64",
            "worker_env_format_invalid": "Format env worker tidak valid (harus KEY=VALUE): {value}",
            "worker_env_key_invalid": "Nama env var tidak valid (huruf/angka/underscore, tidak boleh diawali angka): {value}",
            "worker_env_value_empty": "Value env var {key} tidak boleh kosong",
            "backend_format_invalid": "Format backend tidak valid (harus host:port): {value}",
            "ip_cidr_invalid": "Format IP/CIDR tidak valid: {value}",
            "http_method_unsupported": "Method HTTP tidak didukung: {value}",
            "upload_filter_entry_invalid": "Format entry tidak valid: '{value}' (harus ekstensi seperti 'php' atau MIME type seperti 'image/jpeg')",
            "config_invalid_not_applied": "Konfigurasi tidak valid, perubahan TIDAK diterapkan: {detail}",
            "site_added": "Domain {domain} ditambahkan. Caddy akan otomatis minta sertifikat Let's Encrypt (pastikan DNS domain ini sudah mengarah ke server & port 80/443 terbuka).",
            "site_removed": "Domain {domain} dihapus dari FrankenPHP (file di document root tidak dihapus)",
            "no_log_for_domain": "(belum ada log untuk domain ini - belum pernah menerima request)",
            "config_saved_restarted": "Konfigurasi disimpan, service di-restart",
            "domain_config_updated": "Konfigurasi domain {domain} diperbarui & service di-restart",
            "php_config_saved_restarted": "Konfigurasi PHP disimpan, service di-restart",
            "lang_invalid": "Bahasa tidak dikenal: {lang}",
            "lang_saved": "Bahasa disimpan",
        },
    }

    def _get_lang(self):
        if os.path.exists(self.__lang_file):
            try:
                cfg = json.loads(public.ReadFile(self.__lang_file))
                if cfg.get("lang") in self.__langs:
                    return cfg["lang"]
            except:
                pass
        return "en"

    def _t(self, key, **kwargs):
        lang = self._get_lang()
        template = self.__i18n.get(lang, {}).get(key) or self.__i18n["en"].get(key) or key
        try:
            return template.format(**kwargs)
        except Exception:
            return template

    def GetLang(self, get):
        return {"status": True, "lang": self._get_lang()}

    def SetLang(self, get):
        lang = get.lang.strip() if ('lang' in get and get.lang.strip()) else ""
        if lang not in self.__langs:
            return public.ReturnMsg(False, self._t("lang_invalid", lang=lang))
        os.makedirs(os.path.dirname(self.__lang_file), exist_ok=True)
        public.WriteFile(self.__lang_file, json.dumps({"lang": lang}))
        return public.ReturnMsg(True, self._t("lang_saved"))

    def _is_installed(self):
        return os.path.exists(self.__bin)

    def _get_version(self):
        shell = public.ExecShell(self.__bin + " version")
        out = shell[0].strip() if shell and shell[0] else ""
        return out.splitlines()[0] if out else "unknown"

    __domain_re = re.compile(r'^(?=.{1,253}$)([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$')
    __email_re = re.compile(r'^[^\s@{}"\']+@[^\s@{}"\']+\.[^\s@{}"\']+$')
    __backend_re = re.compile(r'^[a-zA-Z0-9.-]+:[0-9]{1,5}$')
    __modes = ("php", "waf_php", "waf_proxy")
    __lb_policies = ("round_robin", "least_conn", "ip_hash", "random", "first")

    __waf_engines = ("on", "detection")
    __paranoia_range = range(1, 5)
    __ipv4_cidr_re = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(/(\d|[12]\d|3[0-2]))?$')
    # daftar tertutup method HTTP yang bisa dipilih di UI - dipakai mentah di dalam directive
    # Coraza (SecAction/SecRule), jadi HARUS whitelist tertutup, tidak boleh free-text apa pun
    # bisa lolos ke sini (celah injeksi ke config WAF kalau divalidasi longgar).
    __http_methods = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "QUERY")
    # Format tertutup buat entry filter upload - dipakai mentah di dalam regex SecRule (ekstensi)
    # maupun ditulis ke script bash validator MIME (@inspectFile), jadi divalidasi ketat.
    __upload_filter_ext_re = re.compile(r'^[a-zA-Z0-9]{1,20}$')
    __upload_filter_mime_re = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9.+-]{0,60}/[a-zA-Z0-9][a-zA-Z0-9.+-]{0,60}$')
    __upload_filter_modes = ("blacklist", "whitelist")
    __worker_env_key_re = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

    def _parse_backends(self, text):
        if not text:
            return []
        parts = re.split(r'[\s,]+', text.strip())
        backends = [p for p in parts if p]
        for b in backends:
            if not self.__backend_re.match(b):
                raise ValueError(self._t("backend_format_invalid", value=b))
        return backends

    def _parse_ip_list(self, text):
        if not text:
            return []
        parts = re.split(r'[\s,]+', text.strip())
        ips = [p for p in parts if p]
        for ip in ips:
            if ':' in ip:
                continue  # IPv6, validasi longgar
            m = self.__ipv4_cidr_re.match(ip)
            if not m or any(int(g) > 255 for g in m.groups()[:4]):
                raise ValueError(self._t("ip_cidr_invalid", value=ip))
        return ips

    def _parse_methods(self, text):
        if not text:
            return []
        parts = re.split(r'[\s,]+', text.strip())
        methods = sorted(set(p.upper() for p in parts if p))
        for m in methods:
            if m not in self.__http_methods:
                raise ValueError(self._t("http_method_unsupported", value=m))
        return methods

    def _parse_upload_filter_list(self, text):
        """Satu baris/entry bisa berupa ekstensi (mis. 'php', '.exe') atau MIME type
        (mis. 'image/jpeg') - dibedakan otomatis dari ada/tidaknya '/'."""
        if not text:
            return []
        parts = re.split(r'[\s,]+', text.strip())
        out = []
        for p in parts:
            if not p:
                continue
            p = p.lstrip('.').lower()
            if self.__upload_filter_ext_re.match(p) or self.__upload_filter_mime_re.match(p):
                out.append(p)
            else:
                raise ValueError(self._t("upload_filter_entry_invalid", value=p))
        return sorted(set(out))

    def _parse_worker_env(self, text):
        """Satu baris = satu env var, format KEY=VALUE (mis. APP_BASE_PATH=/www/wwwroot/x) -
        dibutuhkan worker script tertentu (mis. Laravel Octane: bootstrap.php baca APP_BASE_PATH
        dari env, biasanya otomatis di-set oleh `php artisan octane:frankenphp`, tapi TIDAK
        pernah ke-set kalau worker dipanggil langsung lewat directive `worker` Caddyfile murni
        - makanya field ini perlu ada di plugin, generik buat worker script apa pun)."""
        if not text:
            return {}
        env = {}
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if '=' not in line:
                raise ValueError(self._t("worker_env_format_invalid", value=line))
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if not self.__worker_env_key_re.match(key):
                raise ValueError(self._t("worker_env_key_invalid", value=key))
            if not value:
                raise ValueError(self._t("worker_env_value_empty", key=key))
            env[key] = value
        return env

    def _cpu_percent(self):
        def read():
            with open('/proc/stat') as f:
                vals = list(map(int, f.readline().split()[1:8]))
            return vals[3], sum(vals)
        idle1, total1 = read()
        time.sleep(0.25)
        idle2, total2 = read()
        dt = total2 - total1
        if dt <= 0:
            return 0
        return round((1 - (idle2 - idle1) / dt) * 100, 1)

    def _get_config(self):
        default = {"port": 8080, "root": self.__install_dir + "/www/public", "sites": [], "stats_scan_minutes": 5}
        if not os.path.exists(self.__config_file):
            return default
        try:
            cfg = json.loads(public.ReadFile(self.__config_file))
        except:
            return default

        # migrasi dari format lama (single domain di top-level) ke sites[]
        if "sites" not in cfg and cfg.get("domain"):
            cfg["sites"] = [{"domain": cfg["domain"], "root": cfg.get("root", default["root"]), "email": cfg.get("email", "")}]
            cfg.pop("domain", None)
            cfg.pop("email", None)
            public.WriteFile(self.__config_file, json.dumps(cfg))

        default.update(cfg)
        if not default.get("sites"):
            default["sites"] = []
        return default

    # ---- statistik website (SQLite) ----

    def _stats_db(self):
        """Buka koneksi ke SQLite stats DB, buat skema kalau belum ada. Retensi data tidak
        dibatasi (sesuai keputusan pemilik server) - tidak ada auto-cleanup baris lama."""
        os.makedirs(os.path.dirname(self.__stats_db_file), exist_ok=True)
        conn = sqlite3.connect(self.__stats_db_file, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS hourly_stats (
                domain TEXT NOT NULL,
                hour_ts INTEGER NOT NULL,
                requests INTEGER DEFAULT 0,
                bytes_total INTEGER DEFAULT 0,
                duration_sum REAL DEFAULT 0,
                duration_count INTEGER DEFAULT 0,
                status_2xx INTEGER DEFAULT 0,
                status_3xx INTEGER DEFAULT 0,
                status_4xx INTEGER DEFAULT 0,
                status_5xx INTEGER DEFAULT 0,
                PRIMARY KEY (domain, hour_ts)
            );
            CREATE TABLE IF NOT EXISTS daily_ips (
                domain TEXT NOT NULL,
                day TEXT NOT NULL,
                ip TEXT NOT NULL,
                PRIMARY KEY (domain, day, ip)
            );
            CREATE TABLE IF NOT EXISTS daily_dim_counts (
                domain TEXT NOT NULL,
                day TEXT NOT NULL,
                dim TEXT NOT NULL,
                value TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                PRIMARY KEY (domain, day, dim, value)
            );
            CREATE TABLE IF NOT EXISTS response_time_buckets (
                domain TEXT NOT NULL,
                day TEXT NOT NULL,
                bucket TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                PRIMARY KEY (domain, day, bucket)
            );
            CREATE TABLE IF NOT EXISTS log_offsets (
                domain TEXT PRIMARY KEY,
                file_inode INTEGER,
                byte_offset INTEGER
            );
            CREATE TABLE IF NOT EXISTS geoip_ranges_v4 (
                start_ip INTEGER NOT NULL,
                end_ip INTEGER NOT NULL,
                country TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS geoip_ranges_v6 (
                start_ip TEXT NOT NULL,
                end_ip TEXT NOT NULL,
                country TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS waf_events (
                unique_id TEXT PRIMARY KEY,
                ts REAL NOT NULL,
                domain TEXT NOT NULL,
                client_ip TEXT NOT NULL,
                country TEXT,
                uri TEXT,
                category TEXT,
                rule_id TEXT,
                message TEXT,
                severity TEXT,
                score TEXT
            );
            CREATE TABLE IF NOT EXISTS request_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                ts REAL NOT NULL,
                client_ip TEXT,
                method TEXT,
                uri TEXT,
                status INTEGER,
                size INTEGER,
                duration REAL,
                user_agent TEXT,
                referer TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_hourly_domain_ts ON hourly_stats(domain, hour_ts);
            CREATE INDEX IF NOT EXISTS idx_dim_domain_day ON daily_dim_counts(domain, day, dim);
            CREATE INDEX IF NOT EXISTS idx_geoip_v4_start ON geoip_ranges_v4(start_ip);
            CREATE INDEX IF NOT EXISTS idx_geoip_v6_start ON geoip_ranges_v6(start_ip);
            CREATE INDEX IF NOT EXISTS idx_waf_events_domain_ts ON waf_events(domain, ts);
            CREATE INDEX IF NOT EXISTS idx_waf_events_country_ts ON waf_events(country, ts);
            CREATE INDEX IF NOT EXISTS idx_request_log_domain_ts ON request_log(domain, ts);
            CREATE INDEX IF NOT EXISTS idx_request_log_status ON request_log(domain, status, ts);
        """)
        if conn.execute("SELECT COUNT(*) FROM geoip_ranges_v4").fetchone()[0] == 0:
            self._import_geoip_csv(conn)
        return conn

    def _import_geoip_csv(self, conn):
        """Import CSV DB-IP (IPv4/IPv6 -> negara) ke tabel geoip_ranges_v4/v6. Sekali jalan
        (dicek kosong-tidaknya oleh _stats_db), berjalan ~beberapa detik untuk ~700rb baris."""
        if os.path.exists(self.__geoip_csv_v4):
            batch = []
            with open(self.__geoip_csv_v4, 'r', errors='replace') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) != 3:
                        continue
                    try:
                        start_int = self._ipv4_to_int(parts[0])
                        end_int = self._ipv4_to_int(parts[1])
                    except:
                        continue
                    batch.append((start_int, end_int, parts[2]))
                    if len(batch) >= 20000:
                        conn.executemany("INSERT INTO geoip_ranges_v4 (start_ip,end_ip,country) VALUES (?,?,?)", batch)
                        batch = []
            if batch:
                conn.executemany("INSERT INTO geoip_ranges_v4 (start_ip,end_ip,country) VALUES (?,?,?)", batch)
        if os.path.exists(self.__geoip_csv_v6):
            batch = []
            with open(self.__geoip_csv_v6, 'r', errors='replace') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) != 3:
                        continue
                    try:
                        start_hex = self._ipv6_to_hex(parts[0])
                        end_hex = self._ipv6_to_hex(parts[1])
                    except:
                        continue
                    batch.append((start_hex, end_hex, parts[2]))
                    if len(batch) >= 20000:
                        conn.executemany("INSERT INTO geoip_ranges_v6 (start_ip,end_ip,country) VALUES (?,?,?)", batch)
                        batch = []
            if batch:
                conn.executemany("INSERT INTO geoip_ranges_v6 (start_ip,end_ip,country) VALUES (?,?,?)", batch)
        conn.commit()

    def _ipv4_to_int(self, ip):
        parts = ip.split('.')
        if len(parts) != 4:
            raise ValueError("bukan IPv4")
        return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])

    def _ipv6_to_hex(self, ip):
        return socket.inet_pton(socket.AF_INET6, ip).hex()

    def _geoip_country(self, conn, ip):
        """Lookup negara dari IP pakai tabel geoip_ranges_v4/v6 (binary-search via index
        start_ip, verifikasi end_ip). Return kode negara 2-huruf atau None kalau tidak ketemu."""
        if not ip:
            return None
        try:
            if ':' in ip:
                key = self._ipv6_to_hex(ip)
                row = conn.execute(
                    "SELECT country, end_ip FROM geoip_ranges_v6 WHERE start_ip <= ? ORDER BY start_ip DESC LIMIT 1",
                    (key,)
                ).fetchone()
            else:
                key = self._ipv4_to_int(ip)
                row = conn.execute(
                    "SELECT country, end_ip FROM geoip_ranges_v4 WHERE start_ip <= ? ORDER BY start_ip DESC LIMIT 1",
                    (key,)
                ).fetchone()
        except:
            return None
        if not row:
            return None
        country, end_ip = row
        if end_ip < key:
            return None
        return country

    def _write_upload_mime_script(self, domain, mode, mimes):
        """Generate script bash validator buat Coraza @inspectFile - dipanggil per file upload
        dengan path temp file sebagai argv[1], deteksi MIME asli via `file --mime-type` (bukan
        header Content-Type dari client yang gampang dipalsukan).

        PENTING (perilaku Coraza @inspectFile, sudah dicek ke source-nya): script HARUS selalu
        exit 0 - kalau exit code != 0/proses gagal/timeout, Coraza menganggap "tidak match" alias
        FILE DILOLOSKAN (fail-open), apa pun isi stdout-nya. Sinyal blokir/izin murni dari stdout:
        - baris pertama diawali '1' -> diizinkan (tidak match -> tidak diblokir)
        - baris pertama TIDAK diawali '1' (termasuk output kosong yang bermasalah) -> diblokir
        Makanya tiap cabang logic di bawah selalu diakhiri `exit 0` secara eksplisit.
        """
        scripts_dir = self.__install_dir + "/waf-scripts"
        if not os.path.isdir(scripts_dir):
            os.makedirs(scripts_dir)
        script_path = scripts_dir + "/" + domain + "-mime-check.sh"
        mime_list_str = " ".join(mimes)

        if mode == "whitelist":
            logic = (
                'for m in %s; do\n'
                '    if [ "$mime" == "$m" ]; then echo "1"; exit 0; fi\n'
                'done\n'
                'echo "0 mime type tidak ada di whitelist: $mime"\n'
                'exit 0\n'
            ) % mime_list_str
        else:
            logic = (
                'for m in %s; do\n'
                '    if [ "$mime" == "$m" ]; then echo "0 mime type diblokir (blacklist): $mime"; exit 0; fi\n'
                'done\n'
                'echo "1"\n'
                'exit 0\n'
            ) % mime_list_str

        content = (
            "#!/bin/bash\n"
            "# Auto-generated oleh FrankenPHP Manager - JANGAN diedit manual, akan ditimpa tiap\n"
            "# domain ini disimpan ulang. Domain: %s | Mode: %s\n"
            "mime=$(file --mime-type -b \"$1\" 2>/dev/null)\n"
            "%s"
        ) % (domain, mode, logic)

        public.WriteFile(script_path, content)
        os.chmod(script_path, 0o755)
        return script_path

    def _waf_block(self, engine, paranoia, threshold, custom_rules, whitelist, blacklist, allowed_methods=None,
                    upload_filter_mode=None, upload_filter_list=None, domain=None):
        # PENTING - urutan directive di bawah ini sudah diverifikasi empiris satu-satu ke
        # binary Coraza asli, JANGAN diubah tanpa test ulang pakai curl:
        # 1. id SecAction tuning HARUS bukan 900000 (dipakai internal crs-setup.conf.example,
        #    bentrok id bikin blocking gagal total secara diam-diam - tetap terdeteksi/skor
        #    jalan tapi actual "deny" tidak pernah terpicu). Dipakai 900500 (paranoia/threshold)
        #    & 900200 (allowed_methods).
        # 2. SecRuleEngine HARUS di paling akhir (setelah Include owasp_crs/*.conf) - taruh
        #    di awal membuat coraza.conf-recommended/crs-setup meng-override balik ke
        #    DetectionOnly, WAF jadi silent-fail (terdeteksi tapi tidak blokir).
        # 3. Rule apa pun yang pakai actions disruptive (deny) HARUS ditaruh SETELAH
        #    SecRuleEngine On, kalau tidak actionnya diam-diam tidak dieksekusi meski rule
        #    match (ini kenapa blacklist & custom_rules ditaruh di akhir). Pengecualian yang
        #    sudah diverifikasi empiris (curl langsung, bukan cuma baca kode): override rule
        #    920650/920651 di bawah TETAP jalan meski ditaruh SEBELUM SecRuleEngine On, karena
        #    keduanya cuma menggantikan definisi rule bawaan CRS (bukan rule baru independen)
        #    sebelum CRS selesai di-Include - jangan pindah ke akhir tanpa test ulang.
        # 4. Whitelist (ctl:ruleEngine=Off) justru HARUS di paling AWAL, sebelum semua
        #    include, supaya request dari IP whitelist skip WAF sepenuhnya sebelum sempat
        #    dievaluasi rule apa pun.
        engine_directive = "SecRuleEngine On" if engine != "detection" else "SecRuleEngine DetectionOnly"

        whitelist_rule = ""
        if whitelist:
            whitelist_rule = 'SecRule REMOTE_ADDR "@ipMatch %s" "id:900400,phase:1,pass,nolog,ctl:ruleEngine=Off"\n' % ",".join(whitelist)

        methods_rule = ""
        method_override_rules = ""
        if allowed_methods:
            methods_str = " ".join(allowed_methods)
            # tx.allowed_methods dipakai rule bawaan CRS 911100 (method level HTTP asli).
            methods_rule = "SecAction \"id:900200,phase:1,pass,nolog,t:none,setvar:'tx.allowed_methods=" + methods_str + "'\"\n"
            # CRS bawaan (rule 920650) menandai SEMUA percobaan override method via param
            # _method / header X-HTTP-Method(-Override) sebagai serangan critical, termasuk
            # pola standar Laravel/Symfony (@method('PUT') dsb) - jadi false-positive kalau
            # app memang didesain begitu. Di sini rule itu diganti: override hanya diizinkan
            # kalau nilainya ada di daftar method yang diizinkan, selain itu tetap ditolak.
            method_override_rules = (
                "SecRuleRemoveById 920650\n"
                'SecRule ARGS:_method|REQUEST_HEADERS:X-HTTP-Method-Override|REQUEST_HEADERS:X-HTTP-Method|REQUEST_HEADERS:X-Method-Override "@pm ' + methods_str + '" "id:920650,phase:2,t:none,t:uppercase,pass,nolog"\n'
                'SecRule ARGS:_method|REQUEST_HEADERS:X-HTTP-Method-Override|REQUEST_HEADERS:X-HTTP-Method|REQUEST_HEADERS:X-Method-Override "!@pm ' + methods_str + '" "id:920651,phase:2,t:none,t:uppercase,deny,status:403,log,'
                'msg:\'Disallowed HTTP method override value\','
                'logdata:\'Requested method override: %{MATCHED_VAR}\','
                'severity:\'CRITICAL\','
                'tag:\'application-multi\',tag:\'language-multi\',tag:\'platform-multi\',tag:\'attack-protocol\'"\n'
            )

        directives = (
            whitelist_rule +
            "Include @coraza.conf-recommended\n"
            "Include @crs-setup.conf.example\n"
            "SecAction \"id:900500,phase:1,pass,nolog,"
            "setvar:tx.blocking_paranoia_level=%s,"
            "setvar:tx.inbound_anomaly_score_threshold=%s,"
            "setvar:tx.outbound_anomaly_score_threshold=%s\"\n"
            "%s"
            "Include @owasp_crs/*.conf\n"
            "%s"
            "%s"
        ) % (paranoia, threshold, threshold, methods_rule, method_override_rules, engine_directive)

        if blacklist:
            directives += '\nSecRule REMOTE_ADDR "@ipMatch %s" "id:900600,phase:1,deny,status:403,log,msg:\'IP diblokir (blacklist)\'"' % ",".join(blacklist)
        if upload_filter_list:
            # Ekstensi dicek dari nama file asli (variabel FILES) - MIME dicek dari isi file asli
            # via Coraza @inspectFile (skrip generated menjalankan `file --mime-type`), BUKAN
            # dari header Content-Type yang dikirim client (gampang dipalsukan).
            # Mode whitelist: kedua jenis check (kalau ada) harus SAMA-SAMA lolos (AND) - lebih
            # ketat/aman. Mode blacklist: cukup SALAH SATU match utk memblokir (OR).
            exts = [e for e in upload_filter_list if '/' not in e]
            mimes = [e for e in upload_filter_list if '/' in e]
            if exts:
                ext_pattern = "|".join(re.escape(e) for e in exts)
                if upload_filter_mode == "whitelist":
                    directives += (
                        '\nSecRule FILES "!@rx \\.(?i:%s)$" '
                        '"id:900700,phase:2,t:none,deny,status:403,log,msg:\'Ekstensi file upload tidak diizinkan (whitelist)\'"'
                    ) % ext_pattern
                else:
                    directives += (
                        '\nSecRule FILES "@rx \\.(?i:%s)$" '
                        '"id:900700,phase:2,t:none,deny,status:403,log,msg:\'Ekstensi file upload diblokir (blacklist)\'"'
                    ) % ext_pattern
            if mimes and domain:
                script_path = self._write_upload_mime_script(domain, upload_filter_mode, mimes)
                directives += (
                    '\nSecRule FILES_TMPNAMES "@inspectFile %s" '
                    '"id:900701,phase:2,t:none,deny,status:403,log,msg:\'MIME type file upload tidak diizinkan (%s)\'"'
                ) % (script_path, upload_filter_mode)
        if custom_rules:
            directives += "\n# --- custom rules ---\n" + custom_rules.strip()
        return (
            "\tcoraza_waf {\n"
            "\t\tload_owasp_crs\n"
            "\t\tdirectives `\n"
            "\t\t\t" + directives.replace("\n", "\n\t\t\t") + "\n"
            "\t\t`\n"
            "\t}\n"
        )

    def _quote_caddy_arg(self, value):
        """Bungkus value jadi token Caddyfile yang aman (quoted, escape backslash+quote) -
        dipakai buat argumen directive yang isinya bisa mengandung spasi/karakter apa pun
        (mis. value env var worker mode), supaya tidak memecah directive-nya."""
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return '"%s"' % escaped

    def _site_block(self, s):
        mode = s.get("mode", "php")
        body = "\theader -Server\n"
        if s.get("force_https"):
            # Redirect otomatis HTTP->HTTPS sudah ditangani Caddy (automatic HTTPS) selama
            # domain berhasil dapat sertifikat Let's Encrypt - toggle ini menambahkan HSTS
            # supaya browser SELALU pakai HTTPS ke depannya (termasuk kunjungan pertama via
            # link http://), dan tidak bisa di-downgrade lewat MITM.
            body += "\theader Strict-Transport-Security \"max-age=31536000; includeSubDomains\"\n"
        if mode in ("waf_php", "waf_proxy"):
            # PENTING - ditemukan via testing curl langsung: kalau coraza_waf men-deny request,
            # coraza-caddy tidak menulis response secara normal - ia me-return caddyhttp.HandlerError
            # yang dirender oleh error handler BAWAAN Caddy, jalur ini TIDAK melewati writer yang
            # dipakai directive "header" di atas, jadi "Server: FrankenPHP Caddy" tetap bocor di
            # response 403 meski berhasil dihapus di response normal. handle_errors di bawah
            # memaksa error page dirender lewat handler kita sendiri supaya "header -Server" ikut
            # berlaku juga di response yang diblokir WAF.
            body += (
                "\thandle_errors {\n"
                "\t\theader -Server\n"
                "\t\trespond \"{http.error.status_code} {http.error.status_text} [ref:{http.error.id}]\" {http.error.status_code}\n"
                "\t}\n"
            )
            body += self._waf_block(
                s.get("waf_engine", "on"), s.get("waf_paranoia", 1), s.get("waf_threshold", 5),
                s.get("waf_custom_rules", ""), s.get("waf_whitelist", []), s.get("waf_blacklist", []),
                s.get("waf_allowed_methods", []),
                s.get("waf_upload_filter_mode", "blacklist"),
                s.get("waf_upload_filter_list", []) if s.get("waf_upload_filter_enabled") else [],
                s.get("domain")
            )
        if mode == "waf_proxy":
            backends = s.get("backends", [])
            policy = s.get("lb_policy") or "round_robin"
            health_uri = s.get("health_uri", "")
            health_interval = s.get("health_interval", 30)
            rp_body = "\t\tlb_policy %s\n" % policy
            if health_uri:
                rp_body += (
                    "\t\thealth_uri %s\n"
                    "\t\thealth_interval %ss\n"
                    "\t\thealth_timeout 5s\n"
                ) % (health_uri, health_interval)
            body += "\treverse_proxy %s {\n%s\t}\n" % (" ".join(backends), rp_body)
        else:
            if s.get("worker_enabled") and s.get("worker_script"):
                # Worker mode: aplikasi tetap "hidup" di memory antar-request (tidak boot ulang
                # tiap request kayak mode classic) - butuh worker script yang implementasi
                # protokol worker FrankenPHP sendiri (mis. Laravel Octane nyediain
                # vendor/laravel/octane/bin/frankenphp-worker.php siap pakai).
                #
                # env vars (mis. APP_BASE_PATH buat Laravel Octane) WAJIB di-set eksplisit di
                # sini - worker script Octane butuh APP_BASE_PATH dari env, yang normalnya
                # otomatis di-set oleh `php artisan octane:frankenphp`, tapi TIDAK PERNAH ke-set
                # kalau worker dipanggil langsung lewat directive `worker` Caddyfile murni
                # (kejadian nyata: web mati total - "Cannot find application base path" - baru
                # ketahuan setelah worker mode diaktifkan tanpa env ini).
                env_lines = "".join(
                    "\t\t\tenv %s %s\n" % (k, self._quote_caddy_arg(v))
                    for k, v in (s.get("worker_env") or {}).items()
                )
                php_server_block = (
                    "\tphp_server {\n"
                    "\t\tworker {\n"
                    "\t\t\tfile %s\n"
                    "\t\t\tnum %s\n"
                    "%s"
                    "\t\t}\n"
                    "\t}\n"
                ) % (s["worker_script"], s.get("worker_num", 4), env_lines)
            else:
                php_server_block = "\tphp_server\n"
            body += "\troot * %s\n\tencode gzip\n%s" % (s["root"], php_server_block)
        body += "\tlog {\n\t\toutput file %s/logs/access-%s.log\n\t}\n" % (self.__install_dir, s["domain"])
        return "%s {\n%s}\n" % (s["domain"], body)

    def _build_caddyfile_content(self, sites, port, root):
        global_opts = "\tfrankenphp\n\torder php_server before file_server\n\tadmin off\n"
        needs_waf = any(s.get("mode") in ("waf_php", "waf_proxy") for s in sites)
        if needs_waf:
            global_opts += "\torder coraza_waf first\n"
        if sites:
            email = next((s.get("email") for s in sites if s.get("email")), "")
            if email:
                global_opts += "\temail %s\n" % email
            blocks = [self._site_block(s) for s in sites]
            return "{\n%s}\n\n%s" % (global_opts, "\n".join(blocks))
        else:
            site_block = (
                "\troot * %s\n"
                "\tencode gzip\n"
                "\theader -Server\n"
                "\tphp_server\n"
                "\tlog {\n"
                "\t\toutput file %s/logs/access.log\n"
                "\t}\n"
            ) % (root, self.__install_dir)
            return "{\n%s}\n\n:%s {\n%s}\n" % (global_opts, port, site_block)

    def _validate_caddyfile_content(self, content):
        tmp = "/tmp/frankenphp_validate_%d.conf" % int(time.time() * 1000)
        public.WriteFile(tmp, content)
        shell = public.ExecShell("%s validate --config %s --adapter caddyfile 2>&1" % (self.__bin, tmp))
        out = shell[0] if shell and shell[0] else ""
        public.ExecShell("rm -f %s" % tmp)
        valid = "Valid configuration" in out
        return valid, out

    def _apply_caddyfile(self, sites, port, root):
        """Bangun+validasi Caddyfile dulu, baru diterapkan+restart. Return (True,None) atau (False, pesan_error)."""
        content = self._build_caddyfile_content(sites, port, root)
        valid, out = self._validate_caddyfile_content(content)
        if not valid:
            err_lines = [l for l in out.splitlines() if 'error' in l.lower()]
            err_msg = err_lines[-1] if err_lines else (out.strip().splitlines()[-1] if out.strip() else "unknown error")
            return False, self._t("config_invalid_not_applied", detail=err_msg)
        public.WriteFile(self.__caddyfile, content)
        public.ExecShell("chown -R www:www %s" % self.__install_dir)
        public.ExecShell("systemctl restart %s" % self.__service)
        time.sleep(2)
        return True, None

    # ---- install/uninstall (custom async flow, dipoll dari index.html) ----

    def CheckInstalled(self, get):
        installed = self._is_installed()
        data = {"installed": installed}
        if installed:
            data["version"] = self._get_version()
            data.update(self._get_config())
        return data

    # Kurasi manual dari rilis resmi php/frankenphp - tiap rilis FrankenPHP membundel SATU
    # versi PHP tetap (tidak ada pilihan versi PHP per-rilis dari upstream), jadi "pilih versi
    # PHP" di sini sebenarnya diterjemahkan ke "pilih tag rilis FrankenPHP tertentu yang
    # terbukti (dicek manual via `frankenphp version`) membundel versi itu". Perlu di-refresh
    # manual kalau upstream merilis versi PHP baru lagi - lihat php/frankenphp/releases.
    # PHP 8.2 TIDAK tersedia lewat rilis resmi mana pun (lompat dari 8.3 ke 8.4) - kalau perlu
    # 8.2, satu-satunya jalan adalah build custom via static-php-cli, di luar fitur ini.
    __php_version_tags = {
        "latest": "",       # selalu ambil /releases/latest (PHP terbaru yg dibundel, saat ini 8.5.x)
        "8.4": "v1.10.1",   # PHP 8.4.16
        "8.3": "v1.2.5",    # PHP 8.3.13
    }
    __release_tag_re = re.compile(r'^v\d+\.\d+\.\d+$')
    __custom_php_version_re = re.compile(r'^\d+\.\d+(\.\d+)?$')

    # Daftar extension yang didukung static-php-cli 2.8.5 (config/ext.json di repo tsb, dicek
    # manual) - whitelist TERTUTUP karena nilai ini masuk mentah ke perintah shell `spc build`,
    # jadi harus divalidasi ketat (bukan sekadar filter karakter) supaya tidak bisa disusupi.
    __spc_extensions = (
        "amqp", "apcu", "ast", "bcmath", "brotli", "bz2", "calendar", "com_dotnet", "ctype",
        "curl", "dba", "decimal", "deepclone", "dio", "dom", "ds", "enchant", "ev", "event",
        "excimer", "exif", "ffi", "fileinfo", "filter", "ftp", "gd", "gettext", "glfw", "gmp",
        "gmssl", "grpc", "iconv", "igbinary", "imagick", "imap", "inotify", "intl", "ldap",
        "libxml", "lz4", "maxminddb", "mbregex", "mbstring", "mcrypt", "memcache", "memcached",
        "mongodb", "msgpack", "mysqli", "mysqlnd", "mysqlnd_ed25519", "mysqlnd_parsec", "oci8",
        "odbc", "opcache", "openssl", "opentelemetry", "parallel", "password-argon2", "pcntl",
        "pcov", "pdo", "pdo_mysql", "pdo_odbc", "pdo_pgsql", "pdo_sqlite", "pdo_sqlsrv", "pgsql",
        "phar", "posix", "protobuf", "rar", "rdkafka", "readline", "redis", "session", "shmop",
        "simdjson", "simplexml", "snappy", "snmp", "soap", "sockets", "sodium", "spx", "sqlite3",
        "sqlsrv", "ssh2", "swoole", "swoole-hook-mysql", "swoole-hook-odbc", "swoole-hook-pgsql",
        "swoole-hook-sqlite", "swow", "sysvmsg", "sysvsem", "sysvshm", "tidy", "tokenizer",
        "trader", "uuid", "uv", "xdebug", "xhprof", "xlswriter", "xml", "xmlreader", "xmlwriter",
        "xsl", "xz", "yac", "yaml", "zip", "zlib", "zstd",
    )
    # Preset yang cukup buat kebanyakan app Laravel/umum - dicentang default di UI, sisanya
    # (114 - 34 = 81 extension lain) tetap bisa dicentang manual kalau perlu.
    __spc_extensions_recommended = (
        "bcmath", "ctype", "curl", "dom", "fileinfo", "filter", "gd", "gmp", "iconv", "intl",
        "mbstring", "mysqli", "mysqlnd", "opcache", "openssl", "pcntl", "pdo", "pdo_mysql",
        "pdo_pgsql", "pdo_sqlite", "pgsql", "phar", "posix", "redis", "session", "simplexml",
        "sockets", "sodium", "sqlite3", "tokenizer", "xml", "xmlreader", "xmlwriter", "zip",
        "zlib",
    )

    __spc_default_version = "2.8.5"
    __spc_version_re = re.compile(r'^\d+\.\d+\.\d+$')
    __spc_config_file = __install_dir + "/data/spc-extensions.json"
    __github_token_file = __install_dir + "/data/.github_token"

    def GetGithubTokenStatus(self, get):
        return {"status": True, "set": os.path.exists(self.__github_token_file)}

    def SetGithubToken(self, get):
        """Token GitHub (Personal Access Token, tidak perlu scope apa pun) - dipakai
        static-php-cli saat build custom supaya panggilan ke api.github.com pakai kuota
        akun (5000/jam) bukan kuota anonim per-IP (cuma 60/jam) - build custom bisa manggil
        api.github.com puluhan kali (cek rilis tiap source), gampang kena 403 rate-limit
        tanpa token ini, apalagi kalau IP server dipakai bareng (cloud/NAT). Write-only:
        token tidak pernah dikirim balik ke frontend setelah disimpan."""
        token = get.token.strip() if ('token' in get and get.token.strip()) else ""
        if len(token) < 10:
            return public.ReturnMsg(False, self._t("gh_token_too_short"))
        os.makedirs(os.path.dirname(self.__github_token_file), exist_ok=True)
        public.WriteFile(self.__github_token_file, token)
        os.chmod(self.__github_token_file, 0o600)
        return public.ReturnMsg(True, self._t("gh_token_saved"))

    def RemoveGithubToken(self, get):
        if os.path.exists(self.__github_token_file):
            os.remove(self.__github_token_file)
        return public.ReturnMsg(True, self._t("gh_token_removed"))

    def _get_spc_config(self):
        """Config extension static-php-cli (versi + daftar extension) - disimpan di file,
        BUKAN hardcode Python, supaya bisa di-refresh dari UI tanpa update kode plugin.
        File belum ada (instalasi baru) -> bootstrap dari default yang sudah teruji manual."""
        if os.path.exists(self.__spc_config_file):
            try:
                cfg = json.loads(public.ReadFile(self.__spc_config_file))
                if cfg.get("extensions") and cfg.get("spc_version"):
                    return cfg
            except:
                pass
        default = {
            "spc_version": self.__spc_default_version,
            "extensions": list(self.__spc_extensions),
            "recommended": list(self.__spc_extensions_recommended),
        }
        os.makedirs(os.path.dirname(self.__spc_config_file), exist_ok=True)
        public.WriteFile(self.__spc_config_file, json.dumps(default))
        return default

    def GetPhpVersionOptions(self, get):
        return {"status": True, "options": list(self.__php_version_tags.keys())}

    def GetSpcExtensionOptions(self, get):
        cfg = self._get_spc_config()
        return {
            "status": True,
            "spc_version": cfg["spc_version"],
            "extensions": cfg["extensions"],
            "recommended": cfg["recommended"],
        }

    def RefreshSpcExtensions(self, get):
        """Ambil ulang daftar extension yang didukung dari config/ext.json static-php-cli
        pada VERSI yang diminta (admin isi manual) - supaya bisa dapat extension yang baru
        dirilis tanpa nunggu update kode plugin. Versi ini JUGA yang akan dipakai proses
        build custom berikutnya (Install_frankenphp), jadi pastikan versi yang dipilih
        memang kompatibel dengan alur build.sh (belum tentu semua versi baru langsung aman)."""
        version = get.spc_version.strip() if ('spc_version' in get and get.spc_version.strip()) else ""
        if not self.__spc_version_re.match(version):
            return public.ReturnMsg(False, self._t("spc_version_invalid"))

        url = "https://raw.githubusercontent.com/crazywhalecc/static-php-cli/%s/config/ext.json" % version
        shell = public.ExecShell("curl -sL --fail --max-time 30 '%s'" % url)
        raw = shell[0] if shell and shell[0] else ""
        try:
            data = json.loads(raw)
            new_extensions = sorted(data.keys())
        except:
            return public.ReturnMsg(False, "Gagal mengambil/parse config/ext.json untuk versi " + version + " - cek apakah tag rilis tsb benar-benar ada di static-php-cli")
        if len(new_extensions) < 20:
            return public.ReturnMsg(False, self._t("spc_refresh_too_few", count=len(new_extensions)))

        old_cfg = self._get_spc_config()
        old_extensions = set(old_cfg["extensions"])
        added = sorted(set(new_extensions) - old_extensions)
        removed = sorted(old_extensions - set(new_extensions))
        # rekomendasi lama dipertahankan sepanjang masih ada di daftar baru - jangan sampai
        # UI nyimpen extension yang sudah tidak dikenal lagi.
        new_recommended = sorted(set(old_cfg["recommended"]) & set(new_extensions))

        new_cfg = {"spc_version": version, "extensions": new_extensions, "recommended": new_recommended}
        os.makedirs(os.path.dirname(self.__spc_config_file), exist_ok=True)
        public.WriteFile(self.__spc_config_file, json.dumps(new_cfg))

        msg = self._t("spc_refresh_success", version=version, count=len(new_extensions))
        if added:
            msg += self._t("spc_refresh_added", list=", ".join(added[:20]) + (self._t("more_suffix") if len(added) > 20 else ""))
        if removed:
            msg += self._t("spc_refresh_removed", list=", ".join(removed[:20]) + (self._t("more_suffix") if len(removed) > 20 else ""))
        result = public.ReturnMsg(True, msg)
        result["extensions"] = new_extensions
        result["recommended"] = new_recommended
        result["added"] = added
        result["removed"] = removed
        return result

    def _add_soft_install_task(self, name, shell_cmd):
        """Daftarkan shell command ke tabel `tasks` aaPanel - INI (bukan panelTask.bt_task/
        task_list) yang jadi sumber badge/message-box "Task" install plugin/software bawaan
        aaPanel, dipoll tiap 2 detik oleh BTTask.task.soft_task(). Sempat salah pakai
        panelTask.bt_task sebelumnya - itu jalan (task_list-nya sendiri valid & tereksekusi
        via daemon BT-Task yang sama), tapi TIDAK muncul di message box karena UI message-box
        aaPanel baca dari tabel `tasks`, bukan `task_list`. Wajib juga tulis tip file
        /tmp/panelTask.pl - poller-nya SKIP total kalau file ini tidak ada, task bisa nyangkut
        di status 'waiting' selamanya kalau lupa."""
        public.M('tasks').add(
            'id,name,type,status,addtime,execstr',
            (None, name, 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), shell_cmd)
        )
        public.WriteFile('/tmp/panelTask.pl', 'True')

    def Install(self, get):
        if self._is_installed():
            return public.ReturnMsg(False, self._t("already_installed"))

        php_version = get.php_version.strip() if ('php_version' in get and get.php_version.strip()) else "latest"

        if php_version == "custom":
            custom_version = get.custom_php_version.strip() if ('custom_php_version' in get and get.custom_php_version.strip()) else ""
            if not self.__custom_php_version_re.match(custom_version):
                return public.ReturnMsg(False, self._t("php_version_invalid"))

            spc_cfg = self._get_spc_config()
            spc_version = spc_cfg["spc_version"]

            ext_raw = get.extensions if 'extensions' in get else ""
            extensions = sorted(set(e.strip() for e in ext_raw.split(",") if e.strip()))
            if not extensions:
                return public.ReturnMsg(False, self._t("pick_min_1_ext"))
            unknown = [e for e in extensions if e not in spc_cfg["extensions"]]
            if unknown:
                return public.ReturnMsg(False, self._t("unknown_extensions", list=", ".join(unknown)))

            # static-php-cli tolak build kalau swoole-hook-X dan pdo_X (yg disediakan hook itu)
            # sama-sama aktif - dicek langsung di source spc (src/SPC/builder/extension/
            # swoole_hook_{pgsql,sqlite,odbc}.php: method validate()). swoole-hook-mysql TIDAK
            # kena aturan ini (tidak override validate()), jadi tidak dicek di sini.
            ext_set = set(extensions)
            for hook, pdo_ext in (
                ("swoole-hook-pgsql", "pdo_pgsql"),
                ("swoole-hook-sqlite", "pdo_sqlite"),
                ("swoole-hook-odbc", "pdo_odbc"),
            ):
                if hook in ext_set and pdo_ext in ext_set:
                    return public.ReturnMsg(False, self._t("conflicting_extensions", hook=hook, pdo=pdo_ext))

            public.ExecShell("echo '' > %s" % self.__install_log)
            shell_cmd = "bash %s/install.sh install custom %s %s %s" % (
                self.__plugin_dir, custom_version, ",".join(extensions), spc_version
            )
            # Daftar ke antrian install/software bawaan aaPanel (tabel `tasks`, BUKAN
            # panelTask.bt_task/task_list) - dieksekusi oleh daemon BT-Task yang berjalan
            # terpisah dari proses request HTTP ini, jadi proses build (bisa 15-40+ menit)
            # benar-benar lepas dari koneksi browser/panel. Progress juga otomatis muncul
            # di badge/message-box Task aaPanel sendiri, di luar polling GetInstallLog
            # milik plugin ini.
            self._add_soft_install_task("Install FrankenPHP (build custom PHP %s)" % custom_version, shell_cmd)
            return public.ReturnMsg(True, self._t("custom_build_started", spc_version=spc_version))

        if php_version not in self.__php_version_tags:
            return public.ReturnMsg(False, self._t("unknown_php_version_choice", version=php_version))
        release_tag = self.__php_version_tags[php_version]
        if release_tag and not self.__release_tag_re.match(release_tag):
            return public.ReturnMsg(False, self._t("internal_release_tag_invalid"))  # pengaman, seharusnya tidak pernah kena

        public.ExecShell("echo '' > %s" % self.__install_log)
        shell_cmd = "bash %s/install.sh install %s" % (self.__plugin_dir, release_tag)
        self._add_soft_install_task("Install FrankenPHP", shell_cmd)
        return public.ReturnMsg(True, self._t("install_started"))

    def GetInstallLog(self, get):
        if not os.path.exists(self.__install_log):
            return {"log": "", "finished": False, "installed": self._is_installed()}
        content = public.ReadFile(self.__install_log) or ""
        finished = ("SUCCESS" in content) or ("gagal" in content.lower()) or ("tidak didukung" in content.lower())
        return {"log": content, "finished": finished, "installed": self._is_installed()}

    def Uninstall(self, get):
        public.ExecShell("bash %s/install.sh uninstall" % self.__plugin_dir)
        return public.ReturnMsg(True, self._t("uninstalled"))

    # ---- service control ----

    def GetServerStatus(self, get):
        if not self._is_installed():
            return {"installed": False, "running": False}
        shell = public.ExecShell("systemctl is-active %s" % self.__service)
        running = bool(shell and shell[0] and shell[0].strip() == "active")
        data = {"installed": True, "running": running, "version": self._get_version()}
        data.update(self._get_config())
        return data

    def StartService(self, get):
        public.ExecShell("systemctl start %s" % self.__service)
        time.sleep(1)
        return self.GetServerStatus(get)

    def StopService(self, get):
        public.ExecShell("systemctl stop %s" % self.__service)
        time.sleep(1)
        return self.GetServerStatus(get)

    def RestartService(self, get):
        public.ExecShell("systemctl restart %s" % self.__service)
        time.sleep(1)
        return self.GetServerStatus(get)

    # ---- config ----

    def GetConfig(self, get):
        return self._get_config()

    def SetConfig(self, get):
        """Atur port+root fallback, dipakai HANYA saat belum ada domain terdaftar (sites kosong)."""
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        try:
            port = int(get.port)
        except:
            return public.ReturnMsg(False, self._t("port_invalid"))
        if port < 1 or port > 65535:
            return public.ReturnMsg(False, self._t("port_range"))
        root = get.root.strip() if ('root' in get and get.root.strip()) else self.__install_dir + "/www/public"
        if not os.path.exists(root):
            return public.ReturnMsg(False, self._t("root_dir_not_found", root=root))

        cfg = self._get_config()
        sites = cfg.get("sites", [])
        if not sites:
            check = public.ExecShell("ss -tlnp 2>/dev/null | grep ':%s '" % port)
            if check and check[0] and 'frankenphp' not in check[0]:
                return public.ReturnMsg(False, self._t("port_in_use", port=port))

        ok, err = self._apply_caddyfile(sites, port, root)
        if not ok:
            return public.ReturnMsg(False, err)
        cfg["port"] = port
        cfg["root"] = root
        public.WriteFile(self.__config_file, json.dumps(cfg))

        result = self.GetServerStatus(get)
        result["msg"] = self._t("config_saved_restarted")
        result["status"] = True
        return result

    def _build_site_fields(self, get, domain, default_root, existing=None):
        """Validasi field form (mode, root, backends, lb_policy, email) -> (dict, None) atau (None, error_msg)"""
        mode = get.mode.strip() if ('mode' in get and get.mode.strip()) else "php"
        if mode not in self.__modes:
            return None, self._t("mode_unknown", mode=mode)

        email = get.email.strip() if ('email' in get and get.email.strip()) else ""
        if email and not self.__email_re.match(email):
            return None, self._t("email_format_invalid", email=email)

        force_https = str(get.force_https).strip() == "1" if 'force_https' in get else False

        site = {"domain": domain, "mode": mode, "email": email, "force_https": force_https}

        if mode in ("waf_php", "waf_proxy"):
            engine = get.waf_engine.strip() if ('waf_engine' in get and get.waf_engine.strip()) else "on"
            if engine not in self.__waf_engines:
                return None, self._t("waf_engine_unknown", engine=engine)
            try:
                paranoia = int(get.waf_paranoia) if ('waf_paranoia' in get and str(get.waf_paranoia).strip()) else 1
            except:
                return None, self._t("paranoia_must_be_number")
            if paranoia not in self.__paranoia_range:
                return None, self._t("paranoia_range")
            try:
                threshold = int(get.waf_threshold) if ('waf_threshold' in get and str(get.waf_threshold).strip()) else 5
            except:
                return None, self._t("anomaly_threshold_must_be_number")
            if threshold < 1 or threshold > 1000:
                return None, self._t("anomaly_threshold_range")
            custom_rules = get.waf_custom_rules if 'waf_custom_rules' in get else ""
            if custom_rules and '`' in custom_rules:
                return None, self._t("custom_rule_no_backtick")
            if custom_rules and re.search(r'\bid\s*:\s*900[0-9]{3}\b', custom_rules):
                return None, self._t("custom_rule_id_reserved")
            try:
                whitelist = self._parse_ip_list(get.waf_whitelist if 'waf_whitelist' in get else "")
            except ValueError as e:
                return None, str(e)
            try:
                blacklist_manual = self._parse_ip_list(get.waf_blacklist if 'waf_blacklist' in get else "")
            except ValueError as e:
                return None, str(e)
            try:
                allowed_methods = self._parse_methods(get.waf_allowed_methods if 'waf_allowed_methods' in get else "")
            except ValueError as e:
                return None, str(e)

            upload_filter_enabled = str(get.waf_upload_filter_enabled).strip() == "1" if 'waf_upload_filter_enabled' in get else False
            upload_filter_mode = get.waf_upload_filter_mode.strip() if ('waf_upload_filter_mode' in get and get.waf_upload_filter_mode.strip()) else "blacklist"
            if upload_filter_mode not in self.__upload_filter_modes:
                return None, self._t("upload_filter_mode_unknown", mode=upload_filter_mode)
            try:
                upload_filter_list = self._parse_upload_filter_list(get.waf_upload_filter_list if 'waf_upload_filter_list' in get else "")
            except ValueError as e:
                return None, str(e)
            if upload_filter_enabled and not upload_filter_list:
                return None, self._t("upload_filter_empty_list")

            # blacklist auto-hasil CC Defense tetap dipertahankan (jangan hilang tiap kali form disave),
            # digabung dengan yang manual & di-dedup.
            cc_auto = (existing.get("waf_blacklist_auto", []) if existing else [])
            blacklist = sorted(set(blacklist_manual) | set(cc_auto))

            cc_enabled = str(get.cc_enabled).strip() == "1" if 'cc_enabled' in get else False
            try:
                cc_threshold = int(get.cc_threshold) if ('cc_threshold' in get and str(get.cc_threshold).strip()) else 300
            except:
                return None, self._t("cc_threshold_must_be_number")
            if cc_threshold < 5 or cc_threshold > 100000:
                return None, self._t("cc_threshold_range")
            try:
                cc_window = int(get.cc_window) if ('cc_window' in get and str(get.cc_window).strip()) else 60
            except:
                return None, self._t("cc_window_must_be_number")
            if cc_window < 5 or cc_window > 3600:
                return None, self._t("cc_window_range")

            waf_autoblock_enabled = str(get.waf_autoblock_enabled).strip() == "1" if 'waf_autoblock_enabled' in get else False
            try:
                waf_autoblock_threshold = int(get.waf_autoblock_threshold) if ('waf_autoblock_threshold' in get and str(get.waf_autoblock_threshold).strip()) else 5
            except:
                return None, self._t("autoblock_threshold_must_be_number")
            if waf_autoblock_threshold < 2 or waf_autoblock_threshold > 1000:
                return None, self._t("autoblock_threshold_range")
            try:
                waf_autoblock_window = int(get.waf_autoblock_window) if ('waf_autoblock_window' in get and str(get.waf_autoblock_window).strip()) else 10
            except:
                return None, self._t("autoblock_window_must_be_number")
            if waf_autoblock_window < 1 or waf_autoblock_window > 1440:
                return None, self._t("autoblock_window_range")

            site["waf_engine"] = engine
            site["waf_paranoia"] = paranoia
            site["waf_threshold"] = threshold
            site["waf_custom_rules"] = custom_rules.strip() if custom_rules else ""
            site["waf_whitelist"] = whitelist
            site["waf_blacklist"] = blacklist
            site["waf_blacklist_manual"] = blacklist_manual
            site["waf_blacklist_auto"] = cc_auto
            site["waf_allowed_methods"] = allowed_methods
            site["waf_upload_filter_enabled"] = upload_filter_enabled
            site["waf_upload_filter_mode"] = upload_filter_mode
            site["waf_upload_filter_list"] = upload_filter_list
            site["cc_enabled"] = cc_enabled
            site["cc_threshold"] = cc_threshold
            site["cc_window"] = cc_window
            site["waf_autoblock_enabled"] = waf_autoblock_enabled
            site["waf_autoblock_threshold"] = waf_autoblock_threshold
            site["waf_autoblock_window"] = waf_autoblock_window

        if mode == "waf_proxy":
            try:
                backends = self._parse_backends(get.backends if 'backends' in get else "")
            except ValueError as e:
                return None, str(e)
            if not backends:
                return None, self._t("lb_backend_required")
            policy = get.lb_policy.strip() if ('lb_policy' in get and get.lb_policy.strip()) else "round_robin"
            if policy not in self.__lb_policies:
                return None, self._t("lb_policy_unknown", policy=policy)
            health_uri = get.health_uri.strip() if ('health_uri' in get and get.health_uri.strip()) else ""
            if health_uri and not health_uri.startswith("/"):
                return None, self._t("health_path_must_start_slash")
            try:
                health_interval = int(get.health_interval) if ('health_interval' in get and str(get.health_interval).strip()) else 30
            except:
                return None, self._t("health_interval_must_be_number")
            if health_interval < 5 or health_interval > 3600:
                return None, self._t("health_interval_range")
            site["backends"] = backends
            site["lb_policy"] = policy
            site["health_uri"] = health_uri
            site["health_interval"] = health_interval
        else:
            root = get.root.strip() if ('root' in get and get.root.strip()) else default_root
            if not os.path.exists(root):
                public.ExecShell("mkdir -p '%s'" % root)
            index_path = root.rstrip("/") + "/index.php"
            if not os.path.exists(index_path):
                public.WriteFile(index_path, "<?php\necho '<h1>' . htmlspecialchars($_SERVER['HTTP_HOST']) . ' is running</h1><p>PHP ' . PHP_VERSION . ' via FrankenPHP</p>';\n")
            site["root"] = root

            # Worker mode: script-nya lazim ada DI LUAR root (mis. Laravel Octane -
            # vendor/laravel/octane/bin/frankenphp-worker.php ada satu level di atas root
            # public/), jadi sengaja TIDAK dibatasi harus di dalam root - konsisten dengan
            # field root sendiri yang juga tidak dijail ke direktori tertentu (plugin ini
            # cuma dipakai admin server, bukan input multi-tenant tidak terpercaya).
            worker_enabled = str(get.worker_enabled).strip() == "1" if 'worker_enabled' in get else False
            worker_script = ""
            worker_num = 4
            if worker_enabled:
                worker_script = get.worker_script.strip() if ('worker_script' in get and get.worker_script.strip()) else ""
                if not worker_script:
                    return None, self._t("worker_script_required")
                if not worker_script.startswith("/"):
                    return None, self._t("worker_script_must_be_absolute")
                if not worker_script.endswith(".php"):
                    return None, self._t("worker_script_must_be_php")
                if not os.path.isfile(worker_script):
                    return None, self._t("worker_script_not_found", path=worker_script)
                try:
                    worker_num = int(get.worker_num) if ('worker_num' in get and str(get.worker_num).strip()) else 4
                except:
                    return None, self._t("worker_num_must_be_number")
                if worker_num < 1 or worker_num > 64:
                    return None, self._t("worker_num_range")
            try:
                worker_env = self._parse_worker_env(get.worker_env if 'worker_env' in get else "")
            except ValueError as e:
                return None, str(e)
            site["worker_enabled"] = worker_enabled
            site["worker_script"] = worker_script
            site["worker_num"] = worker_num
            site["worker_env"] = worker_env

        return site, None

    def AddSite(self, get):
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        domain = get.domain.strip() if ('domain' in get and get.domain.strip()) else ""
        if not domain or not self.__domain_re.match(domain):
            return public.ReturnMsg(False, self._t("domain_format_invalid", domain=domain))

        cfg = self._get_config()
        sites = cfg.get("sites", [])
        if any(s["domain"] == domain for s in sites):
            return public.ReturnMsg(False, self._t("domain_already_registered", domain=domain))

        site, err = self._build_site_fields(get, domain, self.__install_dir + "/www/" + domain)
        if err:
            return public.ReturnMsg(False, err)

        candidate_sites = sites + [site]
        ok, err = self._apply_caddyfile(candidate_sites, cfg.get("port", 8080), cfg.get("root"))
        if not ok:
            return public.ReturnMsg(False, err)
        cfg["sites"] = candidate_sites
        public.WriteFile(self.__config_file, json.dumps(cfg))

        result = self.GetServerStatus(get)
        result["msg"] = self._t("site_added", domain=domain)
        result["status"] = True
        return result

    def UpdateSite(self, get):
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        domain = get.domain.strip() if 'domain' in get else ""

        cfg = self._get_config()
        sites = cfg.get("sites", [])
        idx = next((i for i, s in enumerate(sites) if s["domain"] == domain), None)
        if idx is None:
            return public.ReturnMsg(False, self._t("domain_not_found", domain=domain))

        site, err = self._build_site_fields(get, domain, self.__install_dir + "/www/" + domain, existing=sites[idx])
        if err:
            return public.ReturnMsg(False, err)

        candidate_sites = list(sites)
        candidate_sites[idx] = site
        ok, err = self._apply_caddyfile(candidate_sites, cfg.get("port", 8080), cfg.get("root"))
        if not ok:
            return public.ReturnMsg(False, err)
        cfg["sites"] = candidate_sites
        public.WriteFile(self.__config_file, json.dumps(cfg))

        result = self.GetServerStatus(get)
        result["msg"] = self._t("domain_config_updated", domain=domain)
        result["status"] = True
        return result

    def RemoveSite(self, get):
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        domain = get.domain.strip() if 'domain' in get else ""
        cfg = self._get_config()
        sites = cfg.get("sites", [])
        new_sites = [s for s in sites if s["domain"] != domain]
        if len(new_sites) == len(sites):
            return public.ReturnMsg(False, self._t("domain_not_found", domain=domain))

        ok, err = self._apply_caddyfile(new_sites, cfg.get("port", 8080), cfg.get("root"))
        if not ok:
            return public.ReturnMsg(False, err)
        cfg["sites"] = new_sites
        public.WriteFile(self.__config_file, json.dumps(cfg))

        result = self.GetServerStatus(get)
        result["msg"] = self._t("site_removed", domain=domain)
        result["status"] = True
        return result

    # ---- logs ----

    def GetLog(self, get):
        shell = public.ExecShell("journalctl -u %s -n 200 --no-pager" % self.__service)
        return {"log": shell[0] if shell and shell[0] else ""}

    def GetSiteLog(self, get):
        domain = get.domain.strip() if ('domain' in get and get.domain.strip()) else ""
        if not domain:
            return self.GetLog(get)
        logfile = "%s/logs/access-%s.log" % (self.__install_dir, domain)
        if not os.path.exists(logfile):
            return {"log": self._t("no_log_for_domain")}
        shell = public.ExecShell("tail -n 300 '%s'" % logfile)
        return {"log": shell[0] if shell and shell[0] else ""}

    __waf_id_re = re.compile(r'\[id\s+"([^"]*)"\]')
    __waf_msg_re = re.compile(r'\[msg\s+"((?:[^"\\]|\\.)*)"\]')
    __waf_sev_re = re.compile(r'\[severity\s+"([^"]*)"\]')
    __waf_tag_re = re.compile(r'\[tag\s+"([^"]*)"\]')
    __waf_uid_re = re.compile(r'\[unique_id\s+"([^"]*)"\]')
    __waf_score_re = re.compile(r'Total Score:\s*(\d+)')

    def _get_waf_events(self, domain=None, limit=20000):
        """Ambil & parse event WAF terstruktur dari journal, dikorelasikan via unique_id.
        domain=None -> semua domain (dipakai untuk agregat overview)."""
        shell = public.ExecShell(
            "journalctl -u %s --no-pager -o cat -n %d | grep -F 'http.handlers.waf'" % (self.__service, limit)
        )
        lines = (shell[0] or "").splitlines() if shell else []

        details_by_id = {}
        summaries = []

        for line in lines:
            try:
                obj = json.loads(line)
            except:
                continue
            msg = obj.get("msg", "")
            if msg == "WAF rule violation detected":
                if domain is None or obj.get("hostname") == domain:
                    summaries.append(obj)
                continue
            uid_m = self.__waf_uid_re.search(msg)
            if not uid_m:
                continue
            uid = uid_m.group(1)
            score_m = self.__waf_score_re.search(msg)
            if score_m:
                details_by_id.setdefault(uid, {})["score"] = score_m.group(1)
                continue
            id_m = self.__waf_id_re.search(msg)
            if not id_m:
                continue
            entry = details_by_id.setdefault(uid, {})
            entry.setdefault("rules", []).append({
                "id": id_m.group(1),
                "msg": (self.__waf_msg_re.search(msg).group(1) if self.__waf_msg_re.search(msg) else ""),
                "severity": (self.__waf_sev_re.search(msg).group(1) if self.__waf_sev_re.search(msg) else ""),
                "tags": self.__waf_tag_re.findall(msg),
            })

        events = []
        for s in summaries:
            uid = s.get("unique_id", "")
            d = details_by_id.get(uid, {})
            rules = d.get("rules", [])
            top_rule = rules[0] if rules else None
            category = "OTHER"
            for r in rules:
                tag = next((t for t in r.get("tags", []) if t.startswith("attack-")), None)
                if tag:
                    category = tag.replace("attack-", "").upper()
                    break
            events.append({
                "ts": s.get("ts"),
                "domain": s.get("hostname", ""),
                "client_ip": (s.get("client_ip") or "").split(":")[0],
                "uri": s.get("uri", ""),
                "score": d.get("score", ""),
                "rule_count": len(rules),
                "rule_id": top_rule["id"] if top_rule else "",
                "message": top_rule["msg"] if top_rule else "Rule violation",
                "severity": top_rule["severity"] if top_rule else "",
                "category": category,
                "unique_id": uid,
            })
        return events

    def GetWafEvents(self, get):
        """Event WAF terstruktur untuk satu domain (dipakai tab Keamanan per-domain).
        Filter opsional: ip (substring client_ip), ref (substring unique_id, case-insensitive),
        ts_from/ts_to (unix epoch detik, batas waktu kejadian)."""
        domain = get.domain.strip() if ('domain' in get and get.domain.strip()) else ""
        if not domain:
            return public.ReturnMsg(False, self._t("domain_required"))

        ip_filter = get.ip.strip() if ('ip' in get and get.ip.strip()) else ""
        ref_filter = get.ref.strip().lower() if ('ref' in get and get.ref.strip()) else ""
        try:
            ts_from = float(get.ts_from) if ('ts_from' in get and str(get.ts_from).strip()) else None
        except:
            ts_from = None
        try:
            ts_to = float(get.ts_to) if ('ts_to' in get and str(get.ts_to).strip()) else None
        except:
            ts_to = None

        events = self._get_waf_events(domain)
        if ip_filter:
            events = [e for e in events if ip_filter in (e.get("client_ip") or "")]
        if ref_filter:
            events = [e for e in events if ref_filter in (e.get("unique_id") or "").lower()]
        if ts_from is not None:
            events = [e for e in events if (e.get("ts") or 0) >= ts_from]
        if ts_to is not None:
            events = [e for e in events if (e.get("ts") or 0) <= ts_to]

        filtered = bool(ip_filter or ref_filter or ts_from is not None or ts_to is not None)
        events = events[-1000:] if filtered else events[-300:]
        events.reverse()
        return {"status": True, "events": events, "count": len(events)}

    # ---- load balancer ----

    def CheckBackendHealth(self, get):
        domain = get.domain.strip() if ('domain' in get and get.domain.strip()) else ""
        cfg = self._get_config()
        site = next((s for s in cfg.get("sites", []) if s["domain"] == domain), None)
        if not site or site.get("mode") != "waf_proxy":
            return public.ReturnMsg(False, self._t("domain_not_found_or_not_lb"))

        path = site.get("health_uri") or "/"
        results = []
        for b in site.get("backends", []):
            shell = public.ExecShell(
                "curl -s -o /dev/null -w '%%{http_code}|%%{time_total}' --max-time 3 'http://%s%s'" % (b, path)
            )
            out = (shell[0] or "").strip() if shell else ""
            healthy = False
            code = 0
            time_ms = None
            try:
                code_s, t_s = out.split("|")
                code = int(code_s)
                time_ms = round(float(t_s) * 1000)
                healthy = 200 <= code < 400
            except:
                pass
            results.append({"backend": b, "healthy": healthy, "code": code, "time_ms": time_ms})

        return {"status": True, "path": path, "results": results}

    # ---- CC defense (deteksi flood berbasis scan access log, karena Coraza tidak
    # dukung collection IP/persisten untuk rate-limit asli - lihat catatan _waf_block) &
    # WAF Auto-Block (deteksi IP yang berkali-kali melanggar rule WAF, terlepas dari
    # volume request mentahnya - menangkap serangan low-and-slow yang lolos dari CC Defense) ----

    def _scan_cc_for_site(self, site):
        """Scan access log domain ini, hitung request/IP dalam window cc_window detik terakhir.
        Return list IP baru yang melebihi cc_threshold (exclude yang sudah whitelist/auto-blacklist)."""
        if not site.get("cc_enabled"):
            return []
        domain = site["domain"]
        window = site.get("cc_window", 60)
        threshold = site.get("cc_threshold", 300)
        logfile = "%s/logs/access-%s.log" % (self.__install_dir, domain)
        if not os.path.exists(logfile):
            return []
        shell = public.ExecShell("tail -n 20000 '%s'" % logfile)
        lines = (shell[0] or "").splitlines() if shell else []
        now = time.time()
        counts = {}
        for line in lines:
            try:
                obj = json.loads(line)
            except:
                continue
            ts = obj.get("ts")
            if ts is None or (now - ts) > window or (now - ts) < 0:
                continue
            ip = ((obj.get("request") or {}).get("client_ip") or "")
            if not ip:
                continue
            counts[ip] = counts.get(ip, 0) + 1
        skip = set(site.get("waf_whitelist", [])) | set(site.get("waf_blacklist_auto", []))
        return [ip for ip, c in counts.items() if c >= threshold and ip not in skip]

    def _scan_waf_autoblock_for_site(self, site):
        """Scan event pelanggaran WAF domain ini (via _get_waf_events), hitung pelanggaran/IP
        dalam window waf_autoblock_window menit terakhir. Return list IP baru yang melebihi
        waf_autoblock_threshold (exclude yang sudah whitelist/auto-blacklist). Beda dengan CC
        Defense: ini menghitung PELANGGARAN RULE WAF, bukan volume request mentah - jadi bisa
        menangkap serangan berulang yang volumenya terlalu kecil untuk kena threshold CC Defense."""
        if not site.get("waf_autoblock_enabled") or site.get("mode") not in ("waf_php", "waf_proxy"):
            return []
        domain = site["domain"]
        window_min = site.get("waf_autoblock_window", 10)
        threshold = site.get("waf_autoblock_threshold", 5)
        events = self._get_waf_events(domain)
        now = time.time()
        since = now - window_min * 60
        counts = {}
        for e in events:
            ts = e.get("ts")
            if ts is None or ts < since:
                continue
            ip = e.get("client_ip", "")
            if not ip:
                continue
            counts[ip] = counts.get(ip, 0) + 1
        skip = set(site.get("waf_whitelist", [])) | set(site.get("waf_blacklist_auto", []))
        return [ip for ip, c in counts.items() if c >= threshold and ip not in skip]

    def ScanCC(self, get):
        """Trigger scan manual untuk satu domain (dipanggil dari tombol UI) - jalankan kedua
        mekanisme deteksi: CC Defense (flood volume request) dan WAF Auto-Block (pelanggaran
        WAF berulang), lalu gabungkan hasilnya ke blacklist otomatis."""
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        domain = get.domain.strip() if ('domain' in get and get.domain.strip()) else ""
        cfg = self._get_config()
        sites = cfg.get("sites", [])
        idx = next((i for i, s in enumerate(sites) if s["domain"] == domain), None)
        if idx is None:
            return public.ReturnMsg(False, self._t("domain_not_found", domain=domain))
        site = sites[idx]
        if not site.get("cc_enabled") and not site.get("waf_autoblock_enabled"):
            return public.ReturnMsg(False, self._t("cc_waf_autoblock_not_enabled"))

        cc_offenders = self._scan_cc_for_site(site)
        waf_offenders = self._scan_waf_autoblock_for_site(site)
        offenders = sorted(set(cc_offenders) | set(waf_offenders))
        if not offenders:
            return {"status": True, "msg": self._t("no_ip_over_threshold"), "offenders": []}

        new_site = dict(site)
        new_site["waf_blacklist_auto"] = sorted(set(site.get("waf_blacklist_auto", [])) | set(offenders))
        new_site["waf_blacklist"] = sorted(set(site.get("waf_blacklist_manual", [])) | set(new_site["waf_blacklist_auto"]))
        candidate_sites = list(sites)
        candidate_sites[idx] = new_site
        ok, err = self._apply_caddyfile(candidate_sites, cfg.get("port", 8080), cfg.get("root"))
        if not ok:
            return public.ReturnMsg(False, err)
        cfg["sites"] = candidate_sites
        public.WriteFile(self.__config_file, json.dumps(cfg))

        parts = []
        if cc_offenders:
            parts.append("%d IP karena flood (>= %s request/%ss)" % (len(cc_offenders), site.get("cc_threshold", 300), site.get("cc_window", 60)))
        if waf_offenders:
            parts.append("%d IP karena serangan WAF berulang (>= %s pelanggaran/%smenit)" % (len(waf_offenders), site.get("waf_autoblock_threshold", 5), site.get("waf_autoblock_window", 10)))
        return {
            "status": True,
            "msg": self._t("ip_auto_blocked", count=len(offenders), detail="; ".join(parts)),
            "offenders": offenders,
        }

    def ScanAllCC(self):
        """Scan semua domain yang mengaktifkan cc_enabled dan/atau waf_autoblock_enabled.
        Dipanggil dari systemd timer, bukan AJAX (tanpa param get)."""
        cfg = self._get_config()
        sites = cfg.get("sites", [])
        candidate_sites = []
        changed = False
        for site in sites:
            if site.get("cc_enabled") or site.get("waf_autoblock_enabled"):
                offenders = set(self._scan_cc_for_site(site)) | set(self._scan_waf_autoblock_for_site(site))
                if offenders:
                    site = dict(site)
                    site["waf_blacklist_auto"] = sorted(set(site.get("waf_blacklist_auto", [])) | offenders)
                    site["waf_blacklist"] = sorted(set(site.get("waf_blacklist_manual", [])) | set(site["waf_blacklist_auto"]))
                    changed = True
            candidate_sites.append(site)
        if not changed:
            return True
        ok, err = self._apply_caddyfile(candidate_sites, cfg.get("port", 8080), cfg.get("root"))
        if not ok:
            return False
        cfg["sites"] = candidate_sites
        public.WriteFile(self.__config_file, json.dumps(cfg))
        return True

    def ClearCCBlacklist(self, get):
        """Bersihkan IP hasil auto-block CC Defense untuk satu domain (blacklist manual tetap dipertahankan)."""
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        domain = get.domain.strip() if ('domain' in get and get.domain.strip()) else ""
        cfg = self._get_config()
        sites = cfg.get("sites", [])
        idx = next((i for i, s in enumerate(sites) if s["domain"] == domain), None)
        if idx is None:
            return public.ReturnMsg(False, self._t("domain_not_found", domain=domain))
        site = sites[idx]
        if not site.get("waf_blacklist_auto"):
            return {"status": True, "msg": self._t("no_autoblock_to_clear")}

        new_site = dict(site)
        cleared_count = len(site.get("waf_blacklist_auto", []))
        new_site["waf_blacklist_auto"] = []
        new_site["waf_blacklist"] = sorted(set(site.get("waf_blacklist_manual", [])))
        candidate_sites = list(sites)
        candidate_sites[idx] = new_site
        ok, err = self._apply_caddyfile(candidate_sites, cfg.get("port", 8080), cfg.get("root"))
        if not ok:
            return public.ReturnMsg(False, err)
        cfg["sites"] = candidate_sites
        public.WriteFile(self.__config_file, json.dumps(cfg))
        return {"status": True, "msg": self._t("autoblock_cleared", count=cleared_count)}

    # ---- statistik website (collector: access log -> SQLite, incremental) ----

    def _stats_ua_category(self, ua):
        if not ua:
            return "Unknown"
        u = ua.lower()
        if 'googlebot' in u:
            return 'Googlebot'
        if 'bingbot' in u:
            return 'Bingbot'
        if re.search(r'bot|crawler|spider|slurp|monitor|uptime|pingdom|ahrefs|semrush|facebookexternalhit', u):
            return 'Bot/Crawler lain'
        if 'curl/' in u or 'wget/' in u or 'python-requests' in u or 'okhttp' in u or 'go-http-client' in u:
            return 'Script/CLI'
        if 'edg/' in u:
            return 'Edge'
        if 'opr/' in u or ' opera' in u:
            return 'Opera'
        if 'chrome/' in u:
            return 'Chrome'
        if 'firefox/' in u:
            return 'Firefox'
        if 'safari/' in u:
            return 'Safari'
        return 'Lainnya'

    def _stats_duration_bucket(self, d):
        if d < 0.1:
            return '<100ms'
        if d < 0.3:
            return '100-300ms'
        if d < 1.0:
            return '300ms-1s'
        if d < 3.0:
            return '1-3s'
        return '>3s'

    def _collect_stats_for_domain(self, conn, domain):
        """Parse baris BARU (dari byte_offset terakhir) di access log domain ini, agregasi ke
        SQLite. Rotation-aware: kalau inode berubah atau ukuran file < offset tersimpan
        (logrotate copytruncate), mulai baca dari awal file baru."""
        logfile = "%s/logs/access-%s.log" % (self.__install_dir, domain)
        if not os.path.exists(logfile):
            return 0
        st = os.stat(logfile)
        row = conn.execute("SELECT file_inode, byte_offset FROM log_offsets WHERE domain=?", (domain,)).fetchone()
        offset = 0
        if row and row[0] == st.st_ino and row[1] <= st.st_size:
            offset = row[1]

        hourly = {}
        dayips = set()
        dims = {}
        buckets = {}
        request_rows = []
        processed = 0
        new_offset = offset

        with open(logfile, 'r', errors='replace') as f:
            f.seek(offset)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except:
                    continue
                if obj.get('msg') != 'handled request':
                    continue
                ts = obj.get('ts')
                if ts is None:
                    continue
                req = obj.get('request') or {}
                ip = req.get('client_ip') or ''
                method = req.get('method') or '-'
                uri = (req.get('uri') or '/').split('?')[0][:300]
                proto = req.get('proto') or '-'
                tls = req.get('tls') or {}
                tls_ver = {769: 'TLS1.0', 770: 'TLS1.1', 771: 'TLS1.2', 772: 'TLS1.3'}.get(tls.get('version'), '') if tls else ''
                headers = req.get('headers') or {}
                ua = (headers.get('User-Agent') or headers.get('user-agent') or [''])[0]
                ref = (headers.get('Referer') or headers.get('referer') or [''])[0]
                status = obj.get('status') or 0
                size = obj.get('size') or 0
                duration = obj.get('duration') or 0

                hour_ts = int(ts // 3600) * 3600
                day = time.strftime('%Y-%m-%d', time.gmtime(ts))

                h = hourly.setdefault(hour_ts, {'requests': 0, 'bytes_total': 0, 'duration_sum': 0.0, 'duration_count': 0, 'status_2xx': 0, 'status_3xx': 0, 'status_4xx': 0, 'status_5xx': 0})
                h['requests'] += 1
                h['bytes_total'] += size
                h['duration_sum'] += duration
                h['duration_count'] += 1
                if 200 <= status < 300:
                    h['status_2xx'] += 1
                elif 300 <= status < 400:
                    h['status_3xx'] += 1
                elif 400 <= status < 500:
                    h['status_4xx'] += 1
                elif status >= 500:
                    h['status_5xx'] += 1

                if ip:
                    dayips.add((day, ip))

                def bump(dim, value):
                    if not value:
                        return
                    key = (day, dim, value[:300])
                    dims[key] = dims.get(key, 0) + 1
                bump('uri', uri)
                bump('referrer', ref if ref else '(langsung)')
                bump('method', method)
                bump('protocol', proto)
                if tls_ver:
                    bump('tls_version', tls_ver)
                bump('ua_category', self._stats_ua_category(ua))
                bump('status_code', str(status))

                bkey = (day, self._stats_duration_bucket(duration))
                buckets[bkey] = buckets.get(bkey, 0) + 1

                full_uri = (req.get('uri') or '/')[:500]
                request_rows.append((domain, ts, ip, method, full_uri, status, size, duration, ua[:300], ref[:300]))

                processed += 1
            new_offset = f.tell()

        if processed:
            cur = conn.cursor()
            for hour_ts, h in hourly.items():
                cur.execute(
                    "INSERT INTO hourly_stats (domain,hour_ts,requests,bytes_total,duration_sum,duration_count,status_2xx,status_3xx,status_4xx,status_5xx) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(domain,hour_ts) DO UPDATE SET "
                    "requests=requests+excluded.requests, bytes_total=bytes_total+excluded.bytes_total, "
                    "duration_sum=duration_sum+excluded.duration_sum, duration_count=duration_count+excluded.duration_count, "
                    "status_2xx=status_2xx+excluded.status_2xx, status_3xx=status_3xx+excluded.status_3xx, "
                    "status_4xx=status_4xx+excluded.status_4xx, status_5xx=status_5xx+excluded.status_5xx",
                    (domain, hour_ts, h['requests'], h['bytes_total'], h['duration_sum'], h['duration_count'], h['status_2xx'], h['status_3xx'], h['status_4xx'], h['status_5xx'])
                )
            for (day, ip) in dayips:
                cur.execute("INSERT OR IGNORE INTO daily_ips (domain,day,ip) VALUES (?,?,?)", (domain, day, ip))
            for (day, dim, value), c in dims.items():
                cur.execute(
                    "INSERT INTO daily_dim_counts (domain,day,dim,value,count) VALUES (?,?,?,?,?) "
                    "ON CONFLICT(domain,day,dim,value) DO UPDATE SET count=count+excluded.count",
                    (domain, day, dim, value, c)
                )
            for (day, bucket), c in buckets.items():
                cur.execute(
                    "INSERT INTO response_time_buckets (domain,day,bucket,count) VALUES (?,?,?,?) "
                    "ON CONFLICT(domain,day,bucket) DO UPDATE SET count=count+excluded.count",
                    (domain, day, bucket, c)
                )
            cur.executemany(
                "INSERT INTO request_log (domain,ts,client_ip,method,uri,status,size,duration,user_agent,referer) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                request_rows
            )
            cutoff = time.time() - self.__request_log_retention_days * 86400
            conn.execute("DELETE FROM request_log WHERE domain=? AND ts < ?", (domain, cutoff))

        conn.execute(
            "INSERT INTO log_offsets (domain,file_inode,byte_offset) VALUES (?,?,?) "
            "ON CONFLICT(domain) DO UPDATE SET file_inode=excluded.file_inode, byte_offset=excluded.byte_offset",
            (domain, st.st_ino, new_offset)
        )
        conn.commit()
        return processed

    def _collect_waf_events_to_db(self, conn):
        """Simpan event WAF (dari journalctl, jendela terbatas & bisa hilang saat journal
        di-vacuum systemd) secara permanen ke SQLite, dengan negara asal IP (GeoIP) di-attach.
        Dedup via unique_id (PRIMARY KEY) - aman dipanggil berulang, event lama tidak dobel."""
        events = self._get_waf_events(None)
        if not events:
            return 0
        country_cache = {}
        batch = []
        for e in events:
            uid = e.get("unique_id") or ""
            if not uid:
                continue
            ip = e.get("client_ip", "")
            if ip not in country_cache:
                country_cache[ip] = self._geoip_country(conn, ip)
            batch.append((
                uid, e.get("ts") or 0, e.get("domain", ""), ip, country_cache[ip],
                e.get("uri", ""), e.get("category", ""), e.get("rule_id", ""),
                e.get("message", ""), e.get("severity", ""), e.get("score", "")
            ))
        if not batch:
            return 0
        cur = conn.cursor()
        cur.executemany(
            "INSERT OR IGNORE INTO waf_events (unique_id,ts,domain,client_ip,country,uri,category,rule_id,message,severity,score) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            batch
        )
        conn.commit()
        return cur.rowcount

    def CollectStats(self, get):
        """Trigger koleksi statistik manual (tombol UI) untuk semua domain, plus simpan event WAF ke SQLite."""
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        cfg = self._get_config()
        domains = [s["domain"] for s in cfg.get("sites", [])]
        conn = self._stats_db()
        total = 0
        try:
            for d in domains:
                total += self._collect_stats_for_domain(conn, d)
            self._collect_waf_events_to_db(conn)
        finally:
            conn.close()
        return {"status": True, "msg": self._t("log_lines_processed", count=total), "processed": total}

    def CollectAllStats(self):
        """Dipanggil dari systemd timer frankenphp-statscollect - tanpa param get."""
        cfg = self._get_config()
        domains = [s["domain"] for s in cfg.get("sites", [])]
        conn = self._stats_db()
        try:
            for d in domains:
                self._collect_stats_for_domain(conn, d)
            self._collect_waf_events_to_db(conn)
        finally:
            conn.close()
        return True

    def _apply_stats_timer(self, interval_minutes):
        """Tulis ulang systemd timer frankenphp-statscollect dengan interval baru, reload, restart."""
        svc_dir = "/usr/lib/systemd/system" if os.path.isdir("/usr/lib/systemd/system") else "/lib/systemd/system"
        service_content = (
            "[Unit]\n"
            "Description=FrankenPHP Stats Collector\n"
            "After=frankenphp.service\n\n"
            "[Service]\n"
            "Type=oneshot\n"
            "User=root\n"
            "ExecStart=/www/server/panel/pyenv/bin/python3 %s/stats_collect.py\n"
        ) % self.__install_dir
        timer_content = (
            "[Unit]\n"
            "Description=Jalankan FrankenPHP Stats Collector periodik\n\n"
            "[Timer]\n"
            "OnBootSec=%smin\n"
            "OnUnitActiveSec=%smin\n\n"
            "[Install]\n"
            "WantedBy=timers.target\n"
        ) % (interval_minutes, interval_minutes)
        public.WriteFile(svc_dir + "/" + self.__stats_service + ".service", service_content)
        public.WriteFile(svc_dir + "/" + self.__stats_service + ".timer", timer_content)
        public.ExecShell("systemctl daemon-reload")
        public.ExecShell("systemctl enable --now %s.timer" % self.__stats_service)
        public.ExecShell("systemctl restart %s.timer" % self.__stats_service)

    def SetStatsInterval(self, get):
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        try:
            minutes = int(get.minutes) if ('minutes' in get and str(get.minutes).strip()) else 5
        except:
            return public.ReturnMsg(False, self._t("interval_must_be_number"))
        if minutes not in self.__stats_intervals:
            return public.ReturnMsg(False, self._t("interval_unknown", value=str(minutes)))
        cfg = self._get_config()
        cfg["stats_scan_minutes"] = minutes
        public.WriteFile(self.__config_file, json.dumps(cfg))
        self._apply_stats_timer(minutes)
        result = self.GetServerStatus(get)
        result["msg"] = "Interval scan statistik diubah ke %s menit" % minutes
        result["status"] = True
        return result

    # ---- overview dashboard ----

    def GetSystemInfo(self, get):
        cpu = self._cpu_percent()

        mem_total = mem_avail = 0
        try:
            info = {}
            with open('/proc/meminfo') as f:
                for line in f:
                    parts = line.split(':')
                    if len(parts) == 2:
                        info[parts[0].strip()] = parts[1].strip()
            mem_total = int(info.get('MemTotal', '0 kB').split()[0])
            mem_avail = int(info.get('MemAvailable', '0 kB').split()[0])
        except:
            pass
        mem_used = max(mem_total - mem_avail, 0)
        mem_percent = round(mem_used / mem_total * 100, 1) if mem_total else 0

        disk_total = disk_used = disk_percent = 0
        try:
            st = os.statvfs(self.__install_dir)
            disk_total = st.f_blocks * st.f_frsize
            disk_free = st.f_bavail * st.f_frsize
            disk_used = disk_total - disk_free
            disk_percent = round(disk_used / disk_total * 100, 1) if disk_total else 0
        except:
            pass

        load1 = load5 = load15 = 0.0
        try:
            with open('/proc/loadavg') as f:
                parts = f.readline().split()
                load1, load5, load15 = float(parts[0]), float(parts[1]), float(parts[2])
        except:
            pass

        return {
            "status": True,
            "cpu_percent": cpu,
            "mem_total_kb": mem_total,
            "mem_used_kb": mem_used,
            "mem_percent": mem_percent,
            "disk_total_bytes": disk_total,
            "disk_used_bytes": disk_used,
            "disk_percent": disk_percent,
            "load1": load1,
            "load5": load5,
            "load15": load15,
        }

    def GetOverviewStats(self, get):
        """Agregat lintas domain untuk dashboard Ringkasan: total request 24 jam, request
        ternoda (malicious) 24 jam, trend per jam, top attacker IP, log intersepsi terbaru."""
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        cfg = self._get_config()
        sites = cfg.get("sites", [])
        domains = [s["domain"] for s in sites]

        now = time.time()
        since = now - 86400

        total_requests = 0
        trend_buckets = [0] * 24
        for d in domains:
            logfile = "%s/logs/access-%s.log" % (self.__install_dir, d)
            if not os.path.exists(logfile):
                continue
            shell = public.ExecShell("tail -n 20000 '%s'" % logfile)
            lines = (shell[0] or "").splitlines() if shell else []
            for line in lines:
                try:
                    obj = json.loads(line)
                except:
                    continue
                ts = obj.get("ts")
                if ts is None or ts < since:
                    continue
                total_requests += 1
                bucket = int((now - ts) // 3600)
                if 0 <= bucket < 24:
                    trend_buckets[23 - bucket] += 1

        events = self._get_waf_events(None)
        events_24h = [e for e in events if e.get("ts") and e["ts"] >= since]

        attacker_counts = {}
        for e in events_24h:
            ip = e.get("client_ip", "")
            if not ip:
                continue
            attacker_counts[ip] = attacker_counts.get(ip, 0) + 1
        top_attackers = sorted(attacker_counts.items(), key=lambda kv: -kv[1])[:10]
        top_attackers = [{"ip": ip, "count": c} for ip, c in top_attackers]

        recent = sorted(events_24h, key=lambda e: e.get("ts") or 0, reverse=True)[:50]

        return {
            "status": True,
            "domain_count": len(domains),
            "total_requests_24h": total_requests,
            "malicious_24h": len(events_24h),
            "trend": trend_buckets,
            "top_attackers": top_attackers,
            "recent_events": recent,
        }

    # ---- statistik website (query dari SQLite yang diisi collector) ----

    def GetWebStats(self, get):
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        domain = get.domain.strip() if ('domain' in get and get.domain.strip()) else "all"
        rng = get.range.strip() if ('range' in get and get.range.strip()) else "today"
        if rng not in ("today", "7d", "30d", "all"):
            rng = "today"

        conn = self._stats_db()
        try:
            now = time.time()
            today = time.strftime('%Y-%m-%d', time.gmtime(now))
            dom_filter = "" if domain == "all" else " AND domain=?"
            dom_args = [] if domain == "all" else [domain]

            if rng == "today":
                since_ts = int(now // 86400) * 86400
                rows = conn.execute(
                    "SELECT hour_ts, SUM(requests), SUM(bytes_total) FROM hourly_stats "
                    "WHERE hour_ts >= ?" + dom_filter + " GROUP BY hour_ts ORDER BY hour_ts",
                    [since_ts] + dom_args
                ).fetchall()
                trend = [{"label": time.strftime('%H:%M', time.gmtime(r[0])), "requests": r[1] or 0, "bytes": r[2] or 0} for r in rows]
                since_day = today
                agg_where = "hour_ts >= ?"
                agg_arg = since_ts
            else:
                days_back = {"7d": 6, "30d": 29, "all": 3650}[rng]
                since_day = time.strftime('%Y-%m-%d', time.gmtime(now - days_back * 86400))
                rows = conn.execute(
                    "SELECT strftime('%Y-%m-%d', hour_ts, 'unixepoch') AS d, SUM(requests), SUM(bytes_total) FROM hourly_stats "
                    "WHERE strftime('%Y-%m-%d', hour_ts, 'unixepoch') >= ?" + dom_filter + " GROUP BY d ORDER BY d",
                    [since_day] + dom_args
                ).fetchall()
                trend = [{"label": r[0], "requests": r[1] or 0, "bytes": r[2] or 0} for r in rows]
                agg_where = "strftime('%Y-%m-%d', hour_ts, 'unixepoch') >= ?"
                agg_arg = since_day

            agg = conn.execute(
                "SELECT SUM(requests), SUM(bytes_total), SUM(duration_sum), SUM(duration_count), "
                "SUM(status_2xx), SUM(status_3xx), SUM(status_4xx), SUM(status_5xx) FROM hourly_stats "
                "WHERE " + agg_where + dom_filter,
                [agg_arg] + dom_args
            ).fetchone()
            total_requests = agg[0] or 0
            total_bytes = agg[1] or 0
            dur_sum = agg[2] or 0
            dur_count = agg[3] or 0
            avg_duration = (dur_sum / dur_count) if dur_count else 0
            s2, s3, s4, s5 = (agg[4] or 0, agg[5] or 0, agg[6] or 0, agg[7] or 0)

            uip_row = conn.execute(
                "SELECT COUNT(DISTINCT ip) FROM daily_ips WHERE day >= ?" + dom_filter,
                [since_day] + dom_args
            ).fetchone()
            unique_ips = uip_row[0] or 0

            def top_dim(dim, limit=10):
                rows = conn.execute(
                    "SELECT value, SUM(count) c FROM daily_dim_counts WHERE day >= ? AND dim=?" + dom_filter +
                    " GROUP BY value ORDER BY c DESC LIMIT ?",
                    [since_day, dim] + dom_args + [limit]
                ).fetchall()
                return [{"value": r[0], "count": r[1]} for r in rows]

            bucket_order = ['<100ms', '100-300ms', '300ms-1s', '1-3s', '>3s']
            rows = conn.execute(
                "SELECT bucket, SUM(count) c FROM response_time_buckets WHERE day >= ?" + dom_filter + " GROUP BY bucket",
                [since_day] + dom_args
            ).fetchall()
            bucket_counts = {r[0]: r[1] for r in rows}
            total_bucketed = sum(bucket_counts.values())
            p95_bucket = None
            cum = 0
            for b in bucket_order:
                cum += bucket_counts.get(b, 0)
                if total_bucketed and cum / total_bucketed >= 0.95:
                    p95_bucket = b
                    break

            return {
                "status": True,
                "domain": domain,
                "range": rng,
                "total_requests": total_requests,
                "total_bytes": total_bytes,
                "avg_duration_ms": round(avg_duration * 1000, 1),
                "unique_ips": unique_ips,
                "status_2xx": s2, "status_3xx": s3, "status_4xx": s4, "status_5xx": s5,
                "error_rate_pct": round((s4 + s5) / total_requests * 100, 1) if total_requests else 0,
                "trend": trend,
                "top_uri": top_dim("uri"),
                "top_referrer": top_dim("referrer"),
                "method_breakdown": top_dim("method"),
                "protocol_breakdown": top_dim("protocol"),
                "tls_breakdown": top_dim("tls_version"),
                "ua_breakdown": top_dim("ua_category"),
                "response_time_buckets": [{"bucket": b, "count": bucket_counts.get(b, 0)} for b in bucket_order],
                "p95_bucket": p95_bucket,
            }
        finally:
            conn.close()

    def GetAttacksByCountry(self, get):
        """Agregat serangan (event WAF tersimpan) per negara asal IP (GeoIP), untuk peta
        serangan di Dashboard. Data DB-IP (CC BY 4.0) - lihat atribusi di frontend."""
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        domain = get.domain.strip() if ('domain' in get and get.domain.strip()) else "all"
        rng = get.range.strip() if ('range' in get and get.range.strip()) else "7d"
        if rng not in ("today", "7d", "30d", "all"):
            rng = "7d"

        conn = self._stats_db()
        try:
            now = time.time()
            if rng == "today":
                since = int(now // 86400) * 86400
            elif rng == "7d":
                since = now - 7 * 86400
            elif rng == "30d":
                since = now - 30 * 86400
            else:
                since = 0

            dom_filter = "" if domain == "all" else " AND domain=?"
            dom_args = [] if domain == "all" else [domain]

            rows = conn.execute(
                "SELECT country, COUNT(*) c FROM waf_events WHERE ts >= ?" + dom_filter + " AND country IS NOT NULL GROUP BY country ORDER BY c DESC",
                [since] + dom_args
            ).fetchall()
            total = sum(r[1] for r in rows)

            countries = []
            for country, count in rows:
                top_ip_row = conn.execute(
                    "SELECT client_ip, COUNT(*) c FROM waf_events WHERE ts >= ? AND country=?" + dom_filter + " GROUP BY client_ip ORDER BY c DESC LIMIT 1",
                    [since, country] + dom_args
                ).fetchone()
                countries.append({
                    "country": country,
                    "count": count,
                    "pct": round(count / total * 100, 1) if total else 0,
                    "top_ip": top_ip_row[0] if top_ip_row else None,
                    "top_ip_count": top_ip_row[1] if top_ip_row else 0,
                })

            unknown_row = conn.execute(
                "SELECT COUNT(*) FROM waf_events WHERE ts >= ?" + dom_filter + " AND country IS NULL",
                [since] + dom_args
            ).fetchone()
            unknown_count = unknown_row[0] or 0

            return {
                "status": True,
                "domain": domain,
                "range": rng,
                "total_attacks": total + unknown_count,
                "countries": countries,
                "unknown_count": unknown_count,
            }
        finally:
            conn.close()

    def GetRequestLog(self, get):
        """Daftar request mentah (drill-down dari tabel Status Code di tab Statistik).
        Sumber tabel request_log - retensi 30 hari (lihat __request_log_retention_days),
        beda dari data agregat lain yang tak terbatas."""
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        domain = get.domain.strip() if ('domain' in get and get.domain.strip()) else "all"
        rng = get.range.strip() if ('range' in get and get.range.strip()) else "today"
        if rng not in ("today", "7d", "30d", "all"):
            rng = "today"
        status_filter = get.status_filter.strip() if ('status_filter' in get and get.status_filter.strip()) else "all"
        if status_filter not in ("2xx", "3xx", "4xx", "5xx", "all"):
            status_filter = "all"
        try:
            offset = max(0, int(get.offset)) if ('offset' in get and str(get.offset).strip()) else 0
        except:
            offset = 0
        limit = 50

        conn = self._stats_db()
        try:
            now = time.time()
            if rng == "today":
                since = int(now // 86400) * 86400
            elif rng == "7d":
                since = now - 7 * 86400
            elif rng == "30d":
                since = now - 30 * 86400
            else:
                since = 0

            where = ["ts >= ?"]
            args = [since]
            if domain != "all":
                where.append("domain=?")
                args.append(domain)
            if status_filter != "all":
                lo = {"2xx": 200, "3xx": 300, "4xx": 400, "5xx": 500}[status_filter]
                where.append("status >= ? AND status < ?")
                args.extend([lo, lo + 100])
            where_sql = " AND ".join(where)

            total = conn.execute("SELECT COUNT(*) FROM request_log WHERE " + where_sql, args).fetchone()[0]
            rows = conn.execute(
                "SELECT domain, ts, client_ip, method, uri, status, size, duration FROM request_log WHERE " + where_sql +
                " ORDER BY ts DESC LIMIT ? OFFSET ?",
                args + [limit, offset]
            ).fetchall()

            requests = [{
                "domain": r[0], "ts": r[1], "client_ip": r[2], "method": r[3], "uri": r[4],
                "status": r[5], "size": r[6], "duration_ms": round((r[7] or 0) * 1000, 1),
            } for r in rows]

            return {
                "status": True,
                "domain": domain,
                "range": rng,
                "status_filter": status_filter,
                "total": total,
                "offset": offset,
                "limit": limit,
                "requests": requests,
            }
        finally:
            conn.close()

    # ---- config PHP runtime FrankenPHP (php.ini di install_dir - PHP embedded, BUKAN PHP CLI aapanel) ----

    __php_ini_file = __install_dir + "/php.ini"
    __php_config_keys = ("memory_limit", "upload_max_filesize", "post_max_size", "max_execution_time", "max_input_time", "date.timezone", "display_errors")

    def _php_runtime_ini_get(self, keys):
        """Query nilai ini directive yg AKTIF di PHP embedded FrankenPHP (gabungan default bawaan +
        override php.ini), pakai binary asli via subcommand 'php-cli' - lebih akurat drpd parsing
        teks php.ini sendiri (yg mungkin tidak menyebut directive kalau masih default)."""
        expr = ".'|'.".join("ini_get('%s')" % k for k in keys)
        shell = public.ExecShell(
            "HOME=%s XDG_DATA_HOME=%s/.local/share XDG_CONFIG_HOME=%s/.config PHPRC=%s %s php-cli -r \"echo %s;\"" % (
                self.__install_dir + "/home", self.__install_dir + "/home", self.__install_dir + "/home",
                self.__install_dir, self.__bin, expr
            )
        )
        out = (shell[0] or "").strip() if shell else ""
        parts = out.split("|")
        if len(parts) != len(keys):
            return {}
        return dict(zip(keys, parts))

    def GetPhpConfig(self, get):
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))
        values = self._php_runtime_ini_get(self.__php_config_keys)
        if not values:
            return public.ReturnMsg(False, self._t("php_config_read_failed"))
        return {"status": True, "config": values}

    def SetPhpConfig(self, get):
        """Update php.ini runtime FrankenPHP (bukan PHP CLI aapanel - itu instalasi terpisah, tidak
        dikelola plugin ini). Restart service supaya PHP embedded baca ulang php.ini (tidak ada
        hot-reload utk ini directive semacam ini)."""
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))

        def get_val(key):
            return get[key].strip() if (key in get and get[key].strip()) else None

        updates = {}

        mem = get_val('memory_limit')
        if mem is not None:
            if not re.match(r'^-1$|^\d+[KMG]?$', mem, re.I):
                return public.ReturnMsg(False, self._t("memory_limit_invalid"))
            updates['memory_limit'] = mem

        for key in ('upload_max_filesize', 'post_max_size'):
            val = get_val(key)
            if val is not None:
                if not re.match(r'^\d+[KMG]?$', val, re.I):
                    return public.ReturnMsg(False, self._t("size_value_invalid", key=key))
                updates[key] = val

        for key in ('max_execution_time', 'max_input_time'):
            val = get_val(key)
            if val is not None:
                try:
                    n = int(val)
                except:
                    return public.ReturnMsg(False, self._t("seconds_value_invalid", key=key))
                if n < -1 or n > 86400:
                    return public.ReturnMsg(False, self._t("seconds_range_invalid", key=key))
                updates[key] = str(n)

        tz = get_val('date.timezone')
        if tz is not None:
            if not re.match(r'^[A-Za-z_]+(/[A-Za-z_-]+)*$', tz):
                return public.ReturnMsg(False, self._t("timezone_invalid"))
            updates['date.timezone'] = tz

        disp = get_val('display_errors')
        if disp is not None:
            if disp not in ('On', 'Off'):
                return public.ReturnMsg(False, self._t("display_errors_invalid"))
            updates['display_errors'] = disp

        if not updates:
            return public.ReturnMsg(False, self._t("no_changes_submitted"))

        content = public.ReadFile(self.__php_ini_file) or ""
        lines = content.splitlines()
        seen = set()
        new_lines = []
        for line in lines:
            m = re.match(r'^\s*([A-Za-z_.]+)\s*=', line)
            if m and m.group(1) in updates:
                key = m.group(1)
                new_lines.append("%s = %s" % (key, updates[key]))
                seen.add(key)
            else:
                new_lines.append(line)
        for key, val in updates.items():
            if key not in seen:
                new_lines.append("%s = %s" % (key, val))
        public.WriteFile(self.__php_ini_file, "\n".join(new_lines) + "\n")

        public.ExecShell("systemctl restart %s" % self.__service)
        time.sleep(1)

        result = self.GetServerStatus(get)
        result["msg"] = self._t("php_config_saved_restarted")
        result["status"] = True
        return result

    # ---- wrapper CLI global utk PHP embedded FrankenPHP (dipakai artisan/composer dst,
    # extension jauh lebih lengkap drpd PHP CLI aapanel - lihat GetPhpConfig) ----

    __php_cli_wrapper_script = __install_dir + "/bin/php-cli-wrapper.sh"
    __php_cli_wrapper_link = "/usr/bin/php"

    def GetPhpCliWrapperStatus(self, get):
        installed = False
        if os.path.islink(self.__php_cli_wrapper_link):
            try:
                installed = os.readlink(self.__php_cli_wrapper_link) == self.__php_cli_wrapper_script
            except:
                installed = False
        return {"status": True, "installed": installed, "path": self.__php_cli_wrapper_link}

    def SetupPhpCliWrapper(self, get):
        """Arahkan command 'php' sistem (/usr/bin/php) ke PHP EMBEDDED FrankenPHP (extension jauh
        lebih lengkap drpd PHP CLI aapanel bawaan panel: ada pdo_pgsql, redis, intl, bcmath,
        sodium, dll). PERHATIAN: ini mengganti symlink php SISTEM (dipakai composer/artisan/script
        apa pun yang manggil "php") - kalau ada instalasi PHP lain (mis. PHP CLI aapanel) yang
        justru dibutuhkan sbg "php" default, jangan aktifkan ini atau kembalikan manual via
        `ln -sf /path/php/asli /usr/bin/php`."""
        if not self._is_installed():
            return public.ReturnMsg(False, self._t("not_installed"))

        script = (
            "#!/bin/bash\n"
            "export HOME=%s/home\n"
            "export XDG_DATA_HOME=%s/home/.local/share\n"
            "export XDG_CONFIG_HOME=%s/home/.config\n"
            "export PHPRC=%s\n"
            "exec %s php-cli \"$@\"\n"
        ) % (self.__install_dir, self.__install_dir, self.__install_dir, self.__install_dir, self.__bin)
        public.WriteFile(self.__php_cli_wrapper_script, script)
        public.ExecShell("chmod +x '%s'" % self.__php_cli_wrapper_script)
        public.ExecShell("ln -sf '%s' '%s'" % (self.__php_cli_wrapper_script, self.__php_cli_wrapper_link))

        # catatan: subcommand "php-cli" FrankenPHP dirancang utk MENJALANKAN SCRIPT (spt "artisan"),
        # bukan replacement penuh binary php - flag standalone spt -v/-m tidak didukung. Makanya
        # validasi pakai -r (jalankan kode inline), bukan -v.
        shell = public.ExecShell("%s -r \"echo 'PHP ' . PHP_VERSION;\"" % self.__php_cli_wrapper_link)
        out = (shell[0] or "").strip() if shell else ""
        if "PHP" not in out:
            return public.ReturnMsg(False, self._t("wrapper_created_but_failed", detail=(shell[1] or out)))

        return {
            "status": True,
            "msg": self._t("php_cli_wrapper_active"),
            "path": self.__php_cli_wrapper_link,
            "version_output": out,
        }
