#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin
export PATH

install_dir=/www/server/frankenphp
plugin_dir=/www/server/panel/plugin/frankenphp
install_log=/tmp/frankenphp_install.log
# /tmp/panelExec.log adalah file BERSAMA yang dipakai aaPanel sendiri (files.py GetTaskSpeed)
# buat nampilin isi live-log task yang lagi jalan di message box bawaan panel. Sebelumnya kita
# cuma nulis ke $install_log milik plugin sendiri, jadi kalau task LAIN (mis. plugin/software
# lain, termasuk "site_total" bawaan aaPanel) kebetulan barusan nulis ke file yang sama, message
# box nampilin sisa output task itu, bukan punya kita - bukan berarti instalasi FrankenPHP-nya
# ikut kacau (background execution-nya tetap lewat tabel `tasks`, independen), cuma tampilannya
# membingungkan. Nulis rangkap ke sini bikin message box aaPanel ikut nampilin progress kita.
panel_exec_log=/tmp/panelExec.log

log(){ echo "$1" | tee -a "$install_log" "$panel_exec_log" > /dev/null; }

# Jalankan command, log stdout+stderr-nya ke KEDUA file di atas, TAPI tetap propagate exit
# code asli command-nya (bukan exit code `tee`) via PIPESTATUS - supaya `if ! run_logged ...`
# tetap mendeteksi command asli gagal, bukan selalu "berhasil" karena tee sendiri jarang gagal.
run_logged(){
    "$@" 2>&1 | tee -a "$install_log" "$panel_exec_log" > /dev/null
    return "${PIPESTATUS[0]}"
}

Install_frankenphp(){
    release_tag="$1"

    log "Deteksi arsitektur..."
    arch=$(uname -m)
    case "$arch" in
        x86_64)  asset=frankenphp-linux-x86_64 ;;
        aarch64) asset=frankenphp-linux-aarch64 ;;
        *) log "Arsitektur $arch tidak didukung."; exit 1 ;;
    esac

    mkdir -p "$install_dir/bin" "$install_dir/www/public" "$install_dir/logs" "$install_dir/data" "$install_dir/data/geoip" "$install_dir/home"

    log "Download database GeoIP (DB-IP, CC BY 4.0) untuk fitur peta serangan per negara..."
    curl -sL --fail --max-time 120 -o "$install_dir/data/geoip/dbip-country-ipv4.csv" \
        "https://raw.githubusercontent.com/sapics/ip-location-db/main/dbip-country/dbip-country-ipv4.csv" \
        || log "Download GeoIP IPv4 gagal (opsional, tidak menghentikan instalasi) - peta serangan akan kosong sampai file ini tersedia"
    curl -sL --fail --max-time 120 -o "$install_dir/data/geoip/dbip-country-ipv6.csv" \
        "https://raw.githubusercontent.com/sapics/ip-location-db/main/dbip-country/dbip-country-ipv6.csv" \
        || log "Download GeoIP IPv6 gagal (opsional, tidak menghentikan instalasi)"

    if [ -n "$release_tag" ]; then
        log "Download FrankenPHP ($asset) rilis $release_tag dari GitHub..."
        url="https://github.com/php/frankenphp/releases/download/$release_tag/$asset"
    else
        log "Download FrankenPHP ($asset) dari rilis terbaru GitHub..."
        url="https://github.com/php/frankenphp/releases/latest/download/$asset"
    fi
    if ! curl -L --fail --max-time 300 -o "$install_dir/bin/frankenphp" "$url"; then
        log "Download gagal dari $url"
        exit 1
    fi
    if [ ! -s "$install_dir/bin/frankenphp" ]; then
        log "File binary kosong, download gagal."
        exit 1
    fi
    chmod +x "$install_dir/bin/frankenphp"

    ver=$("$install_dir/bin/frankenphp" version 2>/dev/null | head -1)
    log "Binary terpasang: $ver"

    Common_setup
}

