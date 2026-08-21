#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from synasc2026.experiments.verify_experiment import main


if __name__ == "__main__":
    raise SystemExit(main())
