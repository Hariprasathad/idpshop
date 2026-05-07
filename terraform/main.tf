# IAM ROLE
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

# USERS TABLE
resource "aws_dynamodb_table" "users" {
  name         = "${var.project_name}-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }
}

# PRODUCTS TABLE
resource "aws_dynamodb_table" "products" {
  name         = "${var.project_name}-products"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "productId"

  attribute {
    name = "productId"
    type = "S"
  }
}

# CART TABLE
resource "aws_dynamodb_table" "cart" {
  name         = "${var.project_name}-cart"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"
  range_key    = "productId"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "productId"
    type = "S"
  }
}

# ORDERS TABLE
resource "aws_dynamodb_table" "orders" {
  name         = "${var.project_name}-orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "orderId"

  attribute {
    name = "orderId"
    type = "S"
  }

  attribute {
    name = "userId"
    type = "S"
  }

  global_secondary_index {
    name            = "user-index"
    hash_key        = "userId"
    projection_type = "ALL"
  }
}

# ============================================
# ⭐ Reviews Table
# ============================================
resource "aws_dynamodb_table" "reviews" {
  name         = "${var.project_name}-reviews"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "reviewId"

  # 🔑 Primary Key
  attribute {
    name = "reviewId"
    type = "S"
  }

  # 🏷️ Tags
  tags = {
    Name        = "${var.project_name}-reviews"
    Environment = "dev"
  }
}

# ============================================
# ❤️ Wishlist Table
# ============================================
resource "aws_dynamodb_table" "wishlist" {
  name         = "${var.project_name}-wishlist"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "wishlistId"

  attribute {
    name = "wishlistId"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-wishlist"
    Environment = "dev"
  }
}



# S3 BUCKET
resource "aws_s3_bucket" "product_images" {
  bucket = "${var.project_name}-product-images"
}

# PUBLIC ACCESS BLOCK
resource "aws_s3_bucket_public_access_block" "public_access" {
  bucket = aws_s3_bucket.product_images.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# BUCKET POLICY (Allow Public Read)
resource "aws_s3_bucket_policy" "public_read" {
  bucket = aws_s3_bucket.product_images.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow",
        Principal = "*",
        Action    = "s3:GetObject",
        Resource  = "${aws_s3_bucket.product_images.arn}/*"
      }
    ]
  })
}

# CORS CONFIGURATION
resource "aws_s3_bucket_cors_configuration" "cors" {
  bucket = aws_s3_bucket.product_images.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# --- LAMBDA PACKAGING ---

# Zip the Register Lambda Code
data "archive_file" "register_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/auth/register-package"
  output_path = "${path.module}/register.zip"
}

# Zip the Login Lambda Code
data "archive_file" "login_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/auth/login-package"
  output_path = "${path.module}/login.zip"
}

# Zip the Auth Layer (bcrypt, jwt)
data "archive_file" "auth_layer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/layers/auth_layer"
  output_path = "${path.module}/auth_layer.zip"
}

# ============================================
# 🔍 SEARCH PRODUCTS ZIP
# ============================================
data "archive_file" "search_products_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/product/search_products.py"
  output_path = "${path.module}/search-products.zip"
}


# --- LAMBDA LAYER ---

resource "aws_lambda_layer_version" "auth_layer" {
  filename            = data.archive_file.auth_layer_zip.output_path
  layer_name          = "${var.project_name}-auth-layer"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = data.archive_file.auth_layer_zip.output_base64sha256
}

# --- LAMBDA FUNCTIONS ---

# REGISTER LAMBDA
resource "aws_lambda_function" "auth_register" {
  function_name = "${var.project_name}-auth-register"
  runtime       = "python3.12"
  handler       = "register.lambda_handler"
  timeout       = 10


  filename         = data.archive_file.register_zip.output_path
  source_code_hash = data.archive_file.register_zip.output_base64sha256

  role = aws_iam_role.lambda_exec.arn

  layers = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      USERS_TABLE  = aws_dynamodb_table.users.name
      FRONTEND_URL = var.frontend_url
    }
  }
}