# static-php-cli (crazywhalecc/static-php-cli, pinned rilis 2.8.5) - compile PHP+FrankenPHP
# dari source dengan versi PHP & daftar extension bebas sesuai pilihan user. JAUH lebih berat
# dari Install_frankenphp (download binary jadi) - butuh build tools, bisa makan 15-40+ menit,
# CPU/RAM/disk terpakai penuh selama proses.
Build_frankenphp_source(){
    php_version="$1"
    extensions="$2"
    spc_version="${3:-2.8.5}"
    build_dir="$install_dir/build-src"

    if [ -z "$php_version" ] || [ -z "$extensions" ]; then
        log "Versi PHP atau daftar extension kosong, tidak bisa build."
        exit 1
    fi

    log "=== Build custom: PHP $php_version, extensions: $extensions (static-php-cli $spc_version) ==="
    log "Menyiapkan direktori build di $build_dir..."
    rm -rf "$build_dir"
    mkdir -p "$build_dir"
    cd "$build_dir" || { log "Gagal masuk ke $build_dir"; exit 1; }

    # PENTING - pakai toolchain glibc (native gcc host), BUKAN default musl static-php-cli.
    # Root cause: extension swoole SIGSEGV total (ngerusak seluruh proses FrankenPHP, bukan cuma
    # request individual) tepat di swoole_thread_init() - fungsi inti swoole yg selalu dipanggil
    # tiap MINIT, TIDAK terkait fitur --enable-swoole-thread (itu fitur beda, sempat salah duga).
    # SwooleTG itu variabel C++ thread_local, dan musl libc (dipakai spc buat static link)
    # kelihatannya tidak menginisialisasi TLS block dengan benar utk OS thread yg dibuat FrankenPHP
    # sendiri (lewat Go/cgo, bukan pthread_create biasa) - dicek langsung ke source swoole
    # (src/core/base.cc), crash-nya identik & konsisten di titik itu di 2+ percobaan terpisah.
    # glibc (toolchain native host, dynamic link) diharapkan tidak kena masalah TLS yang sama.
    export SPC_LIBC=glibc

    log "Memasang dependency build dasar via apt (bisa beberapa menit)..."
    export DEBIAN_FRONTEND=noninteractive
    run_logged apt-get update -y
    run_logged apt-get install -y build-essential autoconf bison re2c pkg-config libtool cmake git curl unzip xz-utils

    log "Download static-php-cli (spc) $spc_version..."
    if ! curl -L --fail --max-time 120 -o spc.tar.gz \
        "https://github.com/crazywhalecc/static-php-cli/releases/download/$spc_version/spc-linux-x86_64.tar.gz"; then
        log "Download spc gagal - cek apakah versi $spc_version benar-benar dirilis di static-php-cli."
        exit 1
    fi
    tar -xzf spc.tar.gz
    chmod +x spc
    run_logged ./spc --version

    # spc manggil api.github.com puluhan kali (cek rilis tiap source) - tanpa token, limitnya
    # cuma 60 request/jam PER-IP (gampang kena 403, apalagi kalau IP server dipakai bareng),
    # dengan token naik jadi 5000/jam. Token disimpan lewat menu plugin (opsional).
    token_file="$install_dir/data/.github_token"
    if [ -f "$token_file" ]; then
        export GITHUB_TOKEN
        GITHUB_TOKEN=$(cat "$token_file")
        log "GitHub token ditemukan, dipakai untuk menaikkan rate limit API GitHub saat download source."
    else
        log "Tidak ada GitHub token tersimpan - kalau download source gagal karena 403/rate-limit, set token lewat menu plugin lalu coba lagi."
    fi

    log "Cek & pasang dependency tambahan yang diminta spc (spc doctor --auto-fix)..."
    run_logged ./spc doctor --auto-fix

    # SAPI frankenphp butuh toolchain Go + xcaddy buat compile Caddy (dasar FrankenPHP) - kalau
    # belum ada, build gagal telat di awal step compile dgn pesan "requires the go-xcaddy package"
    # (padahal proses download source udah selesai duluan, buang2 waktu). Ini step wajib terpisah
    # dari `spc doctor`, dicek langsung ke urutan resmi static-php-cli sendiri (CraftCommand.php:
    # doctor -> install-pkg go-xcaddy -> download -> build).
    log "Memasang toolchain Go + xcaddy (dibutuhkan buat compile FrankenPHP/Caddy)..."
    if ! run_logged ./spc install-pkg go-xcaddy; then
        log "Gagal memasang go-xcaddy - cek log di atas (biasanya masalah koneksi ke GitHub/Go module proxy)."
        exit 1
    fi

    # PENTING - php-src & frankenphp HARUS disebut eksplisit di argumen "sources" (bukan cuma
    # --for-extensions, yang cuma menghitung source utk extension+lib terpilih, TIDAK termasuk
    # source PHP itu sendiri maupun FrankenPHP) - dicek langsung ke source DownloadCommand.php
    # static-php-cli. Sebelumnya pakai `--all` (download SEMUA ~131 source didukung meski cuma
    # butuh segelintir) - boros bandwidth/disk/RAM, dan terbukti bisa bikin proses ke-OOM-kill
    # di tengah jalan pada VM kecil (curl "client returned ERROR on write" lalu phar spc sendiri
    # korup) - jangan dikembalikan ke --all tanpa alasan kuat.
    log "Download source PHP $php_version + FrankenPHP + extension terpilih (bisa beberapa menit)..."
    if ! run_logged ./spc download php-src,frankenphp --for-extensions="$extensions" --with-php="$php_version"; then
        log "Download source gagal - cek log di atas (bisa karena versi PHP $php_version tidak didukung static-php-cli $spc_version, koneksi ke GitHub, atau resource server - lihat detail error tepat di atas baris ini)."
        exit 1
    fi

    log "Compile PHP $php_version (static, ZTS) + FrankenPHP dengan extension: $extensions ..."
    log "Ini bagian paling lama (15-40+ menit tergantung CPU) - tunggu sampai muncul 'Instalasi selesai' atau pesan gagal."
    # PENTING - static-php-cli TIDAK menyertakan modul Coraza WAF (coraza_waf directive) di
    # build FrankenPHP-nya secara default (cuma frankenphp inti + mercure + vulcain + caddy-
    # cbrotli) - beda dari binary lama yang dipakai plugin ini sebelumnya (yang punya coraza).
    # Tanpa ini, SEMUA domain mode PHP+WAF/WAF+LB gagal disave dengan error persis:
    # "coraza_waf is not a registered directive" - ketauan dari laporan user langsung. Override
    # env var SPC_CMD_VAR_FRANKENPHP_XCADDY_MODULES (dicek di source spc:
    # UnixBuilderBase::buildFrankenphp()) dengan default resminya (config/env.ini) + modul
    # coraza-caddy, exact Go module path dikonfirmasi langsung dari `strings` binary yang
    # sebelumnya sukses pakai coraza (github.com/corazawaf/coraza-caddy/v2).
    export SPC_CMD_VAR_FRANKENPHP_XCADDY_MODULES="--with github.com/dunglas/mercure/caddy --with github.com/dunglas/vulcain/caddy --with github.com/dunglas/caddy-cbrotli --with github.com/corazawaf/coraza-caddy/v2"
    # --with-added-patch (bisa lebih dari satu, spc jalanin semuanya): source php-src baru
    # di-extract SAAT `spc build` jalan (bukan saat `spc download`), jadi patch file source cuma
    # bisa dilakukan lewat hook resmi spc di titik-titik tertentu - lihat isi tiap file patch buat
    # detail bug yang diperbaiki:
    #  - fix_swoole_curl_openssl_tsl.php: swoole+curl gagal compile vs OpenSSL modern (ZTS build)
    #  - fix_swoole_thread_disable.php:   swoole-thread mode bikin FrankenPHP SIGSEGV saat start
    #    (dua sistem sama-sama coba kelola native thread) - dipaksa mati, fitur coroutine/async
    #    swoole biasa (Server, coroutine, channel, dll) tidak kepengaruh sama sekali.
    if ! run_logged ./spc build "$extensions" --build-frankenphp --enable-zts \
        --with-added-patch="$plugin_dir/patches/fix_swoole_curl_openssl_tsl.php" \
        --with-added-patch="$plugin_dir/patches/fix_swoole_thread_disable.php"; then
        log "Build gagal. Cek log di atas untuk detail error dari spc (biasanya kombinasi extension yang bentrok atau dependency C library yang belum lengkap)."
        exit 1
    fi

    if [ ! -s "$build_dir/buildroot/bin/frankenphp" ]; then
        log "Build tampak selesai tapi binary tidak ditemukan di buildroot/bin/frankenphp."
        exit 1
    fi

    mkdir -p "$install_dir/bin"
    cp "$build_dir/buildroot/bin/frankenphp" "$install_dir/bin/frankenphp"
    chmod +x "$install_dir/bin/frankenphp"

    ver=$("$install_dir/bin/frankenphp" version 2>/dev/null | head -1)
    log "Binary hasil build terpasang: $ver"

    log "Membersihkan direktori build sementara ($build_dir, bisa beberapa GB)..."
    cd "$install_dir" || cd /
    rm -rf "$build_dir"

    Common_setup
}

