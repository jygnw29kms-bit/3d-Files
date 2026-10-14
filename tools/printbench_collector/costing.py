from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CONFIG=ROOT/'cost_config.json'
DEFAULTS={
    'schema':1,
    'material_price_eur_per_kg':18.99,
    'electricity_price_eur_per_kwh':0.40,
    'machine_rate_eur_per_hour':0.65,
    'margin_pct':20.0,
    'estimated_avg_power_kw':0.20,
    'startup_energy_kwh':0.10,
    'energy_is_estimated':True,
    'material_basis':'planned_slicer_filament',
}

def load_config():
    data=dict(DEFAULTS)
    try:
        x=json.loads(CONFIG.read_text(encoding='utf-8'))
        if isinstance(x,dict): data.update(x)
    except Exception: pass
    return data

def calculate(planned_filament_g, actual_time_sec):
    c=load_config()
    g=max(0.0,float(planned_filament_g or 0))
    sec=max(0.0,float(actual_time_sec or 0))
    hours=sec/3600.0
    mat_rate=max(0.0,float(c['material_price_eur_per_kg']))
    power_rate=max(0.0,float(c['electricity_price_eur_per_kwh']))
    machine_rate=max(0.0,float(c['machine_rate_eur_per_hour']))
    margin_pct=max(0.0,float(c['margin_pct']))
    energy=max(0.0,float(c['startup_energy_kwh']))+max(0.0,float(c['estimated_avg_power_kw']))*hours
    material=g/1000.0*mat_rate
    electricity=energy*power_rate
    machine=hours*machine_rate
    self_cost=material+electricity+machine
    margin=self_cost*margin_pct/100.0
    return {
        'cost_basis':'planned_filament_estimated_energy',
        'material_price_eur_per_kg':mat_rate,
        'electricity_price_eur_per_kwh':power_rate,
        'machine_rate_eur_per_hour':machine_rate,
        'margin_pct':margin_pct,
        'estimated_energy_kwh':energy,
        'material_cost_eur':material,
        'electricity_cost_eur':electricity,
        'machine_cost_eur':machine,
        'self_cost_eur':self_cost,
        'margin_eur':margin,
        'sale_price_eur':self_cost+margin,
        'energy_is_estimated':1 if c.get('energy_is_estimated',True) else 0,
    }

def public_config():
    c=load_config()
    return {k:c[k] for k in ('schema','material_price_eur_per_kg','electricity_price_eur_per_kwh','machine_rate_eur_per_hour','margin_pct','estimated_avg_power_kw','startup_energy_kwh','energy_is_estimated','material_basis')}