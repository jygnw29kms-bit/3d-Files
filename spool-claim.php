<?php
declare(strict_types=1);
require __DIR__.'/spool-lib.php';
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD']==='OPTIONS') { http_response_code(204); exit; }
try {
    $id=pb_text($_GET['spool']??'',24);
    $exp=(int)($_GET['exp']??0);
    $nonce=pb_text($_GET['nonce']??'',32);
    $sig=pb_text($_GET['sig']??'',128);
    if ($id==='' || !pb_verify_claim($id,$exp,$nonce,$sig)) pb_json_response(['ok'=>false,'error'=>'claim_invalid_or_expired'],403);
    $data=pb_load_spools(); $i=pb_find_index($data,$id);
    if ($i<0) pb_json_response(['ok'=>false,'error'=>'not_found'],404);
    $s=$data['spools'][$i];
    if (($_SERVER['REQUEST_METHOD']??'GET')==='GET') {
        pb_json_response(['ok'=>true,'claim'=>['spoolId'=>$id,'displayName'=>$s['display_name'],'vendor'=>$s['vendor'],'material'=>$s['material'],'colorHex'=>$s['color_hex'],'expiresAt'=>gmdate(DATE_ATOM,$exp)]]);
    }
    if (($_SERVER['REQUEST_METHOD']??'GET')!=='POST') pb_json_response(['ok'=>false,'error'=>'method'],405);
    $body=pb_body();
    $uid=strtoupper(preg_replace('/[^0-9A-F]/i','',(string)($body['uid']??''))??'');
    if (!preg_match('/^[0-9A-F]{8,32}$/',$uid)) pb_json_response(['ok'=>false,'error'=>'uid'],422);
    foreach($data['spools'] as $other) {
        if (($other['id']??'')!==$id && strtoupper(str_replace(':','',(string)($other['nfc_uid']??'')))===$uid) pb_json_response(['ok'=>false,'error'=>'uid_already_bound','bound_to'=>$other['id']],409);
    }
    $formatted=implode(':',str_split($uid,2));
    $existing=(string)($s['nfc_uid']??'');
    if ($existing!=='' && strtoupper(str_replace(':','',$existing))!==$uid) pb_json_response(['ok'=>false,'error'=>'spool_already_has_different_uid'],409);
    $s['nfc_uid']=$formatted;
    $s['nfc_tag_type']=pb_text($body['tagType']??'NTAG216',32);
    $s['nfc_programmed_at']=gmdate(DATE_ATOM);
    $s['updated_at']=gmdate(DATE_ATOM);
    $data['spools'][$i]=$s; pb_save_spools($data);
    pb_json_response(['ok'=>true,'spool'=>pb_public_spool($s),'nfc_uid'=>$formatted]);
} catch(Throwable $e) {
    error_log('PRINTBENCH spool-claim: '.$e->getMessage());
    pb_json_response(['ok'=>false,'error'=>'server'],500);
}