Common_setup(){
    if [ ! -f "$install_dir/config.json" ]; then
        echo '{"port": 8080, "root": "/www/server/frankenphp/www/public"}' > "$install_dir/config.json"
    fi

    if [ ! -f "$install_dir/php.ini" ]; then
        echo 'expose_php = Off' > "$install_dir/php.ini"
    fi

    if [ ! -f "$install_dir/www/public/index.php" ]; then
        cat > "$install_dir/www/public/index.php" <<'PHP'
<?php
echo "<h1>FrankenPHP is running</h1>";
echo "<p>PHP " . PHP_VERSION . " via FrankenPHP</p>";
PHP
    fi

    if [ ! -f "$install_dir/Caddyfile" ]; then
        cat > "$install_dir/Caddyfile" <<EOF
{
	frankenphp
	order php_server before file_server
	admin off
}

:8080 {
	root * $install_dir/www/public
	encode gzip
	php_server
	log {
		output file $install_dir/logs/access.log
	}
}
EOF
    fi

    id www >/dev/null 2>&1 || useradd -M -s /usr/sbin/nologin www
    chown -R www:www "$install_dir"

    log "Membuat script CC Defense..."
    cat > "$install_dir/cc_defense.py" <<'PYEOF'
#!/usr/bin/python
# coding: utf-8
# Dipanggil periodik oleh systemd timer frankenphp-ccdefense.timer.
# Reuse penuh logika frankenphp_main (ScanAllCC) supaya tidak ada duplikasi kode
# yang bisa divergen dari plugin utama.
import sys
sys.path.insert(0, "/www/server/panel/plugin/frankenphp")
from frankenphp_main import frankenphp_main

if __name__ == "__main__":
    frankenphp_main().ScanAllCC()
PYEOF
    chmod +x "$install_dir/cc_defense.py"

    log "Membuat script Stats Collector..."
    cat > "$install_dir/stats_collect.py" <<'PYEOF'
#!/usr/bin/python
# coding: utf-8
# Dipanggil periodik oleh systemd timer frankenphp-statscollect.timer (interval bisa
# diubah lewat tab Pengaturan plugin). Reuse penuh logika frankenphp_main (CollectAllStats).
import sys
sys.path.insert(0, "/www/server/panel/plugin/frankenphp")
from frankenphp_main import frankenphp_main

if __name__ == "__main__":
    frankenphp_main().CollectAllStats()
PYEOF
    chmod +x "$install_dir/stats_collect.py"

    log "Memasang logrotate untuk access log..."
    cat > /etc/logrotate.d/frankenphp <<EOF
$install_dir/logs/access*.log {
	daily
	rotate 14
	missingok
	notifempty
	compress
	delaycompress
	copytruncate
}
EOF

    log "Membuat systemd service..."
    if [ -d /usr/lib/systemd/system ]; then svc_dir=/usr/lib/systemd/system; else svc_dir=/lib/systemd/system; fi
    cat > "$svc_dir/frankenphp.service" <<EOF
[Unit]
Description=FrankenPHP Application Server
After=network.target

[Service]
Type=simple
User=www
Group=www
WorkingDirectory=$install_dir
Environment=HOME=$install_dir/home
Environment=XDG_DATA_HOME=$install_dir/home/.local/share
Environment=XDG_CONFIG_HOME=$install_dir/home/.config
Environment=PHPRC=$install_dir
ExecStart=$install_dir/bin/frankenphp run --config $install_dir/Caddyfile --adapter caddyfile
Restart=on-failure
RestartSec=5
LimitNOFILE=1048576
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF
    log "Membuat systemd timer CC Defense (scan tiap 30 detik)..."
    cat > "$svc_dir/frankenphp-ccdefense.service" <<EOF
[Unit]
Description=FrankenPHP CC Defense scan
After=frankenphp.service

[Service]
Type=oneshot
User=root
ExecStart=/www/server/panel/pyenv/bin/python3 $install_dir/cc_defense.py
EOF
    cat > "$svc_dir/frankenphp-ccdefense.timer" <<EOF
[Unit]
Description=Jalankan FrankenPHP CC Defense scan periodik

[Timer]
OnBootSec=30s
OnUnitActiveSec=30s

[Install]
WantedBy=timers.target
EOF

    log "Membuat systemd timer Stats Collector (default tiap 5 menit, bisa diubah di Pengaturan)..."
    cat > "$svc_dir/frankenphp-statscollect.service" <<EOF
[Unit]
Description=FrankenPHP Stats Collector
After=frankenphp.service

[Service]
Type=oneshot
User=root
ExecStart=/www/server/panel/pyenv/bin/python3 $install_dir/stats_collect.py
EOF
    cat > "$svc_dir/frankenphp-statscollect.timer" <<EOF
[Unit]
Description=Jalankan FrankenPHP Stats Collector periodik

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
EOF

    systemctl daemon-reload
    systemctl enable frankenphp >/dev/null 2>&1
    systemctl start frankenphp
    systemctl enable --now frankenphp-ccdefense.timer >/dev/null 2>&1
    systemctl enable --now frankenphp-statscollect.timer >/dev/null 2>&1
    sleep 1

    if [ -f "$plugin_dir/icon.png" ]; then
        mkdir -p /www/server/panel/BTPanel/static/img/soft_ico
        \cp -a "$plugin_dir/icon.png" /www/server/panel/BTPanel/static/img/soft_ico/ico-frankenphp.png
    fi

    log "Instalasi selesai."
    echo "SUCCESS" >> "$install_log"
}

