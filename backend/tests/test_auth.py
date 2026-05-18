import json
import bcrypt
from test_helper import assert_equal, mock_users_table

def test_login_missing_fields():
    # Import login inside test to ensure mock_boto3 is already active
    import login

    event = {
        "body": json.dumps({
            "email": ""
        })
    }
    
    res = login.lambda_handler(event, None)
    assert_equal(res["statusCode"], 400)
    body = json.loads(res["body"])
    assert_equal(body["message"], "Missing fields")

def test_login_invalid_credentials():
    import login
    
    # Mock table.query to return no users
    mock_users_table.query.return_value = {"Items": []}
    
    event = {
        "body": json.dumps({
            "email": "test@example.com",
            "password": "wrongpassword"
        })
    }
    
    res = login.lambda_handler(event, None)
    assert_equal(res["statusCode"], 401)
    body = json.loads(res["body"])
    assert_equal(body["message"], "Invalid credentials")

def test_login_success():
    import login
    
    # Pre-hash password for mock user
    plain_password = "correctpassword"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')
    
    mock_user = {
        "userId": "12345",
        "email": "test@example.com",
        "password": hashed,
        "name": "Test User",
        "role": "user"
    }
    
    mock_users_table.query.return_value = {"Items": [mock_user]}
    
    event = {
        "body": json.dumps({
            "email": "test@example.com",
            "password": plain_password
        })
    }
    
    res = login.lambda_handler(event, None)
    assert_equal(res["statusCode"], 200)
    body = json.loads(res["body"])
    assert_equal(body["message"], "Login successful")
    assert_equal(body["user"]["email"], "test@example.com")
    assert_equal(body["user"]["name"], "Test User")

def test_register_missing_fields():
    import register
    
    event = {
        "body": json.dumps({
            "email": "test@example.com"
        })
    }
    
    res = register.lambda_handler(event, None)
    assert_equal(res["statusCode"], 400)
    body = json.loads(res["body"])
    assert_equal(body["message"], "Missing required fields")

def test_register_user_exists():
    import register
    
    # Mock check_response to return existing user
    mock_users_table.query.return_value = {"Items": [{"email": "test@example.com"}]}
    
    event = {
        "body": json.dumps({
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        })
    }
    
    res = register.lambda_handler(event, None)
    assert_equal(res["statusCode"], 400)
    body = json.loads(res["body"])
    assert_equal(body["message"], "User already exists")

def test_register_success():
    import register
    
    # Mock check_response to return no users
    mock_users_table.query.return_value = {"Items": []}
    mock_users_table.scan.return_value = {"Items": []}
    
    event = {
        "body": json.dumps({
            "email": "newuser@example.com",
            "password": "password123",
            "name": "New User"
        })
    }
    
    res = register.lambda_handler(event, None)
    assert_equal(res["statusCode"], 201)
    body = json.loads(res["body"])
    assert_equal(body["message"], "User registered successfully")
