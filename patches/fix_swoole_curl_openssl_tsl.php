<?php
// Dijalankan static-php-cli via --with-added-patch (lihat install.sh, dipasang di spc build).
// Fix bug kompatibilitas: swoole (bundled curl coroutine hook) menyalakan ulang kode lawas
// thread-safety-lock buat OpenSSL <1.1.0 (macro PHP_CURL_NEED_OPENSSL_TSL, di file
// ext/swoole/thirdparty/php/curl/interface.cc) kalau ZTS aktif (selalu kita pakai) - kode itu
// gagal compile di g++ modern ("converting to bool from std::nullptr_t requires
// direct-initialization") dan sama sekali tidak relevan lagi buat OpenSSL 1.1.0+ (locking
// callback API sudah no-op di situ), jadi aman dihapus definisinya.
//
// 'before-php-make' = source php-src sudah di-extract, tapi compile belum mulai - titik yang
// tepat buat patch file source sebelum kepakai.
if ($this->getPatchPoint() === 'before-php-make') {
    $file = SOURCE_PATH . '/php-src/ext/swoole/thirdparty/php/curl/interface.cc';
    if (file_exists($file)) {
        $content = file_get_contents($file);
        $patched = preg_replace('/^#define PHP_CURL_NEED_OPENSSL_TSL\r?\n/m', '', $content);
        if ($patched !== $content) {
            file_put_contents($file, $patched);
        }
    }
}
