import gymnasium as gym
from gymnasium import spaces
import numpy as np
import json
import os

def get_pf(P, Q):
    apparent_power = np.sqrt(P**2 + Q**2)
    return P / apparent_power if apparent_power > 0 else 1.0


class IndustrialPFEnv(gym.Env):
    def __init__(self):
        super(IndustrialPFEnv, self).__init__()
        self.machine_name = "50HP Induction Motor (Simulated)"
        self.P = 100.0
        self.cap_bank_size = 30.0
        self.num_banks = 3
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0]),
            high=np.array([1.0, 500.0, 3.0]),
            dtype=np.float32
        )

    def _generate_load(self):
        base_Q = 80.0
        fluctuation = np.random.uniform(-15, 15)
        return base_Q + fluctuation

    def _get_optimal_banks(self, Q_fixed):
        for banks in range(self.num_banks + 1):
            Q_corrected = Q_fixed - (banks * self.cap_bank_size)
            pf = get_pf(self.P, Q_corrected)
            if pf >= 0.95:
                return banks
        return self.num_banks

    def _save_simulation_data(self, Q_fixed, pf_fixed, S_fixed, optimal_banks):
        """Saves current simulation data to JSON for manual_test.py to read."""
        total_correction = optimal_banks * self.cap_bank_size
        Q_after = Q_fixed - total_correction
        pf_after = get_pf(self.P, Q_after)
        S_after = np.sqrt(self.P**2 + Q_after**2)
        improvement = ((pf_after - pf_fixed) / pf_fixed * 100) if pf_fixed > 0 else 0

        data = {
            "machine_name"      : self.machine_name,
            "P"                 : self.P,
            "cap_bank_size"     : self.cap_bank_size,
            "num_banks"         : self.num_banks,
            "Q_fixed"           : round(Q_fixed, 4),
            "pf_fixed"          : round(pf_fixed, 4),
            "S_fixed"           : round(S_fixed, 4),
            "optimal_banks"     : optimal_banks,
            "recommended": {
                "Q_after"       : round(max(Q_after, 0), 4),
                "S_after"       : round(S_after, 4),
                "pf_after"      : round(pf_after, 4),
                "kvar_removed"  : round(total_correction, 4),
                "kva_reduced"   : round(S_fixed - S_after, 4),
                "pf_improvement": round(improvement, 4)
            }
        }

        with open("simulation_data.json", "w") as f:
            json.dump(data, f, indent=4)

        print(f"  [✔] Simulation data saved → simulation_data.json")

    def _print_simulation(self, Q_fixed, pf_fixed, S_fixed, optimal_banks):
        total_correction = optimal_banks * self.cap_bank_size
        Q_after = Q_fixed - total_correction
        pf_after = get_pf(self.P, Q_after)
        S_after = np.sqrt(self.P**2 + Q_after**2)
        improvement = ((pf_after - pf_fixed) / pf_fixed * 100) if pf_fixed > 0 else 0

        print(f"Machine Specification  : {self.machine_name}")
        print(f"Real Power (P)         : {self.P:.1f} kW")

        print(f"\nBEFORE CORRECTION")
        print(f"  Reactive Power (Q)   : {Q_fixed:.2f} kVAR")
        print(f"  Apparent Power (S)   : {S_fixed:.2f} kVA")
        print(f"  Power Factor         : {pf_fixed:.4f}")

        print(f"\nAFTER CORRECTION  ★ RECOMMENDED")
        print(f"  Reactive Power (Q)   : {max(Q_after, 0):.2f} kVAR")
        print(f"  Apparent Power (S)   : {S_after:.2f} kVA")
        print(f"  Corrected PF         : {pf_after:.4f}")
        print(f"  Banks Used           : {optimal_banks} bank{'s' if optimal_banks != 1 else ''}")

        print(f"\nCORRECTION SUMMARY")
        print(f"  Reactive Power Removed : {total_correction:.1f} kVAR")
        print(f"  Apparent Power Reduced : {S_fixed - S_after:.2f} kVA")
        print(f"  PF Improvement         : {improvement:.2f}%")
        print(f"\n  → Run manual_test.py to manually verify this result.")
        print(f"{'='*80}")

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        return None, {}


if __name__ == "__main__":
    env = IndustrialPFEnv()

    while True:
        print("\nSTARTING NEW TEST SIMULATION")

        Q_fixed = env._generate_load()
        pf_fixed = get_pf(env.P, Q_fixed)
        S_fixed = np.sqrt(env.P**2 + Q_fixed**2)

        optimal_banks = env._get_optimal_banks(Q_fixed)
        env._print_simulation(Q_fixed, pf_fixed, S_fixed, optimal_banks)

        # Save to JSON so manual_test.py can read it
        env._save_simulation_data(Q_fixed, pf_fixed, S_fixed, optimal_banks)

        rerun = input("\nDo you want to run a new simulation? (y/n): ").lower()
        if rerun != 'y':
            print("Simulation ended. You can now run manual_test.py to verify.")
            break