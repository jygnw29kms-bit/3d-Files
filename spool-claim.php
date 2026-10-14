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
    try { $s=pb_bind_nfc_uid($id,$body['uid']??'',pb_text($body['tagType']??'NTAG216',32)); }
    catch(InvalidArgumentException $e){ pb_json_response(['ok'=>false,'error'=>'uid'],422); }
    catch(OutOfBoundsException $e){ pb_json_response(['ok'=>false,'error'=>'not_found'],404); }
    catch(RuntimeException $e){
        $msg=$e->getMessage();
        if (str_starts_with($msg,'uid_already_bound:')) pb_json_response(['ok'=>false,'error'=>'uid_already_bound','bound_to'=>substr($msg,18)],409);
        if ($msg==='spool_already_has_different_uid') pb_json_response(['ok'=>false,'error'=>$msg],409);
        throw $e;
    }
    pb_json_response(['ok'=>true,'spool'=>pb_public_spool($s),'nfc_uid'=>$s['nfc_uid']]);
} catch(Throwable $e) {
    error_log('PRINTBENCH spool-claim: '.$e->getMessage());
    pb_json_response(['ok'=>false,'error'=>'server'],500);
}