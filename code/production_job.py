from __future__ import annotations
import argparse
from production_pipeline import run

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--now', action='store_true', help='Generate through now, without changing the schedule')
    args = parser.parse_args()
    print(run(manual=args.now))