# LOGIN LAMBDA
resource "aws_lambda_function" "auth_login" {
  function_name = "${var.project_name}-auth-login"
  runtime       = "python3.12"
  handler       = "login.lambda_handler"
  timeout       = 10


  filename         = data.archive_file.login_zip.output_path
  source_code_hash = data.archive_file.login_zip.output_base64sha256

  role = aws_iam_role.lambda_exec.arn

  layers = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      USERS_TABLE  = aws_dynamodb_table.users.name
      FRONTEND_URL = var.frontend_url
      SECRET_KEY   = var.jwt_secret
    }
  }
}

# ============================================
# 🔍 SEARCH PRODUCTS LAMBDA
# ============================================
resource "aws_lambda_function" "search_products" {
  function_name = "${var.project_name}-product-search"
  runtime       = "python3.12"
  handler       = "search_products.lambda_handler"
  filename      = data.archive_file.search_products_zip.output_path
  source_code_hash = data.archive_file.search_products_zip.output_base64sha256
  role          = aws_iam_role.lambda_exec.arn

  environment {
    variables = {
      PRODUCTS_TABLE = aws_dynamodb_table.products.name
      REVIEWS_TABLE  = aws_dynamodb_table.reviews.name
    }
  }
}


# --- API GATEWAY ---

resource "aws_apigatewayv2_api" "api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    allow_headers = ["*"]
  }
}

# --- INTEGRATIONS ---

resource "aws_apigatewayv2_integration" "login" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.auth_login.invoke_arn
}

resource "aws_apigatewayv2_integration" "register" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.auth_register.invoke_arn
}

# ============================================
# 🌐 SEARCH PRODUCTS API INTEGRATION
# ============================================
resource "aws_apigatewayv2_integration" "search_products" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.search_products.invoke_arn
}


# --- ROUTES ---

resource "aws_apigatewayv2_route" "login" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "POST /login"
  target    = "integrations/${aws_apigatewayv2_integration.login.id}"
}

resource "aws_apigatewayv2_route" "register" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "POST /register"
  target    = "integrations/${aws_apigatewayv2_integration.register.id}"
}

# ============================================
# 🌐 SEARCH PRODUCTS ROUTE
# ============================================
resource "aws_apigatewayv2_route" "search_products" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /search-products"
  target    = "integrations/${aws_apigatewayv2_integration.search_products.id}"
}


# --- STAGE ---

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true
}

# --- PERMISSIONS ---

resource "aws_lambda_permission" "login" {
  statement_id  = "AllowAPIGatewayInvokeLogin"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth_login.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/login"
}

resource "aws_lambda_permission" "register" {
  statement_id  = "AllowAPIGatewayInvokeRegister"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth_register.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/register"
}

# ============================================
# 🔐 SEARCH PRODUCTS PERMISSION
# ============================================
resource "aws_lambda_permission" "search_products" {
  statement_id  = "AllowAPIGatewayInvokeSearchProducts"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.search_products.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/search-products"
}

# ============================================
# 📦 GET PRODUCTS ZIP
# ============================================
data "archive_file" "get_products_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/product/get_products.py"
  output_path = "${path.module}/get-products.zip"
}

# ============================================
# 📦 GET PRODUCTS LAMBDA
# ============================================
resource "aws_lambda_function" "get_products" {
  function_name = "${var.project_name}-product-get"
  runtime       = "python3.12"
  handler       = "get_products.lambda_handler"
  filename      = data.archive_file.get_products_zip.output_path
  source_code_hash = data.archive_file.get_products_zip.output_base64sha256
  role          = aws_iam_role.lambda_exec.arn

  environment {
    variables = {
      PRODUCTS_TABLE = aws_dynamodb_table.products.name
      REVIEWS_TABLE  = aws_dynamodb_table.reviews.name
    }
  }
}

# ============================================
# 🌐 API INTEGRATION
# ============================================
resource "aws_apigatewayv2_integration" "get_products" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_products.invoke_arn
}

# ============================================
# 🌐 API ROUTE
# ============================================
resource "aws_apigatewayv2_route" "get_products" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /products"
  target    = "integrations/${aws_apigatewayv2_integration.get_products.id}"
}

# ============================================
# 🔐 LAMBDA PERMISSION
# ============================================
resource "aws_lambda_permission" "get_products" {
  statement_id  = "AllowAPIGatewayInvokeGetProducts"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_products.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/products"
}

# --- ADD PRODUCT LAMBDA ---

data "archive_file" "add_product_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/seller/products/add-product.py"
  output_path = "${path.module}/add-product.zip"
}

