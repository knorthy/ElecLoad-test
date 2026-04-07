import numpy as np
import json
import os

def get_pf(P, Q):
    apparent_power = np.sqrt(P**2 + Q**2)
    return P / apparent_power if apparent_power > 0 else 1.0

def load_simulation_data():
    """Loads the latest simulation data from simulation.py's output."""
    if not os.path.exists("simulation_data.json"):
        print("  [!] No simulation data found.")
        print("  → Please run simulation.py first to generate a simulation.")
        return None

    with open("simulation_data.json", "r") as f:
        data = json.load(f)

    # Guard against stale JSON from an older version of simulation.py
    required_fields = ["load_percent", "P", "Q_fixed", "S_fixed", "pf_fixed",
                       "cap_bank_size", "optimal_banks", "Q_required_ieee"]
    missing = [field for field in required_fields if field not in data]
    if missing:
        print(f"  [!] Outdated simulation_data.json (missing: {', '.join(missing)}).")
        print(f"  → Please delete simulation_data.json and re-run simulation.py.")
        return None

    return data

    with open("simulation_data.json", "r") as f:
        return json.load(f)

def print_manual_test(data, active_banks):
    P             = data["P"]               # ← now uses P_actual, not rated P
    Q_fixed       = data["Q_fixed"]
    pf_fixed      = data["pf_fixed"]
    S_fixed       = data["S_fixed"]
    cap_bank_size = data["cap_bank_size"]
    optimal_banks = data["optimal_banks"]
    Q_required    = data["Q_required_ieee"] # ← new IEEE field

    total_correction = active_banks * cap_bank_size
    Q_after          = Q_fixed - total_correction
    pf_after         = get_pf(P, Q_after)
    S_after          = np.sqrt(P**2 + Q_after**2)
    improvement      = ((pf_after - pf_fixed) / pf_fixed * 100) if pf_fixed > 0 else 0

    print(f"\n--- MANUAL TEST: {active_banks} BANK{'S' if active_banks != 1 else ''} ---")
    print(f"  Real Power (P)         : {P:.2f} kW")
    print(f"  Reactive Power (Q)     : {max(Q_after, 0):.2f} kVAR")
    print(f"  Apparent Power (S)     : {S_after:.2f} kVA")
    print(f"  Corrected PF           : {pf_after:.4f}")
    print(f"  Banks Used             : {active_banks} bank{'s' if active_banks != 1 else ''}")

    print(f"\n  Reactive Power Removed : {total_correction:.1f} kVAR")
    print(f"  Apparent Power Reduced : {max(0.0, S_fixed - S_after):.2f} kVA")
    print(f"  PF Improvement         : {improvement:.2f}%")

    # ── VERIFICATION AGAINST RECOMMENDED ─────────────────────────
    if active_banks == optimal_banks:
        print(f"\n  ✔ MATCH! Your manual test confirms the recommended correction.")
        print(f"  ✔ IEEE required {Q_required:.2f} kVAR — you applied {total_correction:.1f} kVAR.")
    elif pf_after >= 0.95:
        print(f"\n  ✔ PF target reached!")
        print(f"  ℹ But recommended uses {optimal_banks} bank{'s' if optimal_banks != 1 else ''} (more efficient).")
        print(f"  ℹ IEEE exact requirement was {Q_required:.2f} kVAR.")
    else:
        print(f"\n  ✘ PF target NOT reached.")
        print(f"  → Try {optimal_banks} bank{'s' if optimal_banks != 1 else ''} to match the recommendation.")
        print(f"  → IEEE exact requirement is {Q_required:.2f} kVAR.")
    # ─────────────────────────────────────────────────────────────

    print(f"{'='*80}")


if __name__ == "__main__":
    print("\nMANUAL TESTING FILE")
    print("  Fetching latest simulation data from simulation.py...\n")

    data = load_simulation_data()
    if data is None:
        exit()

    def display_loaded_data(data):
        """Prints the loaded simulation reference."""
        print(f"{'='*80}")
        print(f"LOADED SIMULATION DATA")
        print(f"  Machine              : {data['machine_name']}")
        print(f"  Load Condition       : {data['load_percent']}% load ({data['P']:.2f} kW)")  # ← new
        print(f"  Reactive Power (Q)   : {data['Q_fixed']} kVAR")
        print(f"  Apparent Power (S)   : {data['S_fixed']} kVA")
        print(f"  Power Factor         : {data['pf_fixed']}")
        print(f"\n  ★ RECOMMENDED CORRECTION (IEEE)")
        print(f"  Exact kVAR Needed    : {data['Q_required_ieee']:.2f} kVAR")  # ← new
        print(f"  Corrected PF         : {data['recommended']['pf_after']}")
        print(f"  Banks Recommended    : {data['optimal_banks']} bank{'s' if data['optimal_banks'] != 1 else ''}")
        print(f"{'='*80}")
        print(f"\nNow manually test banks on this SAME load.")
        print(f"★ Try {data['optimal_banks']} bank{'s' if data['optimal_banks'] != 1 else ''} to verify the recommended correction.\n")

    display_loaded_data(data)

    while True:
        try:
            user_input = input(f"Enter number of banks (0-{data['num_banks']}), 'r' to reload latest data, or 'q' to quit: ").strip().lower()

            if user_input == 'q':
                print("Manual testing ended.")
                break

            elif user_input == 'r':
                print("\n  Reloading latest simulation data...\n")
                data = load_simulation_data()
                if data is None:
                    break
                display_loaded_data(data)   # ← shows full summary after reload
                continue

            active_banks = int(user_input)
            if not (0 <= active_banks <= data["num_banks"]):
                print(f"  Please enter a number between 0 and {data['num_banks']}.")
                continue

            print_manual_test(data, active_banks)

        except ValueError:
            print("  Invalid input. Please enter 0-3, 'r' to reload, or 'q' to quit.")
            continue