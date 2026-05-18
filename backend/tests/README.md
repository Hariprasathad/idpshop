# 🧪 IDPShop Backend Unit Testing Suite

Welcome to the professional unit testing suite for the IDPShop backend Lambda handlers. This system is designed to provide rapid, isolated, and reliable test feedback without requiring live AWS credentials or making network requests to actual DynamoDB tables.

## 📁 Architecture Structure

All tests are placed in the `backend/tests/` directory:

```text
backend/tests/
├── run_tests.py       # Custom fast test runner with human-friendly output
├── test_helper.py     # Setup for mocking sys.path, boto3, jwt, and assertions
├── test_auth.py       # Unit tests for registration and login handlers
├── test_product.py    # Unit tests for product browsing, searching, and pricing
├── test_orders.py     # Unit tests for order processing and inventory protection
└── test_cart.py       # Unit tests for shopping cart operations and limits
```

---

## ⚙️ How it Works

### 1. In-Memory Mocking (`test_helper.py`)
To prevent Lambda handlers from trying to call AWS DynamoDB during testing, `test_helper.py` intercepts package imports via `sys.modules`. It replaces `boto3`, `boto3.dynamodb`, and nested expressions with fully controlled, pre-configured `unittest.mock.MagicMock` objects.
It also includes an in-memory lightweight implementation of `Key` and `Attr` to allow complex filter expressions to run flawlessly without third-party module issues.

### 2. Custom AssertionError Format
The test runner formats and displays failures exactly as specified:
* **PASSED**: Test runs to completion without raising exceptions.
* **FAILED**: Prints `FAILED` and shows the detailed discrepancy (`Expected X but got Y`).

---

## 🏃 Running the Tests

To run the unit tests, execute `run_tests.py` using Python:

```bash
python backend/tests/run_tests.py
```

### 📊 Current Test Coverage (16 Cases)

| Test Module | Function | Description | Status |
|---|---|---|---|
| **Auth** | `test_login_missing_fields` | Verifies 400 Bad Request on empty login fields | ✅ PASSED |
| | `test_login_invalid_credentials` | Verifies 401 Unauthorized on incorrect passwords | ✅ PASSED |
| | `test_login_success` | Verifies 200 OK on correct login and token generation | ✅ PASSED |
| | `test_register_missing_fields` | Verifies 400 Bad Request on empty registration fields | ✅ PASSED |
| | `test_register_user_exists` | Verifies 400 Bad Request if email is already taken | ✅ PASSED |
| | `test_register_success` | Verifies 210 Created and database insertion | ✅ PASSED |
| **Product**| `test_get_products_list` | Tests pagination, reviews integration, and hides out-of-stock items | ✅ PASSED |
| | `test_search_products` | Tests filtering products by keyword match (name/description) | ✅ PASSED |
| **Orders** | `test_get_orders_empty` | Verifies empty lists return a 200 with an empty list structure | ✅ PASSED |
| | `test_get_orders_list` | Verifies list retrieval and checks if order has reviews attached | ✅ PASSED |
| | `test_create_order_insufficient_stock` | Prevents checkout if order quantity exceeds warehouse stock | ✅ PASSED |
| | `test_create_order_success` | Tests successful checkout, stock decrement, and correct dynamic discounts | ✅ PASSED |
| **Cart** | `test_get_cart_empty` | Verifies empty list return on fresh accounts | ✅ PASSED |
| | `test_add_to_cart_success` | Verifies 201 Created and correct price storage | ✅ PASSED |
| | `test_add_to_cart_limit_reached`| Enforces e-commerce safety by capping cart sizes at 10 items | ✅ PASSED |
| | `test_remove_from_cart` | Verifies DELETE requests correctly remove items | ✅ PASSED |

---

## 🛠️ Adding New Tests

Simply add functions starting with `test_` inside any of the `test_*.py` files, import `assert_equal` from `test_helper`, and the test runner will automatically pick them up and run them!

Example:
```python
from test_helper import assert_equal

def test_my_new_feature():
    value = 5 + 5
    assert_equal(value, 10)
```
