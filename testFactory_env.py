import gymnasium as gym
from gymnasium import spaces
import numpy as np

# SECTION 1: THE PHYSICS ENGINE 
def get_pf(P, Q):
    """Calculates Power Factor from Real (P) and Reactive (Q) power."""
    # Standard Electrical Formula: PF = P / S, where S = sqrt(P^2 + Q^2)
    apparent_power = np.sqrt(P**2 + Q**2)
    return P / apparent_power if apparent_power > 0 else 1.0

#  SECTION 2: THE GYMNASIUM ENVIRONMENT 
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
        # 0: No Banks, 1: Bank A, 2: Bank B, 3: Both Banks
        self.action_space = spaces.Discrete(4)
        
        # Observation Space: [Current PF, Reactive Demand, Bank Status] 
        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0]), 
            high=np.array([1.0, 500.0, 3.0]), 
            dtype=np.float32
        )

    def _generate_load(self):
        # Baseline inductive load + random fluctuation to mimic machine cycles
        base_Q = 80.0 
        fluctuation = np.random.uniform(-10, 10)
        return base_Q + fluctuation

    def step(self, action):
        # 1. Generate the 'BEFORE' Variables (Uncorrected State) 
        Q_load = self._generate_load()
        pf_before = get_pf(self.P, Q_load)

        # 2. Apply Correction (The 'Action')
        # Map discrete action to number of active banks
        active_banks = 0
        if action == 1 or action == 2:
            active_banks = 1
        elif action == 3:
            active_banks = 2
            
        total_correction = active_banks * self.cap_bank_size
        Q_after = Q_load - total_correction
        pf_after = get_pf(self.P, Q_after)

        # 3. Calculate Reward 
        # Positive reward for PF > 0.95, penalties for low PF or switching
        reward = 1.0 if pf_after >= 0.95 else -1.0
        
        # 4. Construct Observation for the Agent
        obs = np.array([pf_after, Q_after, float(action)], dtype=np.float32)

        # 5. DISPLAY OUTPUT (Verification Proof for Critique)
        self._print_comparison(pf_before, Q_load, pf_after, Q_after, action)

        return obs, reward, False, False, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        Q_initial = 80.0
        obs = np.array([get_pf(self.P, Q_initial), Q_initial, 0.0], dtype=np.float32)
        return obs, {}

    def _print_comparison(self, pf_before, Q_before, pf_after, Q_after, action):
        """Prints the Before/After state requested by the user."""
        print(f"\n--- ENVIRONMENT STEP (Action: {action} Banks) ---")
        print(f"Machine Spec: {self.machine_name} | Rating: {self.P}kW")
        
        print(f"[BEFORE CORRECTION]")
        print(f"  Real Power (P): {self.P} kW")
        print(f"  Reactive Power (Q): {Q_before:.2f} kVAR")
        print(f"  RESULTING PF: {pf_before:.4f}")
        
        print(f"[AFTER CORRECTION]")
        print(f"  Real Power (P): {self.P} kW")
        print(f"  Net Reactive Power (Q): {Q_after:.2f} kVAR")
        print(f"  RESULTING PF: {pf_after:.4f}")
        print("-" * 40)

# SECTION 3: RUNNING THE PROOF OF CONCEPT
if __name__ == "__main__":
    # Initialize the verified environment 
    env = IndustrialPFEnv()
    obs, info = env.reset()
    
    print("Starting Proof of Concept Run...")
    
    # Test Scenario 1: No Correction
    env.step(0)
    
    # Test Scenario 2: Full Correction (Both Banks)
    env.step(3)