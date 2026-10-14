<?php
declare(strict_types=1);

const PB_SPOOL_SCHEMA = 1;
const PB_ADMIN_HASH = 'ce7a5b29aa8aec800f3d6ba8ae719917c1984621b77b89ed1c875da2c378de5b';

function pb_runtime_dir(): string {
    $dir = __DIR__ . '/runtime';
    if (!is_dir($dir) && !mkdir($dir, 0750, true) && !is_dir($dir)) throw new RuntimeException('runtime_unavailable');
    return $dir;
}

function pb_private_dir(): ?string {
    $dir='/var/www/vhosts/dezender.de/private';
    return is_dir($dir) && is_writable($dir) ? $dir : null;
}

function pb_spool_file(): string {
    $private=pb_private_dir();
    if ($private!==null) return $private . '/printbench-spools.json';
    $runtime=pb_runtime_dir();
    $deny=$runtime.'/.htaccess';
    $rules="<FilesMatch \"^(spools\\.json|\\.spool-secret)$\">\nRequire all denied\n</FilesMatch>\n";
    if (!is_file($deny) || strpos((string)@file_get_contents($deny),'spools\\.json')===false) @file_put_contents($deny,$rules,LOCK_EX);
    return $runtime . '/spools.json';
}

function pb_json_response(array $data, int $status=200): never {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($data, JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT);
    exit;
}

function pb_body(): array {
    $len=(int)($_SERVER['CONTENT_LENGTH']??0);
    if ($len<=0 || $len>65536) pb_json_response(['ok'=>false,'error'=>'size'],413);
    $raw=file_get_contents('php://input');
    $data=json_decode((string)$raw,true);
    if (!is_array($data)) pb_json_response(['ok'=>false,'error'=>'json'],422);
    return $data;
}

function pb_admin_token(): string {
    $token=trim((string)($_SERVER['HTTP_X_PRINTBENCH_ADMIN']??''));
    if ($token==='') {
        $auth=(string)($_SERVER['HTTP_AUTHORIZATION']??'');
        if (preg_match('/^Bearer\s+(.+)$/i',$auth,$m)) $token=trim($m[1]);
    }
    return $token;
}

function pb_require_admin(): void {
    $token=pb_admin_token();
    if ($token==='' || !hash_equals(PB_ADMIN_HASH,hash('sha256',$token))) pb_json_response(['ok'=>false,'error'=>'auth'],403);
}

function pb_secret_path(): string {
    $private=pb_private_dir();
    if ($private!==null) return $private . '/printbench-spool-secret';
    return pb_runtime_dir() . '/.spool-secret';
}

function pb_secret(): string {
    $env=getenv('PRINTBENCH_SPOOL_SECRET');
    if (is_string($env) && strlen($env)>=32) return $env;
    $path=pb_secret_path();
    if (is_file($path)) {
        $s=trim((string)file_get_contents($path));
        if (strlen($s)>=32) return $s;
    }
    $s=rtrim(strtr(base64_encode(random_bytes(48)),'+/','-_'),'=');
    if (file_put_contents($path,$s,LOCK_EX)===false) throw new RuntimeException('secret_write_failed');
    @chmod($path,0600);
    if (str_contains($path,'/runtime/')) {
        $deny=pb_runtime_dir().'/.htaccess';
        if (!is_file($deny)) @file_put_contents($deny,"<FilesMatch \"^\\.\">\nRequire all denied\n</FilesMatch>\n",LOCK_EX);
    }
    return $s;
}

function pb_load_spools(): array {
    $file=pb_spool_file();
    if (!is_file($file)) return ['schema'=>PB_SPOOL_SCHEMA,'next_id'=>1,'spools'=>[],'updated_at'=>gmdate(DATE_ATOM)];
    $raw=file_get_contents($file);
    $data=json_decode((string)$raw,true);
    if (!is_array($data) || !isset($data['spools']) || !is_array($data['spools'])) throw new RuntimeException('spool_storage_invalid');
    $data['next_id']=max(1,(int)($data['next_id']??1));
    return $data;
}

function pb_save_spools(array $data): void {
    $data['schema']=PB_SPOOL_SCHEMA;
    $data['updated_at']=gmdate(DATE_ATOM);
    $file=pb_spool_file();
    $tmp=$file.'.tmp-'.getmypid().'-'.bin2hex(random_bytes(3));
    $json=json_encode($data,JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT);
    if (file_put_contents($tmp,$json,LOCK_EX)===false || !rename($tmp,$file)) { @unlink($tmp); throw new RuntimeException('spool_storage_write'); }
    @chmod($file,0640);
}

