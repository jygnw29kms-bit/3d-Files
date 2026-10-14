<?php
declare(strict_types=1);
require __DIR__.'/spool-lib.php';
header('Access-Control-Allow-Origin: https://www.dezender.de');
header('Access-Control-Allow-Headers: Content-Type, X-PRINTBENCH-ADMIN, Authorization');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD']==='OPTIONS') { http_response_code(204); exit; }
try {
    $method=$_SERVER['REQUEST_METHOD']??'GET';
    $action=pb_text($_GET['action']??'list',40);
    $data=pb_load_spools();

    if ($method==='GET' && $action==='list') {
        $out=array_map('pb_public_spool',$data['spools']);
        usort($out,fn($a,$b)=>strcmp((string)$b['updated_at'],(string)$a['updated_at']));
        pb_json_response(['ok'=>true,'schema'=>PB_SPOOL_SCHEMA,'count'=>count($out),'spools'=>$out,'updated_at'=>$data['updated_at']??null]);
    }

    if ($method==='GET' && $action==='detail') {
        pb_require_admin();
        $id=pb_text($_GET['id']??'',24); $i=pb_find_index($data,$id);
        if ($i<0) pb_json_response(['ok'=>false,'error'=>'not_found'],404);
        pb_json_response(['ok'=>true,'spool'=>$data['spools'][$i]]);
    }

    if ($method==='GET' && $action==='tag_payload') {
        pb_require_admin();
        $id=pb_text($_GET['id']??'',24); $i=pb_find_index($data,$id);
        if ($i<0) pb_json_response(['ok'=>false,'error'=>'not_found'],404);
        $s=$data['spools'][$i]; $claim=pb_claim_url($id,900);
        pb_json_response(['ok'=>true,'payload'=>[
            'version'=>PB_SPOOL_SCHEMA,'spoolId'=>$id,'displayName'=>$s['display_name'],'material'=>$s['material'],
            'vendor'=>$s['vendor'],'colorHex'=>$s['color_hex'],'claimURL'=>$claim['url'],'signature'=>$claim['sig'],
            'expiresAt'=>gmdate(DATE_ATOM,$claim['exp'])
        ]]);
    }

    if ($method!=='POST') pb_json_response(['ok'=>false,'error'=>'method'],405);
    pb_require_admin();
    $body=pb_body();
    $action=pb_text($body['action']??$action,40);

    if ($action==='create') {
        $n=(int)$data['next_id']; $id=pb_spool_id($n);
        while(pb_find_index($data,$id)>=0){$n++;$id=pb_spool_id($n);} 
        $s=pb_normalize_spool((array)($body['spool']??[])); $s['id']=$id;
        if ($s['display_name']==='') $s['display_name']=trim($s['vendor'].' '.$s['material'].' '.$s['color_name']);
        if ($s['material']==='') pb_json_response(['ok'=>false,'error'=>'material_required'],422);
        $data['spools'][]=$s; $data['next_id']=$n+1; pb_save_spools($data);
        pb_json_response(['ok'=>true,'spool'=>$s,'public'=>pb_public_spool($s)],201);
    }

    if ($action==='update') {
        $id=pb_text($body['id']??'',24); $i=pb_find_index($data,$id);
        if ($i<0) pb_json_response(['ok'=>false,'error'=>'not_found'],404);
        $s=pb_normalize_spool((array)($body['spool']??[]),$data['spools'][$i]); $data['spools'][$i]=$s; pb_save_spools($data);
        pb_json_response(['ok'=>true,'spool'=>$s,'public'=>pb_public_spool($s)]);
    }

    if ($action==='set_dried') {
        $id=pb_text($body['id']??'',24); $i=pb_find_index($data,$id); if($i<0) pb_json_response(['ok'=>false,'error'=>'not_found'],404);
        $data['spools'][$i]['last_dried_at']=gmdate(DATE_ATOM); $data['spools'][$i]['updated_at']=gmdate(DATE_ATOM); pb_save_spools($data);
        pb_json_response(['ok'=>true,'spool'=>$data['spools'][$i]]);
    }

    if ($action==='delete') {
        $id=pb_text($body['id']??'',24); $i=pb_find_index($data,$id); if($i<0) pb_json_response(['ok'=>false,'error'=>'not_found'],404);
        $old=$data['spools'][$i]; array_splice($data['spools'],$i,1); pb_save_spools($data);
        pb_json_response(['ok'=>true,'deleted'=>$id,'had_nfc'=>!empty($old['nfc_uid'])]);
    }

    pb_json_response(['ok'=>false,'error'=>'action'],422);
} catch(Throwable $e) {
    error_log('PRINTBENCH spool-api: '.$e->getMessage());
    pb_json_response(['ok'=>false,'error'=>'server'],500);
}