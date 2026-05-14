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
  hash_key     = "reviewId"

  attribute {
    name = "reviewId"
    type = "S"
  }
}

# WISHLIST TABLE
resource "aws_dynamodb_table" "wishlist" {
  name         = "${var.project_name}-wishlist"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "wishlistId"

  attribute {
    name = "wishlistId"
    type = "S"
  }
}

# S3 BUCKET (IMAGES)
resource "aws_s3_bucket" "product_images" {
  bucket = "${var.project_name}-product-images"
}

resource "aws_s3_bucket_public_access_block" "public_access" {
  bucket                  = aws_s3_bucket.product_images.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}



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

# --- LAMBDA LAYERS ---

data "archive_file" "auth_layer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/layers/auth_layer"
  output_path = "${path.module}/auth_layer.zip"
}

resource "aws_lambda_layer_version" "auth_layer" {
  filename            = data.archive_file.auth_layer_zip.output_path
  layer_name          = "${var.project_name}-auth-layer"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = data.archive_file.auth_layer_zip.output_base64sha256
}

# --- LAMBDA PACKAGING (MERGED HANDLERS) ---

data "archive_file" "register_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/auth/register-package"
  output_path = "${path.module}/register.zip"
}

data "archive_file" "login_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/auth/login-package"
  output_path = "${path.module}/login.zip"
}

data "archive_file" "product_handler_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/product/product_handler.py"
  output_path = "${path.module}/product_handler.zip"
}

data "archive_file" "cart_handler_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/cart/cart_handler.py"
  output_path = "${path.module}/cart_handler.zip"
}

data "archive_file" "order_handler_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/orders/order_handler.py"
  output_path = "${path.module}/order_handler.zip"
}

data "archive_file" "profile_handler_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/profile/profile_handler.py"
  output_path = "${path.module}/profile_handler.zip"
}

data "archive_file" "review_handler_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/review/review_handler.py"
  output_path = "${path.module}/review_handler.zip"
}

data "archive_file" "wishlist_handler_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/wishlist/wishlist_handler.py"
  output_path = "${path.module}/wishlist_handler.zip"
}

data "archive_file" "seller_product_handler_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/seller/products/product_handler.py"
  output_path = "${path.module}/seller_product_handler.zip"
}

data "archive_file" "seller_order_handler_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/seller/orders/order_handler.py"
  output_path = "${path.module}/seller_order_handler.zip"
}

data "archive_file" "seller_stats_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/seller/stats/seller-stats.py"
  output_path = "${path.module}/seller-stats.zip"
}

data "archive_file" "upload_url_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/s3/get-upload-url.py"
  output_path = "${path.module}/upload-url.zip"
}

# --- LAMBDA FUNCTIONS ---

resource "aws_lambda_function" "auth_register" {
  function_name    = "${var.project_name}-auth-register"
  runtime          = "python3.12"
  handler          = "register.lambda_handler"
  filename         = data.archive_file.register_zip.output_path
  source_code_hash = data.archive_file.register_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  layers           = [aws_lambda_layer_version.auth_layer.arn]
  environment { variables = { USERS_TABLE = aws_dynamodb_table.users.name, FRONTEND_URL = var.frontend_url } }
  timeout          = 30
  memory_size      = 256
}

resource "aws_lambda_function" "auth_login" {
  function_name    = "${var.project_name}-auth-login"
  runtime          = "python3.12"
  handler          = "login.lambda_handler"
  filename         = data.archive_file.login_zip.output_path
  source_code_hash = data.archive_file.login_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  layers           = [aws_lambda_layer_version.auth_layer.arn]
  environment { variables = { USERS_TABLE = aws_dynamodb_table.users.name, SECRET_KEY = var.jwt_secret, FRONTEND_URL = var.frontend_url } }
  timeout          = 30
  memory_size      = 256
}

