import sys
import os

# Ensure backend/tests is in path
sys.path.insert(0, os.path.dirname(__file__))

import test_helper

def run():
    print("========================================")
    print("IDPShop Backend Unit Tests Runner")
    print("========================================")

    # Import the test modules
    try:
        import test_auth
        import test_product
        import test_orders
        import test_cart
    except Exception as e:
        print(f"Error importing tests: {e}")
        import traceback
        traceback.print_exc()
        return

    test_modules = [
        ("Auth Tests", test_auth),
        ("Product Tests", test_product),
        ("Orders Tests", test_orders),
        ("Cart Tests", test_cart),
    ]

    total_passed = 0
    total_failed = 0

    for suite_name, module in test_modules:
        print(f"\nRunning {suite_name}:")
        print("-" * 40)
        
        test_functions = [getattr(module, name) for name in dir(module) if name.startswith("test_")]
        
        for func in test_functions:
            func_name = func.__name__
            print(f"Testing {func_name} ... ", end="")
            try:
                func()
                print("PASSED")
                total_passed += 1
            except AssertionError:
                # The assert_equal function has already printed FAILED and the mismatch details
                total_failed += 1
            except Exception as e:
                print("FAILED")
                print(f"Unexpected error: {e}")
                total_failed += 1

    print("\n========================================")
    print("TEST SUMMARY")
    print("========================================")
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    if total_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run()