resource "aws_lambda_function" "add_product" {
  function_name = "${var.project_name}-add-product"
  runtime       = "python3.12"
  handler       = "add-product.lambda_handler"

  filename         = data.archive_file.add_product_zip.output_path
  source_code_hash = data.archive_file.add_product_zip.output_base64sha256

  role    = aws_iam_role.lambda_exec.arn
  timeout = 10
  layers  = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      PRODUCTS_TABLE = aws_dynamodb_table.products.name
      SECRET_KEY     = var.jwt_secret
    }
  }
}

resource "aws_apigatewayv2_integration" "add_product" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.add_product.invoke_arn
}

resource "aws_apigatewayv2_route" "add_product" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "POST /add-product"
  target    = "integrations/${aws_apigatewayv2_integration.add_product.id}"
}

resource "aws_lambda_permission" "add_product" {
  statement_id  = "AllowAPIGatewayInvokeAddProduct"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.add_product.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/add-product"
}

# --- S3 UPLOAD LAMBDA ---

data "archive_file" "upload_url_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/s3/get-upload-url.py"
  output_path = "${path.module}/upload-url.zip"
}

resource "aws_lambda_function" "get_upload_url" {
  function_name = "${var.project_name}-get-upload-url"
  runtime       = "python3.12"
  handler       = "get-upload-url.lambda_handler"

  filename         = data.archive_file.upload_url_zip.output_path
  source_code_hash = data.archive_file.upload_url_zip.output_base64sha256

  role    = aws_iam_role.lambda_exec.arn
  timeout = 10

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.product_images.bucket
    }
  }
}

resource "aws_iam_role_policy" "lambda_s3" {
  name = "lambda-s3-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject"
        ],
        Resource = "${aws_s3_bucket.product_images.arn}/*"
      }
    ]
  })
}

resource "aws_apigatewayv2_integration" "upload_url" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_upload_url.invoke_arn
}

resource "aws_apigatewayv2_route" "upload_url" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /get-upload-url"
  target    = "integrations/${aws_apigatewayv2_integration.upload_url.id}"
}

resource "aws_lambda_permission" "upload_url" {
  statement_id  = "AllowAPIGatewayInvokeUploadUrl"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_upload_url.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/get-upload-url"
}

# --- SELLER PRODUCTS LAMBDA ---

data "archive_file" "seller_products_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/seller/products/seller-products.py"
  output_path = "${path.module}/seller-products.zip"
}

resource "aws_lambda_function" "seller_products" {
  function_name = "${var.project_name}-seller-products"
  runtime       = "python3.12"
  handler       = "seller-products.lambda_handler"

  filename         = data.archive_file.seller_products_zip.output_path
  source_code_hash = data.archive_file.seller_products_zip.output_base64sha256

  role    = aws_iam_role.lambda_exec.arn
  timeout = 10

  layers = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      PRODUCTS_TABLE = aws_dynamodb_table.products.name
      SECRET_KEY     = var.jwt_secret
    }
  }
}

resource "aws_apigatewayv2_integration" "seller_products" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.seller_products.invoke_arn
}

resource "aws_apigatewayv2_route" "seller_products" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /seller-products"
  target    = "integrations/${aws_apigatewayv2_integration.seller_products.id}"
}

resource "aws_lambda_permission" "seller_products" {
  statement_id  = "AllowAPIGatewayInvokeSellerProducts"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.seller_products.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/seller-products"
}

# --- UPDATE PRODUCT LAMBDA ---

data "archive_file" "update_product_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/seller/products/update-product.py"
  output_path = "${path.module}/update-product.zip"
}

resource "aws_lambda_function" "update_product" {
  function_name = "${var.project_name}-update-product"
  runtime       = "python3.12"
  handler       = "update-product.lambda_handler"

  filename         = data.archive_file.update_product_zip.output_path
  source_code_hash = data.archive_file.update_product_zip.output_base64sha256

  role    = aws_iam_role.lambda_exec.arn
  timeout = 10

  layers = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      PRODUCTS_TABLE = aws_dynamodb_table.products.name
      SECRET_KEY     = var.jwt_secret
    }
  }
}

resource "aws_apigatewayv2_integration" "update_product" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.update_product.invoke_arn
}

resource "aws_apigatewayv2_route" "update_product" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "PUT /update-product"
  target    = "integrations/${aws_apigatewayv2_integration.update_product.id}"
}

