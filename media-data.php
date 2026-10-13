<?php
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
$dir = __DIR__ . '/runtime/media'; $file=$dir.'/meta.json';
$meta=[]; if (is_file($file)) { $m=json_decode((string)file_get_contents($file),true); if(is_array($m))$meta=$m; }
$archives=[]; foreach(array_slice(array_reverse(glob($dir.'/timelapse-*.mp4')?:[]),0,12) as $f){$archives[]=['file'=>basename($f),'bytes'=>filesize($f),'updated_at'=>gmdate(DATE_ATOM,filemtime($f))];}
echo json_encode(['ok'=>true,'media'=>$meta,'timelapses'=>$archives],JSON_UNESCAPED_SLASHES);