Uninstall_frankenphp(){
    systemctl stop frankenphp-ccdefense.timer 2>/dev/null
    systemctl disable frankenphp-ccdefense.timer 2>/dev/null
    systemctl stop frankenphp-statscollect.timer 2>/dev/null
    systemctl disable frankenphp-statscollect.timer 2>/dev/null
    systemctl stop frankenphp 2>/dev/null
    systemctl disable frankenphp 2>/dev/null
    rm -f /usr/lib/systemd/system/frankenphp.service /lib/systemd/system/frankenphp.service
    rm -f /usr/lib/systemd/system/frankenphp-ccdefense.service /lib/systemd/system/frankenphp-ccdefense.service
    rm -f /usr/lib/systemd/system/frankenphp-ccdefense.timer /lib/systemd/system/frankenphp-ccdefense.timer
    rm -f /usr/lib/systemd/system/frankenphp-statscollect.service /lib/systemd/system/frankenphp-statscollect.service
    rm -f /usr/lib/systemd/system/frankenphp-statscollect.timer /lib/systemd/system/frankenphp-statscollect.timer
    rm -f /etc/logrotate.d/frankenphp
    systemctl daemon-reload
    rm -rf "$install_dir"
    rm -f /www/server/panel/BTPanel/static/img/soft_ico/ico-frankenphp.png
    log "Uninstalled"
}

action=$1
arg2=$2
if [ "$action" == "install" ]; then
    : > "$install_log"
    : > "$panel_exec_log"
    if [ "$arg2" == "custom" ]; then
        Build_frankenphp_source "$3" "$4" "$5"
    else
        Install_frankenphp "$arg2"
    fi
else
    Uninstall_frankenphp
fi