resource "aws_lambda_permission" "update_product" {
  statement_id  = "AllowAPIGatewayInvokeUpdateProduct"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.update_product.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/update-product"
}

# --- DELETE PRODUCT LAMBDA ---

data "archive_file" "delete_product_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/seller/products/delete-product.py"
  output_path = "${path.module}/delete-product.zip"
}

resource "aws_lambda_function" "delete_product" {
  function_name = "${var.project_name}-delete-product"
  runtime       = "python3.12"
  handler       = "delete-product.lambda_handler"

  filename         = data.archive_file.delete_product_zip.output_path
  source_code_hash = data.archive_file.delete_product_zip.output_base64sha256

  role    = aws_iam_role.lambda_exec.arn
  timeout = 10

  layers = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      PRODUCTS_TABLE = aws_dynamodb_table.products.name
      SECRET_KEY     = var.jwt_secret
    }
  }
}

resource "aws_apigatewayv2_integration" "delete_product" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.delete_product.invoke_arn
}

resource "aws_apigatewayv2_route" "delete_product" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "DELETE /delete-product"
  target    = "integrations/${aws_apigatewayv2_integration.delete_product.id}"
}

resource "aws_lambda_permission" "delete_product" {
  statement_id  = "AllowAPIGatewayInvokeDeleteProduct"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.delete_product.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/delete-product"
}

# --- SELLER STATS LAMBDA ---

data "archive_file" "seller_stats_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/seller/stats/seller-stats.py"
  output_path = "${path.module}/seller-stats.zip"
}

resource "aws_lambda_function" "seller_stats" {
  function_name = "${var.project_name}-seller-stats"
  runtime       = "python3.12"
  handler       = "seller-stats.lambda_handler"

  filename         = data.archive_file.seller_stats_zip.output_path
  source_code_hash = data.archive_file.seller_stats_zip.output_base64sha256

  role    = aws_iam_role.lambda_exec.arn
  timeout = 10

  layers = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      PRODUCTS_TABLE = aws_dynamodb_table.products.name
      ORDERS_TABLE   = aws_dynamodb_table.orders.name
      SECRET_KEY     = var.jwt_secret
    }
  }
}

resource "aws_apigatewayv2_integration" "seller_stats" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.seller_stats.invoke_arn
}

resource "aws_apigatewayv2_route" "seller_stats" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /seller-stats"
  target    = "integrations/${aws_apigatewayv2_integration.seller_stats.id}"
}

resource "aws_lambda_permission" "seller_stats" {
  statement_id  = "AllowAPIGatewayInvokeSellerStats"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.seller_stats.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/seller-stats"
}

# --- SELLER ORDERS LAMBDA ---

data "archive_file" "seller_orders_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/seller/orders/seller-orders.py"
  output_path = "${path.module}/seller-orders.zip"
}

resource "aws_lambda_function" "seller_orders" {
  function_name = "${var.project_name}-seller-orders"
  runtime       = "python3.12"
  handler       = "seller-orders.lambda_handler"

  filename         = data.archive_file.seller_orders_zip.output_path
  source_code_hash = data.archive_file.seller_orders_zip.output_base64sha256

  role    = aws_iam_role.lambda_exec.arn
  timeout = 10

  layers = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      ORDERS_TABLE = aws_dynamodb_table.orders.name
      SECRET_KEY   = var.jwt_secret
    }
  }
}

resource "aws_apigatewayv2_integration" "seller_orders" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.seller_orders.invoke_arn
}

resource "aws_apigatewayv2_route" "seller_orders" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /seller-orders"
  target    = "integrations/${aws_apigatewayv2_integration.seller_orders.id}"
}

resource "aws_lambda_permission" "seller_orders" {
  statement_id  = "AllowAPIGatewayInvokeSellerOrders"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.seller_orders.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/seller-orders"
}

# --- UPDATE ORDER STATUS LAMBDA ---

data "archive_file" "update_order_status_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/seller/orders/update-order-status.py"
  output_path = "${path.module}/update-order-status.zip"
}

