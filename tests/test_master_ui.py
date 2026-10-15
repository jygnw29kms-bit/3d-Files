from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'tools' / 'printbench_collector' / 'pi_ui' / 'static'
HTML = (STATIC / 'index.html').read_text(encoding='utf-8')
JS = (STATIC / 'app.js').read_text(encoding='utf-8')
CSS = (STATIC / 'app.css').read_text(encoding='utf-8')


class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        self.ids.extend(value for key, value in attrs if key == 'id')


def html_ids():
    parser = IdParser()
    parser.feed(HTML)
    return parser.ids


def test_master_dom_ids_are_unique_and_cover_javascript_refs():
    ids = html_ids()
    assert len(ids) == len(set(ids))
    js_refs = set(re.findall(r"\$\('([^']+)'\)", JS))
    missing = sorted(js_refs - set(ids))
    assert not missing, f'JavaScript references missing DOM ids: {missing}'


def test_binding_master_dashboard_sections_exist():
    required = [
        'master-hero-grid', 'machine-hero', 'printer-status', 'camera-panel',
        'current-print', 'therm', 'ams-card', 'master-bottom-grid',
        'side-nav', 'top-nav', 'mobileNavToggle', 'navScrim',
    ]
    for token in required:
        assert token in HTML, token

    for label in ['Dashboard', 'Live-Ansicht', 'Steuerung', 'AMS 2 Pro', 'Material',
                  'Druckaufträge', 'Historie', 'Kamera', 'Sicherheit', 'Diagnose', 'System']:
        assert label in HTML


def test_master_is_responsive_and_local_only():
    assert '@media(max-width:980px)' in CSS
    assert '@media(max-width:560px)' in CSS
    assert 'grid-template-columns:1fr' in CSS
    assert 'https://' not in HTML
    assert '<script src="app.js"></script>' in HTML
    assert '<link rel="stylesheet" href="app.css">' in HTML


def test_binding_master_reference_is_present():
    assert (ROOT / 'docs' / 'design' / 'PRINTBENCH_FINAL_MASTER.webp').is_file()
    spec = (ROOT / 'docs' / 'design' / 'PRINTBENCH_FINAL_MASTER.md').read_text(encoding='utf-8')
    assert 'VERBINDLICH / DESIGN SOURCE OF TRUTH' in spec