resource "aws_lambda_function" "product_handler" {
  function_name    = "${var.project_name}-product-handler"
  runtime          = "python3.12"
  handler          = "product_handler.lambda_handler"
  filename         = data.archive_file.product_handler_zip.output_path
  source_code_hash = data.archive_file.product_handler_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  environment { variables = { PRODUCTS_TABLE = aws_dynamodb_table.products.name, REVIEWS_TABLE = aws_dynamodb_table.reviews.name } }
  timeout          = 30
  memory_size      = 256
}

resource "aws_lambda_function" "cart_handler" {
  function_name    = "${var.project_name}-cart-handler"
  runtime          = "python3.12"
  handler          = "cart_handler.lambda_handler"
  filename         = data.archive_file.cart_handler_zip.output_path
  source_code_hash = data.archive_file.cart_handler_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  layers           = [aws_lambda_layer_version.auth_layer.arn]
  environment { variables = { CART_TABLE = aws_dynamodb_table.cart.name, PRODUCTS_TABLE = aws_dynamodb_table.products.name, SECRET_KEY = var.jwt_secret } }
  timeout          = 30
  memory_size      = 256
}

resource "aws_lambda_function" "order_handler" {
  function_name    = "${var.project_name}-order-handler"
  runtime          = "python3.12"
  handler          = "order_handler.lambda_handler"
  filename         = data.archive_file.order_handler_zip.output_path
  source_code_hash = data.archive_file.order_handler_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  layers           = [aws_lambda_layer_version.auth_layer.arn]
  environment { variables = { ORDERS_TABLE = aws_dynamodb_table.orders.name, PRODUCTS_TABLE = aws_dynamodb_table.products.name, REVIEWS_TABLE = aws_dynamodb_table.reviews.name, SECRET_KEY = var.jwt_secret } }
}

resource "aws_lambda_function" "profile_handler" {
  function_name    = "${var.project_name}-profile-handler"
  runtime          = "python3.12"
  handler          = "profile_handler.lambda_handler"
  filename         = data.archive_file.profile_handler_zip.output_path
  source_code_hash = data.archive_file.profile_handler_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  layers           = [aws_lambda_layer_version.auth_layer.arn]
  environment { variables = { USERS_TABLE = aws_dynamodb_table.users.name, SECRET_KEY = var.jwt_secret } }
  timeout          = 30
  memory_size      = 256
}

resource "aws_lambda_function" "review_handler" {
  function_name    = "${var.project_name}-review-handler"
  runtime          = "python3.12"
  handler          = "review_handler.lambda_handler"
  filename         = data.archive_file.review_handler_zip.output_path
  source_code_hash = data.archive_file.review_handler_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  layers           = [aws_lambda_layer_version.auth_layer.arn]
  environment { variables = { REVIEWS_TABLE = aws_dynamodb_table.reviews.name, PRODUCTS_TABLE = aws_dynamodb_table.products.name, SECRET_KEY = var.jwt_secret } }
}

resource "aws_lambda_function" "wishlist_handler" {
  function_name    = "${var.project_name}-wishlist-handler"
  runtime          = "python3.12"
  handler          = "wishlist_handler.lambda_handler"
  filename         = data.archive_file.wishlist_handler_zip.output_path
  source_code_hash = data.archive_file.wishlist_handler_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  layers           = [aws_lambda_layer_version.auth_layer.arn]
  environment { variables = { WISHLIST_TABLE = aws_dynamodb_table.wishlist.name, PRODUCTS_TABLE = aws_dynamodb_table.products.name, REVIEWS_TABLE = aws_dynamodb_table.reviews.name, SECRET_KEY = var.jwt_secret } }
  timeout          = 30
  memory_size      = 256
}

resource "aws_lambda_function" "seller_product_handler" {
  function_name    = "${var.project_name}-seller-product-handler"
  runtime          = "python3.12"
  handler          = "product_handler.lambda_handler"
  filename         = data.archive_file.seller_product_handler_zip.output_path
  source_code_hash = data.archive_file.seller_product_handler_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  layers           = [aws_lambda_layer_version.auth_layer.arn]
  environment { variables = { PRODUCTS_TABLE = aws_dynamodb_table.products.name, SECRET_KEY = var.jwt_secret } }
}

