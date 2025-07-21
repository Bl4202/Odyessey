"""
Test script to verify the noise module is working.
"""

import traceback

try:
    import noise
    print("Successfully imported noise module")
    
    # Test basic noise function
    test_value = noise.pnoise2(0.5, 0.5)
    print(f"Noise test value: {test_value}")
    
    # If we get here, the noise module is working
    print("Noise module is working correctly")
    
except Exception as e:
    print(f"Error testing noise module: {e}")
    traceback.print_exc()