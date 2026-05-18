import sys
import os
from unittest.mock import MagicMock

# Add all handler directories to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(backend_dir, 'auth', 'login-package'))
sys.path.append(os.path.join(backend_dir, 'auth', 'register-package'))
sys.path.append(os.path.join(backend_dir, 'product'))
sys.path.append(os.path.join(backend_dir, 'orders'))
sys.path.append(os.path.join(backend_dir, 'cart'))

# Set environment variables for handlers
os.environ['SECRET_KEY'] = 'test_secret_key'
os.environ['USERS_TABLE'] = 'test-users'
os.environ['PRODUCTS_TABLE'] = 'test-products'
os.environ['ORDERS_TABLE'] = 'test-orders'
os.environ['REVIEWS_TABLE'] = 'test-reviews'
os.environ['CART_TABLE'] = 'test-cart'
os.environ['WISHLIST_TABLE'] = 'test-wishlist'

# Setup a mock Key/Attr implementation to avoid dependencies on live boto3
class MockCondition:
    def __init__(self, name):
        self.name = name
    def eq(self, value):
        return self
    def __getattr__(self, name):
        return lambda *args, **kwargs: self

Key = MockCondition
Attr = MockCondition

# Mock boto3
mock_boto3 = MagicMock()
mock_dynamodb = MagicMock()

# Setup table mocks
mock_users_table = MagicMock()
mock_products_table = MagicMock()
mock_orders_table = MagicMock()
mock_reviews_table = MagicMock()
mock_cart_table = MagicMock()

def get_table_mock(table_name):
    if 'users' in table_name:
        return mock_users_table
    elif 'product' in table_name:
        return mock_products_table
    elif 'order' in table_name:
        return mock_orders_table
    elif 'review' in table_name:
        return mock_reviews_table
    elif 'cart' in table_name:
        return mock_cart_table
    return MagicMock()

mock_dynamodb.Table.side_effect = get_table_mock
mock_boto3.resource.return_value = mock_dynamodb

# Populate sys.modules to mock imports correctly
sys.modules['boto3'] = mock_boto3

mock_dynamodb_module = MagicMock()
mock_conditions_module = MagicMock()
mock_conditions_module.Key = Key
mock_conditions_module.Attr = Attr

sys.modules['boto3.dynamodb'] = mock_dynamodb_module
sys.modules['boto3.dynamodb.conditions'] = mock_conditions_module

# Custom assert helper matching the exact format requested
def assert_equal(actual, expected, message=""):
    if actual != expected:
        print(f"FAILED")
        print(f"Expected {expected} but got {actual}")
        if message:
            print(f"Message: {message}")
        raise AssertionError(f"Expected {expected} but got {actual}")
