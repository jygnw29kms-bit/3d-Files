<?php
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
$root=__DIR__;
$paths=[
'LST-Klammer/LST-Klammer-P2S-24x-4mm.3mf','LST-Klammer/LST-Klammer-4mm.stl','LST-Klammer/LST-Klammer-Download.zip','LST-Klammer/Pruefbericht.json',
'LST-Clips/P2S-KINGROON-HS-PLA/LST_428_P2S_KINGROON_HS_PLA.3mf','LST-Clips/P2S-KINGROON-HS-PLA/LST_Passprobe_6_P2S_KINGROON_HS_PLA.3mf','LST-Clips/P2S-KINGROON-HS-PLA/P2S_KINGROON_LST_Druckpaket.zip','LST-Clips/P2S-KINGROON-HS-PLA/Druckhinweise_P2S_HS_PLA.md'];
$files=[];$total=0;
foreach($paths as $path){$full=$root.'/'.$path;$exists=is_file($full);$size=$exists?filesize($full):0;$total+=$size;$files[]=['path'=>$path,'name'=>basename($path),'exists'=>$exists,'bytes'=>$size,'modified'=>$exists?date(DATE_ATOM,filemtime($full)):null,'sha256'=>$exists?hash_file('sha256',$full):null];}
echo json_encode(['service'=>'PRINTBENCH','version'=>'2.0','serverTime'=>date(DATE_ATOM),'php'=>PHP_VERSION,'fileCount'=>count($files),'totalBytes'=>$total,'files'=>$files],JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE);
