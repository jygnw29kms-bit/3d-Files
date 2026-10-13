<?php
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
$dir = __DIR__ . '/runtime/media'; $file=$dir.'/meta.json';
$meta=[]; if (is_file($file)) { $m=json_decode((string)file_get_contents($file),true); if(is_array($m))$meta=$m; }
$archives=[]; foreach(array_slice(array_reverse(glob($dir.'/timelapse-*.mp4')?:[]),0,12) as $f){$archives[]=['file'=>basename($f),'bytes'=>filesize($f),'updated_at'=>gmdate(DATE_ATOM,filemtime($f))];}
$native=[]; $ndir=$dir.'/native';
if (is_dir($ndir)) {
  foreach(array_reverse(glob($ndir.'/video_*.mp4')?:[]) as $f){
    $name=basename($f); $stem=pathinfo($name,PATHINFO_FILENAME); $thumb=$stem.'.jpg';
    $native[]=['file'=>'native/'.$name,'thumb'=>is_file($ndir.'/'.$thumb)?'native/'.$thumb:null,'bytes'=>filesize($f),'updated_at'=>gmdate(DATE_ATOM,filemtime($f))];
  }
  usort($native,fn($a,$b)=>strcmp($b['file'],$a['file']));
}
echo json_encode(['ok'=>true,'media'=>$meta,'timelapses'=>$archives,'native_timelapses'=>$native],JSON_UNESCAPED_SLASHES);
