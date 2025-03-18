import wave
import numpy as np
import os

# Create a simple subtle eating sound
def create_eat_dot_sound():
    # Parameters
    sample_rate = 44100
    duration = 0.15  # Increased from 0.1 to 0.15 seconds
    frequency = 300  # Lowered base frequency for less high-pitched sound
    
    # Generate time array
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Create a signal with decreasing amplitude but slower decay
    # Reduced decay rate from -10 to -7 for more audible sound
    # Added slight pitch bend by varying frequency over time
    freq_mod = 1 + 0.5 * t/duration  # Frequency modulation factor
    note = np.sin(2 * np.pi * frequency * t * freq_mod) * np.exp(-7 * t)
    
    # Convert to 16-bit PCM
    audio = note * 32767 / np.max(np.abs(note))
    audio = audio.astype(np.int16)
    
    # Save as WAV file
    output_file = os.path.join(os.path.dirname(__file__), 'eat_dot.wav')
    with wave.open(output_file, 'w') as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        wav.writeframes(audio.tobytes())
    
    print(f"Sound file created at {output_file}")

if __name__ == "__main__":
    create_eat_dot_sound() 