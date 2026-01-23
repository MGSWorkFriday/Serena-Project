# debug_boot.py
import sys
import os
import traceback

print("=== DEBUG DIAGNOSE START ===")
print(f"Map: {os.getcwd()}")

print("\n1. Test import 'resp_rr_param_sets'...")
try:
    import resp_rr_param_sets
    print("   [OK] Module gevonden.")
    try:
        p = resp_rr_param_sets.get_params("v1_default")
        print(f"   [OK] Config geladen. Buffer size: {getattr(p, 'BUFFER_SIZE', '???')}")
    except Exception as e:
        print(f"   [FOUT] get_params crasht: {e}")
except Exception as e:
    print(f"   [FOUT] Import mislukt: {e}")
    traceback.print_exc()

print("\n2. Test import 'server.session'...")
try:
    from server import session
    print("   [OK] Session module geladen.")
except Exception as e:
    print("   [FOUT] CRASH IN SESSION.PY:")
    traceback.print_exc()

print("\n3. Test import 'server.main'...")
try:
    from server import main
    print("   [OK] Main module geladen.")
except Exception as e:
    print("   [FOUT] CRASH IN MAIN.PY:")
    traceback.print_exc()

print("\n=== EINDE DIAGNOSE ===")
input("Druk op Enter om te sluiten...")