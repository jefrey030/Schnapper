#!/usr/bin/env python3
"""Read-only E2E prerequisites. Never starts a model or generates consent."""
import json
import pathlib
import shutil
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'team'))
from diagnose_local import diagnose
from operator_approval import pruefe_freigabe
from ki import KINichtVerfuegbar


def main():
    result = diagnose()
    try:
        pruefe_freigabe()
        approved = True
    except KINichtVerfuegbar:
        approved = False
    result.update(operator_approval_valid=approved,
                  alternative_llama_server_installed=shutil.which('llama-server') is not None,
                  android_adb_available=shutil.which('adb') is not None,
                  real_inference_executed=False, security_release_approved=False)
    result['e2e_ready'] = result['startbereit'] and approved
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['e2e_ready'] else 2


if __name__ == '__main__':
    sys.exit(main())
