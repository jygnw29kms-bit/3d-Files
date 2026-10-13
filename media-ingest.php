<?php
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['ok'=>false,'error'=>'method']); exit; }
$token = trim((string)($_SERVER['HTTP_X_PRINTBENCH_TOKEN'] ?? ''));
if ($token === '') { $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? ''; if (preg_match('/^Bearer\s+(.+)$/i', $auth, $m)) $token = trim($m[1]); }
if ($token === '') { http_response_code(401); echo json_encode(['ok'=>false,'error'=>'auth']); exit; }
$expected = '932995b6ae893c2501982f4b840575980cd6c5b0309c09267314fe813a2285f9';
if (!hash_equals($expected, hash('sha256', $token))) { http_response_code(403); echo json_encode(['ok'=>false,'error'=>'auth']); exit; }
$kind = strtolower(trim((string)($_GET['kind'] ?? '')));
$map = [
 'snapshot'=>['latest.jpg','image/jpeg',2000000],
 'clip'=>['live.mp4','video/mp4',50000000],
 'timelapse'=>['timelapse-latest.mp4','video/mp4',200000000]
];
if (!isset($map[$kind])) { http_response_code(422); echo json_encode(['ok'=>false,'error'=>'kind']); exit; }
[$name,$mime,$max] = $map[$kind];
$len = (int)($_SERVER['CONTENT_LENGTH'] ?? 0);
if ($len <= 0 || $len > $max) { http_response_code(413); echo json_encode(['ok'=>false,'error'=>'size']); exit; }
$ctype = strtolower(trim(explode(';', (string)($_SERVER['CONTENT_TYPE'] ?? ''))[0]));
if ($ctype !== $mime) { http_response_code(415); echo json_encode(['ok'=>false,'error'=>'type']); exit; }
$raw = file_get_contents('php://input');
if ($raw === false || strlen($raw) !== $len) { http_response_code(400); echo json_encode(['ok'=>false,'error'=>'body']); exit; }
$dir = __DIR__ . '/runtime/media';
if (!is_dir($dir) && !mkdir($dir, 0750, true)) { http_response_code(500); echo json_encode(['ok'=>false,'error'=>'storage']); exit; }
$tmp = $dir . '/' . $name . '.tmp'; $dst = $dir . '/' . $name;
if (file_put_contents($tmp, $raw, LOCK_EX) === false || !rename($tmp, $dst)) { @unlink($tmp); http_response_code(500); echo json_encode(['ok'=>false,'error'=>'write']); exit; }
@chmod($dst, 0644);
if ($kind === 'timelapse') {
  $archive = $dir . '/timelapse-' . gmdate('Ymd-His') . '.mp4'; @copy($dst, $archive); @chmod($archive, 0644);
  $old = glob($dir . '/timelapse-*.mp4') ?: []; usort($old, fn($a,$b)=>filemtime($b)<=>filemtime($a)); foreach(array_slice($old,12) as $f) @unlink($f);
}
$metaFile = $dir . '/meta.json'; $meta = [];
if (is_file($metaFile)) { $m = json_decode((string)file_get_contents($metaFile), true); if (is_array($m)) $meta=$m; }
$meta[$kind] = ['file'=>$name,'updated_at'=>gmdate(DATE_ATOM),'bytes'=>strlen($raw),'mime'=>$mime];
$meta['updated_at'] = gmdate(DATE_ATOM);
file_put_contents($metaFile, json_encode($meta, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT), LOCK_EX); @chmod($metaFile,0644);
echo json_encode(['ok'=>true,'kind'=>$kind,'bytes'=>strlen($raw),'updated_at'=>$meta[$kind]['updated_at']]);
