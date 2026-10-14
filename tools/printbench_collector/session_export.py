from __future__ import annotations

import sqlite3
from pathlib import Path

import session_tracker, costing

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'printbench.db'


def snapshot(limit=100):
    if not DB.exists():
        return {'print_sessions': [], 'print_summary': {}}

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    try:
        session_tracker.ensure_schema(db)
        rows = db.execute('''
          SELECT id,started_at,ended_at,state,outcome,start_progress,end_progress,max_progress,
                 start_layer,end_layer,max_layer,origin_path,filament_type,filament_vendor,
                 filament_profile,planned_filament_g,planned_filament_m,planned_time_sec,
                 actual_time_sec,final_print_state,fail_reason,media_key,final_image,
                 cost_basis,material_price_eur_per_kg,electricity_price_eur_per_kwh,machine_rate_eur_per_hour,
                 margin_pct,estimated_energy_kwh,material_cost_eur,electricity_cost_eur,machine_cost_eur,
                 self_cost_eur,margin_eur,sale_price_eur,energy_is_estimated
          FROM print_sessions ORDER BY id DESC LIMIT ?
        ''', (int(limit),)).fetchall()
        sessions = []
        for row in rows:
            item = dict(row)
            if item.get('origin_path'):
                item['origin_path'] = Path(item['origin_path']).name
            sessions.append(item)

        row = db.execute('''
          SELECT COUNT(*) total,
                 SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END) success,
                 SUM(CASE WHEN outcome='failed' THEN 1 ELSE 0 END) failed,
                 SUM(CASE WHEN outcome='cancelled' THEN 1 ELSE 0 END) cancelled,
                 SUM(CASE WHEN outcome='interrupted' THEN 1 ELSE 0 END) interrupted,
                 SUM(CASE WHEN ended_at IS NULL THEN 1 ELSE 0 END) active,
                 SUM(COALESCE(planned_filament_g,0)) filament_g,
                 SUM(COALESCE(planned_filament_m,0)) filament_m,
                 SUM(COALESCE(actual_time_sec,0)) actual_time_sec,
                 SUM(COALESCE(planned_time_sec,0)) planned_time_sec,
                 SUM(COALESCE(estimated_energy_kwh,0)) estimated_energy_kwh,
                 SUM(COALESCE(self_cost_eur,0)) self_cost_eur,
                 SUM(COALESCE(sale_price_eur,0)) sale_price_eur,
                 MIN(started_at) first_print,
                 MAX(COALESCE(ended_at,started_at)) last_print
          FROM print_sessions
        ''').fetchone()
        summary = dict(row)
        total = int(summary.get('total') or 0)
        active = int(summary.get('active') or 0)
        finished = max(0, total - active)
        success = int(summary.get('success') or 0)
        summary['finished'] = finished
        summary['success_rate'] = round(success / finished * 100, 1) if finished else None
        return {'print_sessions': sessions, 'print_summary': summary, 'cost_config': costing.public_config()}
    finally:
        db.close()
