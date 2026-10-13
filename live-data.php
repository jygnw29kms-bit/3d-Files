<?php
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Pragma: no-cache');
$file = __DIR__ . '/runtime/live.json';
if (!is_file($file)) { http_response_code(503); echo json_encode(['ok'=>false,'status'=>'waiting_for_collector']); exit; }
$raw = file_get_contents($file);
if ($raw === false) { http_response_code(500); echo json_encode(['ok'=>false,'status'=>'read_error']); exit; }
echo $raw;
