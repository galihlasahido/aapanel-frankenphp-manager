<?php
// Dijalankan static-php-cli via --with-added-patch (lihat install.sh, dipasang di spc build).
//
// static-php-cli otomatis nyalain fitur "swoole thread" (--enable-swoole-thread) setiap kali
// build pakai ZTS (lihat src/SPC/builder/extension/swoole.php di static-php-cli - FrankenPHP
// SELALU butuh ZTS buat worker-thread-nya sendiri, jadi ini otomatis kena kalau extension
// swoole dipilih). Masalahnya: fitur ini masih eksperimental di swoole (default OFF kalau user
// build manual), dan bikin FrankenPHP SIGSEGV persis saat inisialisasi PHP worker thread-nya
// sendiri (initPHPThreads -> phpMainThread.start) - dua sistem sama-sama coba kelola native
// thread dan bentrok di level C. Fitur coroutine/async swoole yang biasa dipakai (Server,
// coroutine, channel, dll) TIDAK butuh mode ini - itu jalan lewat coroutine biasa, bukan native
// thread. Jadi aman dipaksa mati.
//
// Mekanisme: config.m4 swoole (ext/swoole/config.m4) nentuin PHP_SWOOLE_THREAD lewat
// PHP_ARG_ENABLE([swoole-thread], ...) yang baca flag --enable-swoole-thread/--disable-swoole-thread
// dari command ./configure. Kita override variabelnya balik ke "no" TEPAT SEBELUM baris yang
// makai (`if test "$PHP_SWOOLE_THREAD" != "no"; then AC_DEFINE(SW_THREAD, ...)`), jadi berapa pun
// flag yang dikirim spc, macro SW_THREAD tetap tidak pernah didefinisikan.
//
// 'before-php-buildconf' = source extension sudah di-extract, tapi `./buildconf --force` (yang
// generate script `configure` dari config.m4) belum jalan - titik paling awal & paling tepat.
//
// DEBUG: tulis ke /tmp/frankenphp_worker_patch_debug.log supaya bisa dicek cepat (tanpa nunggu
// build 30-45 menit penuh) apakah patch ini beneran ke-trigger & match - percobaan sebelumnya
// crash-nya identik persis, dicurigai patch ini silent no-op sama seperti kasus openssl_tsl dulu.
$dbg = fopen('/tmp/frankenphp_worker_patch_debug.log', 'a');
fwrite($dbg, '[' . $this->getPatchPoint() . "] patch script dipanggil\n");
if ($this->getPatchPoint() === 'before-php-buildconf') {
    $file = SOURCE_PATH . '/php-src/ext/swoole/config.m4';
    fwrite($dbg, "before-php-buildconf: cek file $file\n");
    if (file_exists($file)) {
        $content = file_get_contents($file);
        fwrite($dbg, 'file ada, panjang=' . strlen($content) . "\n");
        $needle = 'if test "$PHP_SWOOLE_THREAD" != "no"; then';
        $found = str_contains($content, $needle);
        $already = str_contains($content, 'PHP_SWOOLE_THREAD=no');
        fwrite($dbg, "needle ditemukan=" . ($found ? 'ya' : 'tidak') . ", sudah dipatch sebelumnya=" . ($already ? 'ya' : 'tidak') . "\n");
        if ($found && !$already) {
            $content = str_replace($needle, "PHP_SWOOLE_THREAD=no\n    " . $needle, $content);
            file_put_contents($file, $content);
            fwrite($dbg, "PATCH DITERAPKAN\n");
        } else {
            fwrite($dbg, "PATCH TIDAK DITERAPKAN (kondisi tidak terpenuhi)\n");
        }
    } else {
        fwrite($dbg, "FILE TIDAK DITEMUKAN\n");
    }
}
fclose($dbg);
