from __future__ import annotations
import argparse
from production_pipeline import run, run_style_test

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--now', action='store_true', help='Generate through now, without changing the schedule')
    parser.add_argument('--style-test', metavar='STYLE', help='Generate a new interpretation from previous heard birds without resetting the daily observation window')
    args = parser.parse_args()
    if args.style_test:
        print(run_style_test(style_name=args.style_test))
    else:
        print(run(manual=args.now))