resource "aws_lambda_function" "update_order_status" {
  function_name = "${var.project_name}-update-order-status"
  runtime       = "python3.12"
  handler       = "update-order-status.lambda_handler"

  filename         = data.archive_file.update_order_status_zip.output_path
  source_code_hash = data.archive_file.update_order_status_zip.output_base64sha256

  role    = aws_iam_role.lambda_exec.arn
  timeout = 10

  layers = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      ORDERS_TABLE = aws_dynamodb_table.orders.name
      SECRET_KEY   = var.jwt_secret
    }
  }
}

resource "aws_apigatewayv2_integration" "update_order_status" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.update_order_status.invoke_arn
}

resource "aws_apigatewayv2_route" "update_order_status" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "PUT /update-order-status"
  target    = "integrations/${aws_apigatewayv2_integration.update_order_status.id}"
}

resource "aws_lambda_permission" "update_order_status" {
  statement_id  = "AllowAPIGatewayInvokeUpdateOrderStatus"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.update_order_status.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/update-order-status"
}

# ============================================
# 🛒 ADD CART ZIP
# ============================================
data "archive_file" "add_to_cart_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/cart/add_to_cart.py"
  output_path = "${path.module}/add-to-cart.zip"
}

# ============================================
# 🛒 ADD CART LAMBDA
# ============================================
resource "aws_lambda_function" "add_to_cart" {
  function_name = "${var.project_name}-cart-add"
  runtime       = "python3.12"
  handler       = "add_to_cart.lambda_handler"
  filename      = data.archive_file.add_to_cart_zip.output_path
  source_code_hash = data.archive_file.add_to_cart_zip.output_base64sha256
  role          = aws_iam_role.lambda_exec.arn
  layers        = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      CART_TABLE     = aws_dynamodb_table.cart.name
      PRODUCTS_TABLE = aws_dynamodb_table.products.name
      SECRET_KEY     = var.jwt_secret
    }
  }
}

# ============================================
# 🛒 ADD CART API
# ============================================
resource "aws_apigatewayv2_integration" "add_to_cart" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.add_to_cart.invoke_arn
}

resource "aws_apigatewayv2_route" "add_to_cart" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "POST /add-to-cart"
  target    = "integrations/${aws_apigatewayv2_integration.add_to_cart.id}"
}

resource "aws_lambda_permission" "add_to_cart" {
  statement_id  = "AllowAPIGatewayInvokeAddCart"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.add_to_cart.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/add-to-cart"
}

# ============================================
# 🛒 GET CART ZIP
# ============================================
data "archive_file" "get_cart_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/cart/get_cart.py"
  output_path = "${path.module}/get-cart.zip"
}

# ============================================
# 🛒 GET CART LAMBDA
# ============================================
resource "aws_lambda_function" "get_cart" {
  function_name = "${var.project_name}-cart-get"
  runtime       = "python3.12"
  handler       = "get_cart.lambda_handler"
  filename      = data.archive_file.get_cart_zip.output_path
  source_code_hash = data.archive_file.get_cart_zip.output_base64sha256
  role          = aws_iam_role.lambda_exec.arn
  layers        = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      CART_TABLE = aws_dynamodb_table.cart.name
      SECRET_KEY = var.jwt_secret
    }
  }
}

# ============================================
# 🛒 GET CART API
# ============================================
resource "aws_apigatewayv2_integration" "get_cart" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_cart.invoke_arn
}

resource "aws_apigatewayv2_route" "get_cart" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /cart"
  target    = "integrations/${aws_apigatewayv2_integration.get_cart.id}"
}

resource "aws_lambda_permission" "get_cart" {
  statement_id  = "AllowAPIGatewayInvokeGetCart"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_cart.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/cart"
}

# ============================================
# ❤️ ADD WISHLIST ZIP
# ============================================
data "archive_file" "add_wishlist_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/wishlist/add_to_wishlist.py"
  output_path = "${path.module}/add-wishlist.zip"
}

# ============================================
# ❤️ ADD WISHLIST LAMBDA
# ============================================
resource "aws_lambda_function" "add_wishlist" {
  function_name = "${var.project_name}-wishlist-add"
  runtime       = "python3.12"
  handler       = "add_to_wishlist.lambda_handler"
  filename      = data.archive_file.add_wishlist_zip.output_path
  source_code_hash = data.archive_file.add_wishlist_zip.output_base64sha256
  role          = aws_iam_role.lambda_exec.arn
  layers        = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      WISHLIST_TABLE = aws_dynamodb_table.wishlist.name
      PRODUCTS_TABLE = aws_dynamodb_table.products.name
      SECRET_KEY     = var.jwt_secret
    }
  }
}

