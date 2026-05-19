import json
import jwt
from test_helper import assert_equal, mock_cart_table, mock_products_table
from backend.cart import cart_handler

SECRET_KEY = "test_secret_key"

def get_auth_headers(user_id):
    token = jwt.encode({"userId": user_id}, SECRET_KEY, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

def test_get_cart_empty():
    mock_cart_table.scan.return_value = {"Items": []}
    
    event = {
        "httpMethod": "GET",
        "headers": get_auth_headers("user123")
    }
    
    res = cart_handler.lambda_handler(event, None)
    assert_equal(res["statusCode"], 200)
    body = json.loads(res["body"])
    assert_equal(body["count"], 0)

def test_add_to_cart_success():
    mock_product = {
        "productId": "p1",
        "name": "Wireless Bluetooth Headphones",
        "price": 2000,
        "discount": 20,
        "stock": 5
    }
    
    mock_products_table.get_item.return_value = {"Item": mock_product}
    mock_cart_table.scan.return_value = {"Count": 0} # Empty cart
    mock_cart_table.put_item.return_value = {}
    
    event = {
        "httpMethod": "POST",
        "headers": get_auth_headers("user123"),
        "body": json.dumps({
            "productId": "p1",
            "quantity": 1
        })
    }
    
    res = cart_handler.lambda_handler(event, None)
    assert_equal(res["statusCode"], 201)
    body = json.loads(res["body"])
    assert_equal(body["message"], "Added to cart")
    assert_equal(body["cart"]["sellingPrice"], 1600)

def test_add_to_cart_limit_reached():
    mock_product = {
        "productId": "p1",
        "name": "Wireless Bluetooth Headphones",
        "price": 2000,
        "discount": 20,
        "stock": 5
    }
    
    mock_products_table.get_item.return_value = {"Item": mock_product}
    mock_cart_table.scan.return_value = {"Count": 10} # Limit is 10
    
    event = {
        "httpMethod": "POST",
        "headers": get_auth_headers("user123"),
        "body": json.dumps({
            "productId": "p1",
            "quantity": 1
        })
    }
    
    res = cart_handler.lambda_handler(event, None)
    assert_equal(res["statusCode"], 400)
    body = json.loads(res["body"])
    assert_equal(body["message"], "Cart limit reached")

def test_remove_from_cart():
    mock_cart_table.delete_item.return_value = {}
    
    event = {
        "httpMethod": "DELETE",
        "headers": get_auth_headers("user123"),
        "body": json.dumps({
            "productId": "p1"
        })
    }
    
    res = cart_handler.lambda_handler(event, None)
    assert_equal(res["statusCode"], 200)
    body = json.loads(res["body"])
    assert_equal(body["message"], "Removed from cart")
