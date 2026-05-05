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

# REVIEWS TABLE
resource "aws_dynamodb_table" "reviews" {
  name         = "${var.project_name}-reviews"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "productId"
  range_key    = "reviewId"

  attribute {
    name = "productId"
    type = "S"
  }

  attribute {
    name = "reviewId"
    type = "S"
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

# Zip the Search Lambda Code
data "archive_file" "search_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/search/search_products.py"
  output_path = "${path.module}/search.zip"
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

# SEARCH LAMBDA
resource "aws_lambda_function" "search" {
  function_name = "${var.project_name}-search"
  runtime       = "python3.12"
  handler       = "search_products.lambda_handler"

  filename         = data.archive_file.search_zip.output_path
  source_code_hash = data.archive_file.search_zip.output_base64sha256

  role = aws_iam_role.lambda_exec.arn
  timeout = 10


  environment {
    variables = {
      PRODUCTS_TABLE = aws_dynamodb_table.products.name
      FRONTEND_URL   = var.frontend_url
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

resource "aws_apigatewayv2_integration" "search" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.search.invoke_arn
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

resource "aws_apigatewayv2_route" "search" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /search"
  target    = "integrations/${aws_apigatewayv2_integration.search.id}"
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

resource "aws_lambda_permission" "search" {
  statement_id  = "AllowAPIGatewayInvokeSearch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.search.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*/search"
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