resource "aws_apigatewayv2_integration" "add_wishlist" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.add_wishlist.invoke_arn
}

resource "aws_apigatewayv2_route" "add_wishlist" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "POST /add-to-wishlist"
  target    = "integrations/${aws_apigatewayv2_integration.add_wishlist.id}"
}

resource "aws_lambda_permission" "add_wishlist" {
  statement_id  = "AllowAPIGatewayInvokeAddWishlist"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.add_wishlist.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/add-to-wishlist"
}

# ============================================
# ❤️ GET WISHLIST ZIP
# ============================================
data "archive_file" "get_wishlist_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/wishlist/get_wishlist.py"
  output_path = "${path.module}/get-wishlist.zip"
}

# ============================================
# ❤️ GET WISHLIST LAMBDA
# ============================================
resource "aws_lambda_function" "get_wishlist" {
  function_name = "${var.project_name}-wishlist-get"
  runtime       = "python3.12"
  handler       = "get_wishlist.lambda_handler"
  filename      = data.archive_file.get_wishlist_zip.output_path
  source_code_hash = data.archive_file.get_wishlist_zip.output_base64sha256
  role          = aws_iam_role.lambda_exec.arn
  layers        = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      WISHLIST_TABLE = aws_dynamodb_table.wishlist.name
      SECRET_KEY     = var.jwt_secret
    }
  }
}

resource "aws_apigatewayv2_integration" "get_wishlist" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_wishlist.invoke_arn
}

resource "aws_apigatewayv2_route" "get_wishlist" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /wishlist"
  target    = "integrations/${aws_apigatewayv2_integration.get_wishlist.id}"
}

resource "aws_lambda_permission" "get_wishlist" {
  statement_id  = "AllowAPIGatewayInvokeGetWishlist"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_wishlist.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/wishlist"
}

# ============================================
# 📦 PLACE ORDER ZIP
# ============================================
data "archive_file" "place_order_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/orders/place_order.py"
  output_path = "${path.module}/place-order.zip"
}

# ============================================
# 🗑️ REMOVE CART ZIP
# ============================================
data "archive_file" "remove_cart_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/cart/remove_from_cart.py"
  output_path = "${path.module}/remove-cart.zip"
}

# ============================================
# 🗑️ REMOVE CART LAMBDA
# ============================================
resource "aws_lambda_function" "remove_cart" {
  function_name    = "${var.project_name}-cart-remove"
  runtime          = "python3.12"
  handler          = "remove_from_cart.lambda_handler"
  filename         = data.archive_file.remove_cart_zip.output_path
  source_code_hash = data.archive_file.remove_cart_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  layers           = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      CART_TABLE = aws_dynamodb_table.cart.name
      SECRET_KEY = var.jwt_secret
    }
  }
}

# ============================================
# 🗑️ REMOVE CART API
# ============================================
resource "aws_apigatewayv2_integration" "remove_cart" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.remove_cart.invoke_arn
}

resource "aws_apigatewayv2_route" "remove_cart" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "DELETE /remove-from-cart"
  target    = "integrations/${aws_apigatewayv2_integration.remove_cart.id}"
}

resource "aws_lambda_permission" "remove_cart" {
  statement_id  = "AllowAPIGatewayInvokeRemoveCart"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.remove_cart.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/remove-from-cart"
}

# ============================================
# 📦 PLACE ORDER LAMBDA
# ============================================
resource "aws_lambda_function" "place_order" {
  function_name = "${var.project_name}-order-create"
  runtime       = "python3.12"
  handler       = "place_order.lambda_handler"
  filename      = data.archive_file.place_order_zip.output_path
  source_code_hash = data.archive_file.place_order_zip.output_base64sha256
  role          = aws_iam_role.lambda_exec.arn
  layers        = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      ORDERS_TABLE   = aws_dynamodb_table.orders.name
      PRODUCTS_TABLE = aws_dynamodb_table.products.name
      SECRET_KEY     = var.jwt_secret
    }
  }
}

resource "aws_apigatewayv2_integration" "place_order" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.place_order.invoke_arn
}

resource "aws_apigatewayv2_route" "place_order" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "POST /place-order"
  target    = "integrations/${aws_apigatewayv2_integration.place_order.id}"
}

