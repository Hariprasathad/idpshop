import json
import jwt
from test_helper import assert_equal, mock_orders_table, mock_products_table, mock_reviews_table
from backend.orders import order_handler

SECRET_KEY = "test_secret_key"

def get_auth_headers(user_id):
    token = jwt.encode({"userId": user_id}, SECRET_KEY, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

def test_get_orders_empty():
    mock_orders_table.scan.return_value = {"Items": []}
    
    event = {
        "httpMethod": "GET",
        "headers": get_auth_headers("user123")
    }
    
    res = order_handler.lambda_handler(event, None)
    assert_equal(res["statusCode"], 200)
    body = json.loads(res["body"])
    assert_equal(body["count"], 0)

def test_get_orders_list():
    mock_orders = [
        {
            "orderId": "o1",
            "userId": "user123",
            "productId": "p1",
            "productName": "Wireless Bluetooth Headphones",
            "price": 1600,
            "quantity": 1,
            "totalAmount": 1600,
            "status": "Delivered",
            "createdAt": "2026-05-18T10:00:00"
        }
    ]
    
    mock_orders_table.scan.return_value = {"Items": mock_orders}
    # No reviews found for the order
    mock_reviews_table.scan.return_value = {"Count": 0, "Items": []}
    
    event = {
        "httpMethod": "GET",
        "headers": get_auth_headers("user123")
    }
    
    res = order_handler.lambda_handler(event, None)
    assert_equal(res["statusCode"], 200)
    body = json.loads(res["body"])
    assert_equal(body["count"], 1)
    assert_equal(body["orders"][0]["orderId"], "o1")
    assert_equal(body["orders"][0]["reviewed"], False)

def test_create_order_insufficient_stock():
    mock_product = {
        "productId": "p1",
        "name": "Wireless Bluetooth Headphones",
        "price": 2000,
        "discount": 20,
        "stock": 1  # Only 1 in stock
    }
    
    mock_products_table.get_item.return_value = {"Item": mock_product}
    
    event = {
        "httpMethod": "POST",
        "headers": get_auth_headers("user123"),
        "body": json.dumps({
            "items": [
                {"productId": "p1", "quantity": 2}  # Asking for 2!
            ],
            "address": "123 Main St"
        })
    }
    
    res = order_handler.lambda_handler(event, None)
    assert_equal(res["statusCode"], 400)
    body = json.loads(res["body"])
    assert_equal(body["message"], "Not enough stock for Wireless Bluetooth Headphones")

def test_create_order_success():
    mock_product = {
        "productId": "p1",
        "name": "Wireless Bluetooth Headphones",
        "price": 2000,
        "discount": 20,
        "stock": 5
    }
    
    mock_products_table.get_item.return_value = {"Item": mock_product}
    mock_orders_table.put_item.return_value = {}
    mock_products_table.update_item.return_value = {}
    
    event = {
        "httpMethod": "POST",
        "headers": get_auth_headers("user123"),
        "body": json.dumps({
            "items": [
                {"productId": "p1", "quantity": 1}
            ],
            "address": "123 Main St"
        })
    }
    
    res = order_handler.lambda_handler(event, None)
    assert_equal(res["statusCode"], 201)
    body = json.loads(res["body"])
    assert_equal(body["message"], "Orders placed successfully")
    assert_equal(body["count"], 1)
    assert_equal(body["totalAmount"], 1600) # 2000 - 20% = 1600
