import gymnasium as gym
from gymnasium import spaces
import numpy as np

def get_pf(P, Q):
    """Calculates Power Factor from Real (P) and Reactive (Q) power."""
    apparent_power = np.sqrt(P**2 + Q**2)
    return P / apparent_power if apparent_power > 0 else 1.0


class IndustrialPFEnv(gym.Env):
    def __init__(self):
        super(IndustrialPFEnv, self).__init__()
        
        self.machine_name = "50HP Induction Motor (Simulated)"
        self.P = 100.0                    # Real Power in kW
        self.cap_bank_size = 30.0         # kVAR per bank
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
        """Finds the minimum number of banks needed to reach PF >= 0.95"""
        for banks in range(self.num_banks + 1):
            Q_corrected = Q_fixed - (banks * self.cap_bank_size)
            pf = get_pf(self.P, Q_corrected)
            if pf >= 0.95:
                return banks
        return self.num_banks  # use all banks if target still not reached

    def _print_full_simulation(self, Q_fixed, pf_fixed, S_fixed, active_banks=None, is_initial=False):
        total_correction = active_banks * self.cap_bank_size
        Q_after = Q_fixed - total_correction
        pf_after = get_pf(self.P, Q_after)
        S_after = np.sqrt(self.P**2 + Q_after**2)
        improvement = ((pf_after - pf_fixed) / pf_fixed * 100) if pf_fixed > 0 else 0

        print(f"Machine Specification: {self.machine_name}")
        print(f"Real Power (P)         : {self.P:.1f} kW")

        print(f"\nBEFORE CORRECTION")
        print(f"  Reactive Power (Q)   : {Q_fixed:.2f} kVAR")
        print(f"  Apparent Power (S)   : {S_fixed:.2f} kVA")
        print(f"  Power Factor         : {pf_fixed:.4f}")

        print(f"\nAFTER CORRECTION")
        print(f"  Reactive Power (Q)   : {max(Q_after, 0):.2f} kVAR")
        print(f"  Apparent Power (S)   : {S_after:.2f} kVA")
        print(f"  Corrected PF         : {pf_after:.4f}")
        print(f"  Banks Used           : {active_banks} bank{'s' if active_banks != 1 else ''}")

        print(f"\nCORRECTION SUMMARY")
        print(f"  Reactive Power Removed : {total_correction:.1f} kVAR")
        print(f"  Apparent Power Reduced : {S_fixed - S_after:.2f} kVA")
        print(f"  PF Improvement         : {improvement:.2f}%")

        if is_initial:
            print(f"\n  ★ This is the RECOMMENDED correction.")
            print(f"  → Now manually test banks below to verify this result.")

        print(f"{'='*80}")


if __name__ == "__main__":
    env = IndustrialPFEnv()

    while True:
        print("\nSTARTING NEW TEST SIMULATION")

        Q_fixed = env._generate_load()
        pf_fixed = get_pf(env.P, Q_fixed)
        S_fixed = np.sqrt(env.P**2 + Q_fixed**2)

        # Auto-calculate optimal banks and show initial correction
        optimal_banks = env._get_optimal_banks(Q_fixed)
        env._print_full_simulation(Q_fixed, pf_fixed, S_fixed, 
                                   active_banks=optimal_banks, is_initial=True)

        print("\nYou can now manually test different banks on this SAME load.")
        print(f"★ Try turning ON {optimal_banks} bank{'s' if optimal_banks != 1 else ''} to verify the correction above.\n")

        while True:
            try:
                user_input = input("Enter number of banks to turn ON (0-3) or 'r' for new test: ").strip().lower()

                if user_input == 'r':
                    print("→ Starting new test simulation with fresh load...")
                    break

                active_banks = int(user_input)
                if not (0 <= active_banks <= 3):
                    print("Please enter a number between 0 and 3.")
                    continue

                print(f"\n--- MANUAL TEST: {active_banks} BANK{'S' if active_banks != 1 else ''} ---")
                env._print_full_simulation(Q_fixed, pf_fixed, S_fixed, active_banks=active_banks)

                # Hint to user if they matched the optimal
                manual_pf = get_pf(env.P, Q_fixed - active_banks * env.cap_bank_size)
                if active_banks == optimal_banks:
                    print(f"  ✔ MATCH! This confirms the recommended correction of {optimal_banks} banks.")
                else:
                    print(f"  ℹ Try {optimal_banks} bank{'s' if optimal_banks != 1 else ''} to match the recommended correction.")

            except ValueError:
                print("Invalid input. Please enter 0-3 or 'r'")
                continue

        rerun = input("\nDo you want to rerun with a new random load? (y/n): ").lower()
        if rerun != 'y':
            print("Simulation ended.")
            break