resource "aws_lambda_function" "seller_order_handler" {
  function_name    = "${var.project_name}-seller-order-handler"
  runtime          = "python3.12"
  handler          = "order_handler.lambda_handler"
  filename         = data.archive_file.seller_order_handler_zip.output_path
  source_code_hash = data.archive_file.seller_order_handler_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  layers           = [aws_lambda_layer_version.auth_layer.arn]
  environment { variables = { ORDERS_TABLE = aws_dynamodb_table.orders.name, SECRET_KEY = var.jwt_secret } }
}

resource "aws_lambda_function" "seller_stats" {
  function_name    = "${var.project_name}-seller-stats"
  runtime          = "python3.12"
  handler          = "seller-stats.lambda_handler"
  filename         = data.archive_file.seller_stats_zip.output_path
  source_code_hash = data.archive_file.seller_stats_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  layers           = [aws_lambda_layer_version.auth_layer.arn]
  environment { variables = { PRODUCTS_TABLE = aws_dynamodb_table.products.name, ORDERS_TABLE = aws_dynamodb_table.orders.name, SECRET_KEY = var.jwt_secret } }
}

resource "aws_lambda_function" "get_upload_url" {
  function_name    = "${var.project_name}-get-upload-url"
  runtime          = "python3.12"
  handler          = "get-upload-url.lambda_handler"
  filename         = data.archive_file.upload_url_zip.output_path
  source_code_hash = data.archive_file.upload_url_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  environment { variables = { BUCKET_NAME = aws_s3_bucket.product_images.bucket } }
}

# --- S3 ACCESS POLICY ---
resource "aws_iam_role_policy" "lambda_s3" {
  name = "lambda-s3-access"
  role = aws_iam_role.lambda_exec.id
  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{ Effect = "Allow", Action = ["s3:PutObject"], Resource = "${aws_s3_bucket.product_images.arn}/*" }]
  })
}

# --- API GATEWAY ---

resource "aws_apigatewayv2_api" "api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }
}

# --- API INTEGRATIONS ---

locals {
  integrations = {
    "register"       = aws_lambda_function.auth_register.invoke_arn
    "login"          = aws_lambda_function.auth_login.invoke_arn
    "products"       = aws_lambda_function.product_handler.invoke_arn
    "cart"           = aws_lambda_function.cart_handler.invoke_arn
    "orders"         = aws_lambda_function.order_handler.invoke_arn
    "profile"        = aws_lambda_function.profile_handler.invoke_arn
    "reviews"        = aws_lambda_function.review_handler.invoke_arn
    "wishlist"       = aws_lambda_function.wishlist_handler.invoke_arn
    "seller_product" = aws_lambda_function.seller_product_handler.invoke_arn
    "seller_order"   = aws_lambda_function.seller_order_handler.invoke_arn
    "seller_stats"   = aws_lambda_function.seller_stats.invoke_arn
    "upload_url"     = aws_lambda_function.get_upload_url.invoke_arn
  }
}

resource "aws_apigatewayv2_integration" "this" {
  for_each         = local.integrations
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = each.value
}

# --- API ROUTES ---

