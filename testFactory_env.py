import gymnasium as gym
from gymnasium import spaces
import numpy as np

# SECTION 1: THE PHYSICS ENGINE 
def get_pf(P, Q):
    """Calculates Power Factor from Real (P) and Reactive (Q) power."""
    apparent_power = np.sqrt(P**2 + Q**2)
    return P / apparent_power if apparent_power > 0 else 1.0

# SECTION 2: THE GYMNASIUM ENVIRONMENT 
class IndustrialPFEnv(gym.Env):
    """
    Custom Environment for Adaptive Power Factor Correction[cite: 7, 110].
    Models a 100kW Industrial Motor with switchable capacitor banks[cite: 111, 112].
    """
    def __init__(self):
        super(IndustrialPFEnv, self).__init__()
        
        # Machine Specification 
        self.machine_name = "50HP Induction Motor (Simulated)"
        self.P = 100.0  # Real Power in kW
        self.cap_bank_size = 30.0  # kVAR per capacitor bank 
        
        # Action Space: 4 discrete actions [cite: 120]
        self.action_space = spaces.Discrete(4)
        
        # Observation Space: [Current PF, Reactive Demand, Bank Status] 
        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0]), 
            high=np.array([1.0, 500.0, 3.0]), 
            dtype=np.float32
        )

    def _generate_load(self):
        # Baseline inductive load + random fluctuation to mimic machine cycles [cite: 72]
        base_Q = 80.0 
        fluctuation = np.random.uniform(-10, 10)
        return base_Q + fluctuation

    def step(self, action):
        # 1. Generate the 'BEFORE' Variables (Uncorrected State) 
        Q_load = self._generate_load()
        pf_before = get_pf(self.P, Q_load)

        # 2. Apply Correction (The 'Action') [cite: 120]
        active_banks = 0
        if action == 1 or action == 2:
            active_banks = 1
        elif action == 3:
            active_banks = 2
            
        total_correction = active_banks * self.cap_bank_size
        Q_after = Q_load - total_correction
        pf_after = get_pf(self.P, Q_after)

        # 3. Calculate Reward [cite: 124]
        reward = 1.0 if pf_after >= 0.95 else -1.0
        
        # 4. Construct Observation
        obs = np.array([pf_after, Q_after, float(action)], dtype=np.float32)

        # 5. DISPLAY OUTPUT (Verification Proof)
        self._print_comparison(pf_before, Q_load, pf_after, Q_after, action)

        return obs, reward, False, False, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        Q_initial = 80.0
        obs = np.array([get_pf(self.P, Q_initial), Q_initial, 0.0], dtype=np.float32)
        return obs, {}

    def _print_comparison(self, pf_before, Q_before, pf_after, Q_after, action):
        """Prints the Before/After state and the Power Reduction (Savings)."""
        # Calculate Apparent Power (S = sqrt(P^2 + Q^2)) [cite: 35]
        S_before = np.sqrt(Q_before**2 + self.P**2)
        S_after = np.sqrt(Q_after**2 + self.P**2)
        s_reduction = S_before - S_after
        
        active_banks = 2 if action == 3 else (1 if action > 0 else 0)

        print(f"\n ENVIRONMENT STEP (Action: {action} Banks) ")
        print(f"Machine Spec: {self.machine_name} | Rating: {self.P}kW")
        
        print(f"BEFORE CORRECTION")
        print(f"  Real Power (P): {self.P} kW")
        print(f"  Reactive Power (Q): {Q_before:.2f} kVAR")
        print(f"  Apparent Power (S): {S_before:.2f} kVA")
        print(f"  RESULTING PF: {pf_before:.4f}")
        
        print(f"\nAFTER CORRECTION")
        print(f"  Real Power (P): {self.P} kW")
        print(f"  Net Reactive Power (Q): {Q_after:.2f} kVAR")
        print(f"  Apparent Power (S): {S_after:.2f} kVA")
        print(f"  RESULTING PF: {pf_after:.4f}")

        print(f"\nCORRECTION SUMMARY")
        print(f"  Reactive Power Removed: {active_banks * self.cap_bank_size} kVAR")
        print(f"  Total Apparent Power Reduced: {s_reduction:.2f} kVA")
        print(f"  Efficiency Improvement: {((pf_after - pf_before) / pf_before * 100):.2f}%")
        print("-" * 45)

# SECTION 3: RUNNING THE PROOF OF CONCEPT
if __name__ == "__main__":
    env = IndustrialPFEnv()
    
    while True:
        print("\nNEW TEST SIMULATION RUN")
        
        env.reset() 
        
        print("\nTesting Action: 0 Banks...")
        env.step(0)
        
        print("\nTesting Action: 3 Banks...")
        env.step(3)
        
        rerun = input("\nRe-run test simulation with new random loads? (y/n): ").lower()
        if rerun != 'y':
            print("Simulation ended.")
            break