function pb_text(mixed $v,int $max=120): string {
    $s=trim((string)$v);
    $s=preg_replace('/[\x00-\x1F\x7F]/u','',$s)??'';
    return mb_substr($s,0,$max);
}
function pb_float(mixed $v,float $min=0,float $max=100000): ?float {
    if ($v==='' || $v===null) return null;
    if (!is_numeric($v)) return null;
    $n=(float)$v; return max($min,min($max,$n));
}
function pb_color(mixed $v): string {
    $s=strtoupper(ltrim(pb_text($v,9),'#'));
    return preg_match('/^[0-9A-F]{6}$/',$s)?'#'.$s:'#808080';
}
function pb_spool_id(int $n): string { return 'PB-'.str_pad((string)$n,6,'0',STR_PAD_LEFT); }
function pb_find_index(array $data,string $id): int {
    foreach($data['spools'] as $i=>$s) if (($s['id']??'')===$id) return (int)$i;
    return -1;
}

function pb_normalize_spool(array $in, ?array $old=null): array {
    $now=gmdate(DATE_ATOM);
    $start=pb_float($in['initial_net_g']??($old['initial_net_g']??1000),0,100000)??1000;
    $remaining=pb_float($in['remaining_g']??($old['remaining_g']??$start),0,100000)??$start;
    return [
        'id'=>$old['id']??'',
        'display_name'=>pb_text($in['display_name']??($old['display_name']??''),160),
        'vendor'=>pb_text($in['vendor']??($old['vendor']??''),100),
        'material'=>strtoupper(pb_text($in['material']??($old['material']??''),40)),
        'color_name'=>pb_text($in['color_name']??($old['color_name']??''),80),
        'color_hex'=>pb_color($in['color_hex']??($old['color_hex']??'#808080')),
        'filament_profile'=>pb_text($in['filament_profile']??($old['filament_profile']??''),180),
        'diameter_mm'=>pb_float($in['diameter_mm']??($old['diameter_mm']??1.75),1,4)??1.75,
        'initial_net_g'=>$start,
        'remaining_g'=>min($remaining,$start),
        'spool_tare_g'=>pb_float($in['spool_tare_g']??($old['spool_tare_g']??null),0,5000),
        'purchase_price_eur'=>pb_float($in['purchase_price_eur']??($old['purchase_price_eur']??null),0,10000),
        'nozzle_temp_min'=>pb_float($in['nozzle_temp_min']??($old['nozzle_temp_min']??null),0,400),
        'nozzle_temp_max'=>pb_float($in['nozzle_temp_max']??($old['nozzle_temp_max']??null),0,400),
        'dry_temp_c'=>pb_float($in['dry_temp_c']??($old['dry_temp_c']??null),0,100),
        'dry_duration_h'=>pb_float($in['dry_duration_h']??($old['dry_duration_h']??null),0,168),
        'last_dried_at'=>$old['last_dried_at']??null,
        'status'=>pb_text($in['status']??($old['status']??'open'),24),
        'ams_id'=>$old['ams_id']??null,
        'ams_slot'=>$old['ams_slot']??null,
        'nfc_uid'=>$old['nfc_uid']??null,
        'nfc_tag_type'=>$old['nfc_tag_type']??null,
        'nfc_programmed_at'=>$old['nfc_programmed_at']??null,
        'created_at'=>$old['created_at']??$now,
        'updated_at'=>$now,
    ];
}

function pb_public_spool(array $s): array {
    $start=max(0.001,(float)($s['initial_net_g']??0));
    $remaining=max(0,(float)($s['remaining_g']??0));
    return [
        'id'=>$s['id'],'display_name'=>$s['display_name'],'vendor'=>$s['vendor'],'material'=>$s['material'],
        'color_name'=>$s['color_name'],'color_hex'=>$s['color_hex'],'filament_profile'=>$s['filament_profile'],
        'remaining_g'=>$remaining,'initial_net_g'=>$start,'remaining_pct'=>round(($remaining/$start)*100,1),
        'status'=>$s['status'],'ams_id'=>$s['ams_id'],'ams_slot'=>$s['ams_slot'],
        'nfc_bound'=>!empty($s['nfc_uid']),'updated_at'=>$s['updated_at']
    ];
}

function pb_claim_url(string $id,int $ttl=900): array {
    $exp=time()+max(60,min(3600,$ttl));
    $nonce=bin2hex(random_bytes(8));
    $msg=$id.'|'.$exp.'|'.$nonce;
    $sig=rtrim(strtr(base64_encode(hash_hmac('sha256',$msg,pb_secret(),true)),'+/','-_'),'=');
    $base='https://www.dezender.de/3d-druck/spool-claim.php';
    return ['url'=>$base.'?spool='.rawurlencode($id).'&exp='.$exp.'&nonce='.$nonce.'&sig='.rawurlencode($sig),'exp'=>$exp,'nonce'=>$nonce,'sig'=>$sig];
}

function pb_verify_claim(string $id,int $exp,string $nonce,string $sig): bool {
    if ($exp<time() || $exp>time()+3700 || !preg_match('/^[A-Fa-f0-9]{16}$/',$nonce)) return false;
    $msg=$id.'|'.$exp.'|'.$nonce;
    $want=rtrim(strtr(base64_encode(hash_hmac('sha256',$msg,pb_secret(),true)),'+/','-_'),'=');
    return hash_equals($want,$sig);
}