resource "aws_lambda_permission" "place_order" {
  statement_id  = "AllowAPIGatewayInvokePlaceOrder"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.place_order.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/place-order"
}

# ============================================
# 📦 GET MY ORDERS ZIP
# ============================================
data "archive_file" "get_my_orders_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/orders/get_my_orders.py"
  output_path = "${path.module}/get-my-orders.zip"
}

# ============================================
# 📦 GET MY ORDERS LAMBDA
# ============================================
resource "aws_lambda_function" "get_my_orders" {
  function_name = "${var.project_name}-orders-get"
  runtime       = "python3.12"
  handler       = "get_my_orders.lambda_handler"
  filename      = data.archive_file.get_my_orders_zip.output_path
  source_code_hash = data.archive_file.get_my_orders_zip.output_base64sha256
  role          = aws_iam_role.lambda_exec.arn
  layers        = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      ORDERS_TABLE  = aws_dynamodb_table.orders.name
      REVIEWS_TABLE = aws_dynamodb_table.reviews.name
      SECRET_KEY    = var.jwt_secret
    }
  }
}

# ============================================
# 📦 GET MY ORDERS API
# ============================================
resource "aws_apigatewayv2_integration" "get_my_orders" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_my_orders.invoke_arn
}

resource "aws_apigatewayv2_route" "get_my_orders" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /my-orders"
  target    = "integrations/${aws_apigatewayv2_integration.get_my_orders.id}"
}

resource "aws_lambda_permission" "get_my_orders" {
  statement_id  = "AllowAPIGatewayInvokeGetMyOrders"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_my_orders.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/my-orders"
}

# ============================================
# 👤 GET PROFILE ZIP
# ============================================
data "archive_file" "get_profile_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/profile/get_profile.py"
  output_path = "${path.module}/get-profile.zip"
}

# ============================================
# 👤 GET PROFILE LAMBDA
# ============================================
resource "aws_lambda_function" "get_profile" {
  function_name = "${var.project_name}-profile-get"
  runtime       = "python3.12"
  handler       = "get_profile.lambda_handler"
  filename      = data.archive_file.get_profile_zip.output_path
  source_code_hash = data.archive_file.get_profile_zip.output_base64sha256
  role          = aws_iam_role.lambda_exec.arn
  layers        = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      USERS_TABLE = aws_dynamodb_table.users.name
      SECRET_KEY  = var.jwt_secret
    }
  }
}

# ============================================
# 👤 GET PROFILE API
# ============================================
resource "aws_apigatewayv2_integration" "get_profile" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_profile.invoke_arn
}

resource "aws_apigatewayv2_route" "get_profile" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /profile"
  target    = "integrations/${aws_apigatewayv2_integration.get_profile.id}"
}

resource "aws_lambda_permission" "get_profile" {
  statement_id  = "AllowAPIGatewayInvokeGetProfile"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_profile.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/profile"
}

# ============================================
# 👤 UPDATE PROFILE ZIP
# ============================================
data "archive_file" "update_profile_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/profile/update_profile.py"
  output_path = "${path.module}/update-profile.zip"
}

# ============================================
# 👤 UPDATE PROFILE LAMBDA
# ============================================
resource "aws_lambda_function" "update_profile" {
  function_name = "${var.project_name}-profile-update"
  runtime       = "python3.12"
  handler       = "update_profile.lambda_handler"
  filename      = data.archive_file.update_profile_zip.output_path
  source_code_hash = data.archive_file.update_profile_zip.output_base64sha256
  role          = aws_iam_role.lambda_exec.arn
  layers        = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      USERS_TABLE = aws_dynamodb_table.users.name
      SECRET_KEY  = var.jwt_secret
    }
  }
}

# ============================================
# 👤 UPDATE PROFILE API
# ============================================
resource "aws_apigatewayv2_integration" "update_profile" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.update_profile.invoke_arn
}

resource "aws_apigatewayv2_route" "update_profile" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "PUT /profile"
  target    = "integrations/${aws_apigatewayv2_integration.update_profile.id}"
}

resource "aws_lambda_permission" "update_profile" {
  statement_id  = "AllowAPIGatewayInvokeUpdateProfile"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.update_profile.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/profile"
}

