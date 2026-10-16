from __future__ import annotations
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=json.loads((ROOT/'config'/'product-contract.json').read_text(encoding='utf-8'))
ORCA=ROOT/CONTRACT['orca']['source_dir']
BBL=ORCA/'resources'/'profiles'/'BBL'
errors=[]

version=(ORCA/'version.inc').read_text(encoding='utf-8',errors='ignore')
m=re.search(r'set\(SoftFever_VERSION "([^"]+)"\)',version)
if not m or m.group(1)!=CONTRACT['orca']['version']:
    errors.append(f"Orca version mismatch: {m.group(1) if m else 'missing'}")

model=json.loads((BBL/'machine'/'Bambu Lab P2S.json').read_text(encoding='utf-8'))
if model.get('model_id')!=CONTRACT['hardware']['orca_model_id']:
    errors.append(f"P2S model_id mismatch: {model.get('model_id')}")
actual=sorted(float(x) for x in str(model.get('nozzle_diameter','')).split(';') if x)
expected=sorted(float(x) for x in CONTRACT['hardware']['supported_nozzles_mm'])
if actual!=expected:errors.append(f'Nozzle set mismatch: {actual} != {expected}')
for nozzle in expected:
    p=BBL/'machine'/f'Bambu Lab P2S {nozzle:.1f} nozzle.json'
    if not p.is_file():errors.append(f'Missing P2S machine profile: {p.name}')
    else:
        data=json.loads(p.read_text(encoding='utf-8'))
        if data.get('printer_model')!='Bambu Lab P2S':errors.append(f'Wrong printer_model in {p.name}')

if CONTRACT['boundaries'].get('ams_writes_default') is not False:errors.append('AMS writes must default to false')
if CONTRACT['desktop'].get('single_app') is not True:errors.append('PRINTBENCH must be a single desktop app')
if CONTRACT['desktop'].get('bambu_studio_required') is not False:errors.append('Bambu Studio must not be required')
if CONTRACT['desktop'].get('native_device_ui') is not True:errors.append('Device UI must be native')
if CONTRACT['desktop'].get('native_collector') is not True:errors.append('Desktop collector must be native')
if CONTRACT['desktop'].get('pi_required') is not False:errors.append('Pi must not be required for desktop operation')
master=ROOT/CONTRACT['desktop']['final_master']
if not master.is_file():errors.append(f'Binding FINAL-MASTER missing: {master}')

wizard=(ORCA/'src'/'slic3r'/'GUI'/'ConfigWizard.cpp').read_text(encoding='utf-8',errors='ignore')
if 'set_variant("BBL", "N7", "0.4", true)' not in wizard:errors.append('PRINTBENCH P2S default variant gate missing')
if 'index->add_page(page_custom);' in wizard:errors.append('Custom-printer page is exposed in ConfigWizard')
if 'vendor.id == "BBL" && model.id == "N7"' not in wizard:errors.append('P2S-only model filter missing')
if 'set(SLIC3R_APP_NAME "PRINTBENCH Studio")' not in version:errors.append('PRINTBENCH Studio branding missing')

plater=(ORCA/'src'/'slic3r'/'GUI'/'Plater.cpp').read_text(encoding='utf-8',errors='ignore')
if 'm_printer_connect->Hide();' not in plater:errors.append('Generic print-host connection UI is exposed')
gui_app=(ORCA/'src'/'slic3r'/'GUI'/'GUI_App.cpp').read_text(encoding='utf-8',errors='ignore')
if 'printer presets may only extend the fixed Bambu Lab P2S family' not in gui_app:errors.append('Foreign pending printer preset filter missing')

native_panel=ORCA/'src'/'slic3r'/'GUI'/'PrintbenchNativePanel.cpp'
native_collector=ORCA/'src'/'slic3r'/'GUI'/'PrintbenchCollector.cpp'
monitor=(ORCA/'src'/'slic3r'/'GUI'/'Monitor.cpp').read_text(encoding='utf-8',errors='ignore')
if not native_panel.is_file():errors.append('Native PRINTBENCH panel missing')
if not native_collector.is_file():errors.append('Native PRINTBENCH collector missing')
# The FINAL-MASTER gives PRINTBENCH the complete Device viewport. The native
# panel therefore belongs directly to MonitorPanel; Orca's legacy Tabbook is
# kept hidden only for internal services.
if 'm_printbench_panel = new PrintbenchNativePanel(this);' not in monitor:
    errors.append('Device -> PRINTBENCH is not using the full native Device viewport')
if 'm_tabpanel->Hide();' not in monitor:
    errors.append('Legacy Orca Device tabbook is still exposed')
if 'm_main_sizer->Add(m_printbench_panel, 1, wxEXPAND, 0);' not in monitor:
    errors.append('Native PRINTBENCH panel does not own the Device viewport')
if 'm_printbench_panel->load_url' in monitor:errors.append('PRINTBENCH Device surface still embeds a WebView URL')

if errors:
    print('PRODUCT_CONTRACT_FAIL')
    for e in errors:print('-',e)
    raise SystemExit(1)
print('PRODUCT_CONTRACT_OK')
print('orca',CONTRACT['orca']['version'],'model_id',model['model_id'],'nozzles',','.join(map(str,expected)),'native_device',True)
