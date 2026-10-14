from pathlib import Path
import shutil
import ssl
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / 'tools' / 'printbench_collector'
PI_UI = COLLECTOR / 'pi_ui'
RUNTIME = ROOT / 'runtime' / 'pytest-control-security'
sys.path.insert(0, str(COLLECTOR))
sys.path.insert(0, str(PI_UI))

import bambu_tls
import server


def fresh_runtime():
    shutil.rmtree(RUNTIME, ignore_errors=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    return RUNTIME


def test_control_token_is_strict_64_hex(monkeypatch):
    token_file = fresh_runtime() / 'control.token'
    monkeypatch.setattr(server, 'CONTROL_TOKEN_FILE', token_file)

    token_file.write_text('a' * 64, encoding='utf-8')
    assert server._control_token() == 'a' * 64

    token_file.write_text('x' * 64, encoding='utf-8')
    assert server._control_token() == ''

    token_file.write_text('a' * 63, encoding='utf-8')
    assert server._control_token() == ''


def test_unauthorized_catalog_never_advertises_enabled_write(monkeypatch):
    monkeypatch.setenv('PRINTBENCH_CONTROL_WRITES', '1')
    monkeypatch.setenv('PRINTBENCH_CONTROL_DESTRUCTIVE', '1')
    monkeypatch.setenv('PRINTBENCH_CONTROL_THERMAL', '1')
    monkeypatch.setenv('PRINTBENCH_CONTROL_AMS', '1')
    catalog = server.control_catalog(authorized=False)
    assert catalog['browser_write_endpoint'] is False
    assert all(not item['enabled'] for item in catalog['items'].values())
    assert all(item['status'] == 'authorization_required' for item in catalog['items'].values())


def test_missing_tls_pin_fails_closed(monkeypatch):
    missing = fresh_runtime() / 'missing.pem'
    monkeypatch.setenv('PRINTBENCH_P2S_CERT', str(missing))
    monkeypatch.delenv('PRINTBENCH_TLS_ALLOW_UNPINNED', raising=False)
    with pytest.raises(RuntimeError, match='TLS pin missing'):
        bambu_tls.mqtt_context()


def test_unpinned_tls_requires_explicit_escape_hatch(monkeypatch):
    missing = fresh_runtime() / 'missing.pem'
    monkeypatch.setenv('PRINTBENCH_P2S_CERT', str(missing))
    monkeypatch.setenv('PRINTBENCH_TLS_ALLOW_UNPINNED', '1')
    ctx = bambu_tls.mqtt_context()
    assert ctx.verify_mode == ssl.CERT_NONE
    assert ctx.check_hostname is False
