from __future__ import annotations
import argparse, json
import command_engine


def main() -> int:
    p = argparse.ArgumentParser(description='PRINTBENCH fail-closed P2S control CLI')
    sub = p.add_subparsers(dest='op', required=True)
    sub.add_parser('capabilities')

    prev = sub.add_parser('preview')
    prev.add_argument('command', choices=sorted(command_engine.SPECS))
    prev.add_argument('--args', default='{}', help='JSON object with validated command arguments')

    run = sub.add_parser('execute')
    run.add_argument('command', choices=sorted(command_engine.SPECS))
    run.add_argument('--args', default='{}', help='JSON object with validated command arguments')
    run.add_argument('--apply', action='store_true', help='Required in addition to local write policy')
    run.add_argument('--confirm', action='store_true', help='Required for destructive commands')

    ns = p.parse_args()
    if ns.op == 'capabilities':
        print(json.dumps(command_engine.capabilities(), ensure_ascii=False, indent=2))
        return 0

    try:
        args = json.loads(ns.args)
    except json.JSONDecodeError as exc:
        p.error(f'invalid --args JSON: {exc}')
    if not isinstance(args, dict):
        p.error('--args must be a JSON object')

    if ns.op == 'preview':
        print(json.dumps(command_engine.preview(ns.command, args), ensure_ascii=False, indent=2))
        return 0

    if not ns.apply:
        print(json.dumps(command_engine.preview(ns.command, args), ensure_ascii=False, indent=2))
        print('NOT SENT: add --apply; local policy must also enable this command.')
        return 2

    try:
        result = command_engine.execute(ns.command, args, confirm=ns.confirm)
    except (ValueError, PermissionError, RuntimeError) as exc:
        print(json.dumps({'ok': False, 'error': type(exc).__name__, 'detail': str(exc)}, ensure_ascii=False))
        return 3
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get('ok') else 4


if __name__ == '__main__':
    raise SystemExit(main())