resource "aws_apigatewayv2_route" "routes" {
  for_each = {
    "POST /register"          = aws_apigatewayv2_integration.this["register"].id
    "POST /login"             = aws_apigatewayv2_integration.this["login"].id
    "GET /products"           = aws_apigatewayv2_integration.this["products"].id
    "GET /cart"               = aws_apigatewayv2_integration.this["cart"].id
    "POST /cart"              = aws_apigatewayv2_integration.this["cart"].id
    "DELETE /cart"            = aws_apigatewayv2_integration.this["cart"].id
    "GET /orders"             = aws_apigatewayv2_integration.this["orders"].id
    "POST /orders"            = aws_apigatewayv2_integration.this["orders"].id
    "GET /profile"            = aws_apigatewayv2_integration.this["profile"].id
    "PUT /profile"            = aws_apigatewayv2_integration.this["profile"].id
    "GET /reviews"            = aws_apigatewayv2_integration.this["reviews"].id
    "POST /reviews"           = aws_apigatewayv2_integration.this["reviews"].id
    "GET /wishlist"           = aws_apigatewayv2_integration.this["wishlist"].id
    "POST /wishlist"          = aws_apigatewayv2_integration.this["wishlist"].id
    "GET /seller/products"    = aws_apigatewayv2_integration.this["seller_product"].id
    "POST /seller/products"   = aws_apigatewayv2_integration.this["seller_product"].id
    "PUT /seller/products"    = aws_apigatewayv2_integration.this["seller_product"].id
    "DELETE /seller/products" = aws_apigatewayv2_integration.this["seller_product"].id
    "GET /seller/orders"      = aws_apigatewayv2_integration.this["seller_order"].id
    "PUT /seller/orders"      = aws_apigatewayv2_integration.this["seller_order"].id
    "GET /seller-stats"       = aws_apigatewayv2_integration.this["seller_stats"].id
    "GET /get-upload-url"     = aws_apigatewayv2_integration.this["upload_url"].id
  }

  api_id    = aws_apigatewayv2_api.api.id
  route_key = each.key
  target    = "integrations/${each.value}"
}

# --- LAMBDA PERMISSIONS ---

resource "aws_lambda_permission" "permissions" {
  for_each = {
    register       = aws_lambda_function.auth_register.function_name
    login          = aws_lambda_function.auth_login.function_name
    products       = aws_lambda_function.product_handler.function_name
    cart           = aws_lambda_function.cart_handler.function_name
    orders         = aws_lambda_function.order_handler.function_name
    profile        = aws_lambda_function.profile_handler.function_name
    reviews        = aws_lambda_function.review_handler.function_name
    wishlist       = aws_lambda_function.wishlist_handler.function_name
    seller_product = aws_lambda_function.seller_product_handler.function_name
    seller_order   = aws_lambda_function.seller_order_handler.function_name
    seller_stats   = aws_lambda_function.seller_stats.function_name
    upload_url     = aws_lambda_function.get_upload_url.function_name
  }

  statement_id  = "AllowAPIGatewayInvoke-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
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

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- CLOUDFRONT OAC ---

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.project_name}-oac"
  description                       = "CloudFront OAC for IDPShop Frontend"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# --- UPDATED PRODUCT IMAGES POLICY (CLOUDFRONT ONLY) ---

resource "aws_s3_bucket_policy" "public_read" {
  bucket = aws_s3_bucket.product_images.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontAccess"
        Effect    = "Allow"
        Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.product_images.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })
}

resource "aws_cloudfront_function" "rewrite_uri" {
  name    = "rewrite-images-uri"
  runtime = "cloudfront-js-2.0"
  comment = "Strips /images prefix before sending to S3"
  publish = true
  code    = <<EOF
function handler(event) {
    var request = event.request;
    request.uri = request.uri.replace(/^\/images/, '');
    return request;
}
EOF
}

# --- CLOUDFRONT DISTRIBUTION (MULTI-ORIGIN) ---

resource "aws_cloudfront_distribution" "frontend" {
  # Origin 1: Frontend Website
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "S3-Frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  # Origin 2: Product Images
  origin {
    domain_name              = aws_s3_bucket.product_images.bucket_regional_domain_name
    origin_id                = "S3-Images"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "pages/auth/login.html"

  # Behavior 1: Images (/images/*)
  ordered_cache_behavior {
    path_pattern     = "/images/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-Images"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }


  # Behavior 2: Default (Frontend)
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-Frontend"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/pages/auth/login.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/pages/auth/login.html"
  }
}

# --- UPDATED FRONTEND BUCKET POLICY ---

resource "aws_s3_bucket_policy" "frontend_policy" {
  bucket = aws_s3_bucket.frontend.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontAccess"
        Effect    = "Allow"
        Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
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