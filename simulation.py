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

        self.machine_name  = "50HP Induction Motor (Simulated)"
        self.P             = 37.3
        self.voltage       = 460
        self.rated_current = 52.0
        self.efficiency    = 0.92
        self.rated_pf      = 0.85

        self.num_banks     = 3

        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0]),
            high=np.array([1.0, 500.0, 3.0]),
            dtype=np.float32
        )

    def _generate_load(self, load_percent=None):
        load_pf_curve = {
            25:  0.55,
            50:  0.73,
            75:  0.80,
            100: 0.85
        }
        if load_percent is None:
            load_percent = int(np.random.choice([25, 50, 75, 100]))  # ← cast to int

        pf_at_load = load_pf_curve[load_percent]
        P_actual   = self.P * (load_percent / 100)
        theta      = np.arccos(pf_at_load)
        Q_actual   = P_actual * np.tan(theta)
        return Q_actual, P_actual, load_percent

    def _get_required_kvar(self, P, pf_current, pf_target=0.95):
        """IEEE formula: Q_correction = P × (tan θ1 - tan θ2)"""
        theta1       = np.arccos(pf_current)
        theta2       = np.arccos(pf_target)
        Q_correction = P * (np.tan(theta1) - np.tan(theta2))
        return round(Q_correction, 2)

    STANDARD_BANK_SIZES = [2.5, 5, 7.5, 10, 12.5, 15, 20, 25, 30, 40, 50, 60, 75, 100]

    def _select_bank_size(self, Q_required):
        """Pick smallest standard bank size that meets or exceeds requirement."""
        for size in self.STANDARD_BANK_SIZES:
            if size >= Q_required:
                return size
        return self.STANDARD_BANK_SIZES[-1]

    def _calculate_penalty(self, pf, monthly_kwh):
        """MERALCO PF penalty: surcharge if PF < 0.85"""
        base_rate    = 12.00    # PHP per kWh
        monthly_bill = monthly_kwh * base_rate
        if pf < 0.85:
            surcharge_rate = (0.85 / pf) - 1
            return round(monthly_bill * surcharge_rate, 2)
        return 0.0

    def _get_true_pf(self, displacement_pf, thd=0.0):
        """True PF = Displacement PF × Distortion Factor"""
        distortion_factor = 1 / np.sqrt(1 + thd**2)
        return round(displacement_pf * distortion_factor, 4)

    def _get_optimal_banks(self, Q_fixed, P_actual, pf_fixed):
        Q_required = self._get_required_kvar(P_actual, pf_fixed)
        for banks in range(self.num_banks + 1):
            Q_corrected = Q_fixed - (banks * self.cap_bank_size)
            pf = get_pf(P_actual, max(Q_corrected, 0))  # ← clamp Q to 0, prevent going negative
            if pf >= 0.95:
                return banks, Q_required
        return self.num_banks, Q_required

    def _save_simulation_data(self, Q_fixed, pf_fixed, S_fixed, P_actual,
                               load_percent, optimal_banks, Q_required):
        total_correction = optimal_banks * self.cap_bank_size
        Q_after          = Q_fixed - total_correction
        pf_after         = get_pf(P_actual, Q_after)
        S_after          = np.sqrt(P_actual**2 + Q_after**2)
        improvement      = ((pf_after - pf_fixed) / pf_fixed * 100) if pf_fixed > 0 else 0

        data = {
            "machine_name"   : self.machine_name,
            "P"              : P_actual,                # ← actual P, not rated
            "P_rated"        : self.P,
            "load_percent"   : load_percent,
            "cap_bank_size"  : self.cap_bank_size,
            "num_banks"      : self.num_banks,
            "Q_fixed"        : round(Q_fixed, 4),
            "pf_fixed"       : round(pf_fixed, 4),
            "S_fixed"        : round(S_fixed, 4),
            "Q_required_ieee": Q_required,              # ← IEEE exact kVAR
            "optimal_banks"  : optimal_banks,
            "recommended": {
                "Q_after"        : round(max(Q_after, 0), 4),
                "S_after"        : round(S_after, 4),
                "pf_after"       : round(pf_after, 4),
                "kvar_removed"   : round(total_correction, 4),
                "kva_reduced"    : round(max(0.0, S_fixed - S_after), 4),
                "pf_improvement" : round(improvement, 4)
            }
        }

        with open("simulation_data.json", "w") as f:
            json.dump(data, f, indent=4)
        print(f"  [✔] Simulation data saved → simulation_data.json")

    def _print_simulation(self, Q_fixed, pf_fixed, S_fixed, P_actual,
                           load_percent, optimal_banks, Q_required):
        total_correction = optimal_banks * self.cap_bank_size
        Q_after          = Q_fixed - total_correction
        pf_after         = get_pf(P_actual, Q_after)
        S_after          = np.sqrt(P_actual**2 + Q_after**2)
        improvement      = ((pf_after - pf_fixed) / pf_fixed * 100) if pf_fixed > 0 else 0

        print(f"Machine Specification  : {self.machine_name}")
        print(f"Load Condition         : {load_percent}% load ({P_actual:.2f} kW)")
        print(f"Voltage                : {self.voltage} V")

        print(f"\nBEFORE CORRECTION")
        print(f"  Real Power (P)       : {P_actual:.2f} kW")
        print(f"  Reactive Power (Q)   : {Q_fixed:.2f} kVAR")
        print(f"  Apparent Power (S)   : {S_fixed:.2f} kVA")
        print(f"  Power Factor         : {pf_fixed:.4f}")

        print(f"\nIEEE REQUIRED CORRECTION")
        print(f"  Exact kVAR Needed    : {Q_required:.2f} kVAR")
        print(f"  Installed Correction : {total_correction:.1f} kVAR ({optimal_banks} banks × {self.cap_bank_size} kVAR)")

        print(f"\nAFTER CORRECTION  ★ RECOMMENDED")
        print(f"  Reactive Power (Q)   : {max(Q_after, 0):.2f} kVAR")
        print(f"  Apparent Power (S)   : {S_after:.2f} kVA")
        print(f"  Corrected PF         : {pf_after:.4f}")
        print(f"  Banks Used           : {optimal_banks} bank{'s' if optimal_banks != 1 else ''}")

        print(f"\nCORRECTION SUMMARY")
        print(f"  Reactive Power Removed : {total_correction:.1f} kVAR")
        print(f"  Apparent Power Reduced : {max(0.0, S_fixed - S_after):.2f} kVA")
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

        Q_fixed, P_actual, load_percent = env._generate_load()
        pf_fixed = get_pf(P_actual, Q_fixed)
        S_fixed  = np.sqrt(P_actual**2 + Q_fixed**2)

        Q_required_for_size = env._get_required_kvar(P_actual, pf_fixed)
        env.cap_bank_size = env._select_bank_size(Q_required_for_size)

        optimal_banks, Q_required = env._get_optimal_banks(Q_fixed, P_actual, pf_fixed)

        env._print_simulation(Q_fixed, pf_fixed, S_fixed,
                               P_actual, load_percent, optimal_banks, Q_required)

        env._save_simulation_data(Q_fixed, pf_fixed, S_fixed,
                                   P_actual, load_percent, optimal_banks, Q_required)

        rerun = input("\nDo you want to run a new simulation? (y/n): ").lower()
        if rerun != 'y':
            print("Simulation ended. You can now run manual_test.py to verify.")
            break