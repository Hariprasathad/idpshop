import json
from test_helper import assert_equal, mock_products_table, mock_reviews_table
from backend.product import product_handler

def test_get_products_list():
    # Mock products scan response
    mock_products = [
        {
            "productId": "p1",
            "name": "Product 1",
            "category": "Electronics",
            "price": 100,
            "discount": 10,
            "stock": 5,
            "sellerId": "s1",
            "createdAt": "2026-05-18T10:00:00"
        },
        {
            "productId": "p2",
            "name": "Product 2",
            "category": "Home",
            "price": 200,
            "discount": 0,
            "stock": 0,  # Out of stock, should be hidden!
            "sellerId": "s1",
            "createdAt": "2026-05-18T10:00:00"
        }
    ]
    
    mock_products_table.scan.return_value = {"Items": mock_products}
    
    # Mock reviews scan response for rating calculation
    mock_reviews_table.scan.return_value = {"Items": [
        {"rating": 5},
        {"rating": 4}
    ]}
    
    event = {
        "httpMethod": "GET",
        "queryStringParameters": {
            "limit": "10"
        }
    }
    
    res = product_handler.lambda_handler(event, None)
    assert_equal(res["statusCode"], 200)
    body = json.loads(res["body"])
    
    # Only Product 1 should be visible (Product 2 is out of stock)
    assert_equal(body["count"], 1)
    assert_equal(body["products"][0]["productId"], "p1")
    assert_equal(body["products"][0]["category"], "Electronics")
    assert_equal(body["products"][0]["sellingPrice"], 90) # 100 - 10%
    assert_equal(body["products"][0]["rating"], 4.5) # (5+4)/2

def test_search_products():
    mock_products = [
        {
            "productId": "p1",
            "name": "Amazing Wireless Headphones",
            "description": "Premium noise cancelling headphones",
            "price": 2000,
            "discount": 20,
            "stock": 10
        },
        {
            "productId": "p2",
            "name": "Mechanical Keyboard",
            "description": "RGB mechanical keyboard",
            "price": 1000,
            "discount": 0,
            "stock": 5
        }
    ]
    
    mock_products_table.scan.return_value = {"Items": mock_products}
    mock_reviews_table.scan.return_value = {"Items": []} # No reviews
    
    # Test match name
    event = {
        "httpMethod": "GET",
        "queryStringParameters": {
            "q": "headphones"
        }
    }
    
    res = product_handler.lambda_handler(event, None)
    assert_equal(res["statusCode"], 200)
    body = json.loads(res["body"])
    assert_equal(body["count"], 1)
    assert_equal(body["products"][0]["productId"], "p1")
    assert_equal(body["products"][0]["sellingPrice"], 1600) # 2000 - 20%
    
    # Test no match
    event["queryStringParameters"]["q"] = "nonexistent"
    res = product_handler.lambda_handler(event, None)
    body = json.loads(res["body"])
    assert_equal(body["count"], 0)
