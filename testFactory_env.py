import gymnasium as gym
from gymnasium import spaces
import numpy as np

class PowerFactorEnv(gym.Env):
    """Custom Environment that follows gymnasium interface"""
    metadata = {"render_modes": ["console"]}

    def __init__(self):
        super(PowerFactorEnv, self).__init__()
        
        # Action Space: Two switchable capacitor banks (0 = Off, 1 = On for each)
        # Using MultiBinary for independent ON/OFF control of multiple banks
        self.action_space = spaces.MultiBinary(2) 

        # Observation Space: Power Factor (0 to 1), Reactive Power Demand, 
        # Cap Bank 1 Status (0/1), Cap Bank 2 Status (0/1), Time Index (0 to 24)
        # We use a Box space for continuous and discrete numerical values
        low = np.array([0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        high = np.array([1.0, 10000.0, 1.0, 1.0, 24.0], dtype=np.float32)
        self.observation_space = spaces.Box(low, high, dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Reset the environment to an initial state (e.g., start of a new shift)
        self.current_time = 0.0
        self.cap_banks = np.array([0.0, 0.0], dtype=np.float32)
        
        # Calculate initial power factor and reactive demand using your mathematical models here
        initial_pf = 0.82 
        initial_reactive_power = 1500.0 

        observation = np.array([
            initial_pf, 
            initial_reactive_power, 
            self.cap_banks[0], 
            self.cap_banks[1], 
            self.current_time
        ], dtype=np.float32)
        
        info = {}
        return observation, info

    def step(self, action):
        # 1. Apply the agent's action (switch capacitor banks)
        self.cap_banks = action.astype(np.float32)
        
        # 2. Advance time
        self.current_time += 1.0
        
        # 3. Calculate new electrical behavior (your mathematical load models go here)
        new_pf = 0.96 # Placeholder for the calculated PF after correction
        new_reactive_power = 800.0 # Placeholder
        
        # 4. Calculate Reward 
        # (e.g., positive for PF > 0.95, penalty for switching)
        reward = 1.0 if new_pf >= 0.95 else -1.0
        
        # 5. Check if the episode is done (e.g., end of the 24-hour shift)
        terminated = bool(self.current_time >= 24.0)
        truncated = False 
        
        # 6. Format the observation
        observation = np.array([
            new_pf, 
            new_reactive_power, 
            self.cap_banks[0], 
            self.cap_banks[1], 
            self.current_time
        ], dtype=np.float32)
        
        info = {}
        return observation, reward, terminated, truncated, info

    def render(self):
        # Optional: Print the current state to the console
        pass

# Initialize the environment
env = PowerFactorEnv()
obs, info = env.reset()

print("Initial Observation:", obs)

# Run a quick 5-step test with random actions
for i in range(5):
    random_action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(random_action)
    print(f"Step {i+1} | Action: {random_action} | Reward: {reward} | Obs: {obs}")
    
    if terminated or truncated:
        obs, info = env.reset()