<?php
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['ok'=>false,'error'=>'method']); exit; }
$auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
if (!preg_match('/^Bearer\s+(.+)$/i', $auth, $m)) { http_response_code(401); echo json_encode(['ok'=>false,'error'=>'auth']); exit; }
$expected = '932995b6ae893c2501982f4b840575980cd6c5b0309c09267314fe813a2285f9';
if (!hash_equals($expected, hash('sha256', trim($m[1])))) { http_response_code(403); echo json_encode(['ok'=>false,'error'=>'auth']); exit; }
$len = (int)($_SERVER['CONTENT_LENGTH'] ?? 0);
if ($len <= 0 || $len > 600000) { http_response_code(413); echo json_encode(['ok'=>false,'error'=>'size']); exit; }
$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data) || !isset($data['live']) || !is_array($data['live'])) { http_response_code(422); echo json_encode(['ok'=>false,'error'=>'schema']); exit; }
$dir = __DIR__ . '/runtime';
if (!is_dir($dir) && !mkdir($dir, 0750, true)) { http_response_code(500); echo json_encode(['ok'=>false,'error'=>'storage']); exit; }
$data['received_at'] = gmdate(DATE_ATOM);
$tmp = $dir . '/live.json.tmp';
$dst = $dir . '/live.json';
$json = json_encode($data, JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE);
if (file_put_contents($tmp, $json, LOCK_EX) === false || !rename($tmp, $dst)) { @unlink($tmp); http_response_code(500); echo json_encode(['ok'=>false,'error'=>'write']); exit; }
@chmod($dst, 0640);
echo json_encode(['ok'=>true,'received_at'=>$data['received_at']]);
