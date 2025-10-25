#!/usr/bin/env python3

# {{ ansible_managed }}
# oxlorg.haproxy_waf_coraza

# Copyright: Rath Pascal Rene
# License: MIT

from pathlib import Path
from sys import exit as sys_exit
from argparse import ArgumentParser

STATE_DISABLE = 'disable'
STATE_REPLACE = 'replace'
NEWLINE_CHAR = '\\n'
RULE_START = 'SecRule '
RULE_ID_START = '"id:'


def _error(msg: str):
    print(f'ERROR: {msg}')
    sys_exit(1)


# pylint: disable=E0606,R0912
def main():
    if not Path(args.rule_file).is_file():
        _error('File not found')

    with open(args.rule_file, 'r', encoding='utf-8') as f:
        in_rules = f.readlines()

    line_from = -1
    for line_nr, line in enumerate(in_rules):
        if line.find(f'{RULE_ID_START}{args.rule_id}') != -1:
            if line.startswith(RULE_START):
                line_from = line_nr

            else:
                line_from = line_nr - 1

            break

    if line_from == -1:
        _error('Rule not found')

    out_rules = []
    done = False
    changed = False

    for line_nr, line in enumerate(in_rules):
        if not done and line_nr >= line_from:
            if not line_nr == line_from and line.startswith(RULE_START):
                # insert new
                if args.state == STATE_REPLACE:
                    out_rules.extend(
                        [f'{line}\n' for line in args.rule_replacement.split(NEWLINE_CHAR)]
                    )

                out_rules.append(line)

                done = True
                if changed:
                    print(f'Rule {args.rule_id} {args.state}d')

                continue

            # comment-out
            if args.state == STATE_DISABLE:
                if not line.startswith('#'):
                    line = f'#{line}'
                    changed = True

            # remove old
            elif args.state == STATE_REPLACE:
                continue

            # comment-in
            else:
                if line.startswith('#'):
                    line = f'{line[1:]}'
                    changed = True

        out_rules.append(line)

    if not args.check_mode:
        with open(args.rule_file, 'w', encoding='utf-8') as f:
            f.writelines(out_rules)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '-c', '--check-mode', type=bool,
        default=False, help='Dry-run check-mode - changes are not written',
    )
    parser.add_argument(
        '-f', '--rule-file', type=str,
        required=True, help='Full path to the rule config-file',
    )
    parser.add_argument(
        '-i', '--rule-id', type=str,
        required=True, help='ID of the Rule to modify',
    )
    parser.add_argument(
        '-s', '--state', type=str, choices=['enable', STATE_DISABLE, STATE_REPLACE],
        required=True, help='ID of the Rule to modify'
    )
    parser.add_argument(
        '-r', '--rule-replacement', type=str, help='ID of the Rule to modify',
    )

    args = parser.parse_args()

    if args.state == STATE_REPLACE:
        if args.rule_replacement is None:
            _error('No Rule-replacement provided')

        if args.rule_replacement.find(f'{RULE_ID_START}{args.rule_id}') == -1:
            _error('Missing rule-id in Rule-replacement')

        if not args.rule_replacement.startswith(RULE_START):
            _error('Missing SecRule-prefix in Rule-replacement')

        if not args.rule_replacement.endswith('"'):
            _error('Missing end-quote in Rule-replacement')

    main()