# ============================================
# ⭐ ADD REVIEW ZIP
# ============================================
data "archive_file" "add_review_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/review/add_review.py"
  output_path = "${path.module}/add-review.zip"
}

# ============================================
# ⭐ ADD REVIEW LAMBDA
# ============================================
resource "aws_lambda_function" "add_review" {
  function_name = "${var.project_name}-review-add"
  runtime       = "python3.12"
  handler       = "add_review.lambda_handler"
  filename      = data.archive_file.add_review_zip.output_path
  source_code_hash = data.archive_file.add_review_zip.output_base64sha256
  role          = aws_iam_role.lambda_exec.arn
  layers        = [aws_lambda_layer_version.auth_layer.arn]

  environment {
    variables = {
      REVIEWS_TABLE  = aws_dynamodb_table.reviews.name
      PRODUCTS_TABLE = aws_dynamodb_table.products.name
      SECRET_KEY     = var.jwt_secret
    }
  }
}

# ============================================
# ⭐ ADD REVIEW API INTEGRATION
# ============================================
resource "aws_apigatewayv2_integration" "add_review" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.add_review.invoke_arn
}

# ============================================
# ⭐ ADD REVIEW ROUTE
# ============================================
resource "aws_apigatewayv2_route" "add_review" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "POST /add-review"
  target    = "integrations/${aws_apigatewayv2_integration.add_review.id}"
}

# ============================================
# ⭐ ADD REVIEW PERMISSION
# ============================================
resource "aws_lambda_permission" "add_review" {
  statement_id  = "AllowAPIGatewayInvokeAddReview"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.add_review.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/add-review"
}

# ============================================
# ⭐ GET REVIEWS ZIP
# ============================================
data "archive_file" "get_reviews_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/review/get_reviews.py"
  output_path = "${path.module}/get-reviews.zip"
}

# ============================================
# ⭐ GET REVIEWS LAMBDA
# ============================================
resource "aws_lambda_function" "get_reviews" {
  function_name = "${var.project_name}-review-get"
  runtime       = "python3.12"
  handler       = "get_reviews.lambda_handler"
  filename      = data.archive_file.get_reviews_zip.output_path
  source_code_hash = data.archive_file.get_reviews_zip.output_base64sha256
  role          = aws_iam_role.lambda_exec.arn

  environment {
    variables = {
      REVIEWS_TABLE = aws_dynamodb_table.reviews.name
    }
  }
}

# ============================================
# ⭐ GET REVIEWS API INTEGRATION
# ============================================
resource "aws_apigatewayv2_integration" "get_reviews" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_reviews.invoke_arn
}

# ============================================
# ⭐ GET REVIEWS ROUTE
# ============================================
resource "aws_apigatewayv2_route" "get_reviews" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /reviews"
  target    = "integrations/${aws_apigatewayv2_integration.get_reviews.id}"
}

# ============================================
# ⭐ GET REVIEWS PERMISSION
# ============================================
resource "aws_lambda_permission" "get_reviews" {
  statement_id  = "AllowAPIGatewayInvokeGetReviews"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_reviews.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/reviews"
}

# --- FRONTEND S3 BUCKET ---

resource "aws_s3_bucket" "frontend" {
  bucket = "${var.project_name}-frontend"
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "login.html"
  }

  error_document {
    key = "pages/auth/login.html"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend_public_access" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend_policy" {
  bucket = aws_s3_bucket.frontend.id
  depends_on = [aws_s3_bucket_public_access_block.frontend_public_access]
  policy = jsonencode({

    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })
}

# --- UPLOAD FRONTEND FILES ---

resource "aws_s3_object" "frontend_files" {
  for_each = {
    for file in fileset("${path.module}/../frontend", "**/*") :
    file => file if !endswith(file, "/")
  }


  bucket = aws_s3_bucket.frontend.id
  key    = each.value
  source = "${path.module}/../frontend/${each.value}"
  etag   = filemd5("${path.module}/../frontend/${each.value}")
  
  content_type = lookup({
    "html" = "text/html",
    "css"  = "text/css",
    "js"   = "application/javascript",
    "png"  = "image/png",
    "jpg"  = "image/jpeg",
    "jpeg" = "image/jpeg",
    "svg"  = "image/svg+xml",
    "ico"  = "image/x-icon"
  }, split(".", each.value)[length(split(".", each.value)) - 1], "application/octet-stream")
}