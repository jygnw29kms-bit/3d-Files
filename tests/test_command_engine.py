from pathlib import Path
import pytest,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'printbench_collector'))
import command_engine

ALL={'print.pause','print.resume','print.stop','printer.speed','printer.light','printer.fan','printer.nozzle_temp','printer.bed_temp','printer.chamber_temp','camera.recording','camera.timelapse','camera.resolution','ams.rfid_read','ams.control','ams.stop_drying','ams.filament_setting','ams.change_filament'}

def clear(monkeypatch):
    for k in ('PRINTBENCH_CONTROL_WRITES','PRINTBENCH_CONTROL_DESTRUCTIVE','PRINTBENCH_CONTROL_THERMAL','PRINTBENCH_CONTROL_AMS'):
        monkeypatch.delenv(k,raising=False)

def test_surface_and_default_fail_closed(monkeypatch):
    clear(monkeypatch); assert set(command_engine.SPECS)==ALL
    caps=command_engine.capabilities(); assert all(not v['enabled'] for v in caps.values())

def test_separate_policy_boundaries(monkeypatch):
    clear(monkeypatch);monkeypatch.setenv('PRINTBENCH_CONTROL_WRITES','1');caps=command_engine.capabilities()
    assert caps['printer.light']['enabled'] and caps['camera.recording']['enabled'] and caps['printer.fan']['enabled']
    assert not caps['print.stop']['enabled'] and not caps['printer.nozzle_temp']['enabled'] and not caps['ams.control']['enabled']
    monkeypatch.setenv('PRINTBENCH_CONTROL_DESTRUCTIVE','1');monkeypatch.setenv('PRINTBENCH_CONTROL_THERMAL','1');monkeypatch.setenv('PRINTBENCH_CONTROL_AMS','1');caps=command_engine.capabilities()
    assert caps['print.stop']['enabled'] and caps['printer.nozzle_temp']['enabled'] and caps['ams.change_filament']['enabled']

def test_exact_orca_payloads():
    assert command_engine.SPECS['print.pause'].builder({},'7')=={'print':{'sequence_id':'7','command':'pause','param':''}}
    assert command_engine.SPECS['printer.speed'].builder({'level':3},'8')['print']=={'sequence_id':'8','command':'print_speed','param':'3'}
    l=command_engine.SPECS['printer.light'].builder({'mode':'on'},'9')['system']; assert l['command']=='ledctrl' and l['led_node']=='chamber_light'
    assert command_engine.SPECS['printer.fan'].builder({'fan':1,'speed':128},'10')['print']['command']=='set_fan'
    assert command_engine.SPECS['printer.nozzle_temp'].builder({'temp':250},'11')['print']['target_temp']==250
    assert command_engine.SPECS['printer.bed_temp'].builder({'temp':80},'12')['print']['temp']==80
    assert command_engine.SPECS['printer.chamber_temp'].builder({'temp':45},'13')['print']['ctt_val']==45
    assert command_engine.SPECS['camera.recording'].builder({'enabled':True},'14')['camera']['command']=='ipcam_record_set'
    assert command_engine.SPECS['camera.timelapse'].builder({'enabled':False},'15')['camera']['control']=='disable'
    assert command_engine.SPECS['camera.resolution'].builder({'resolution':'1080p'},'16')['camera']['resolution']=='1080p'
    assert command_engine.SPECS['ams.rfid_read'].builder({'ams_id':0,'slot_id':3},'17')['print']['command']=='ams_get_rfid'
    assert command_engine.SPECS['ams.control'].builder({'action':'pause'},'18')['print']['param']=='pause'
    assert command_engine.SPECS['ams.stop_drying'].builder({},'19')['print']['command']=='auto_stop_ams_dry'

def test_validation():
    bad=[('printer.speed',{'level':5}),('printer.light',{'mode':'blink'}),('printer.fan',{'fan':5,'speed':1}),('printer.nozzle_temp',{'temp':301}),('printer.bed_temp',{'temp':121}),('printer.chamber_temp',{'temp':20}),('camera.resolution',{'resolution':'4k'}),('ams.rfid_read',{'ams_id':0,'slot_id':4}),('ams.control',{'action':'explode'})]
    for name,args in bad:
        with pytest.raises((ValueError,TypeError)):command_engine.preview(name,args)

def test_no_raw_escape_hatch():
    assert all('raw' not in n and 'mqtt' not in n and 'gcode' not in n for n in command_engine.SPECS)

def test_light_is_live_verified():
    assert command_engine.SPECS['printer.light'].protocol_status=='supported_verified'

def test_ams_filament_builder_uses_validated_generic_mapping():
    p=command_engine.SPECS['ams.filament_setting'].builder({'ams_id':0,'slot_id':3,'material':'ASA','color':'2850E0FF','nozzle_temp_min':240,'nozzle_temp_max':280},'20')['print']
    assert p['command']=='ams_filament_setting' and p['tray_info_idx']=='GFB98' and p['slot_id']==3 and p['tray_id']==3
