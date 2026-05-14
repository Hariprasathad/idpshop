# --- TABLE ARNS ---
output "users_table_arn" { value = aws_dynamodb_table.users.arn }
output "products_table_arn" { value = aws_dynamodb_table.products.arn }
output "cart_table_arn" { value = aws_dynamodb_table.cart.arn }
output "orders_table_arn" { value = aws_dynamodb_table.orders.arn }
output "reviews_table_arn" { value = aws_dynamodb_table.reviews.arn }
output "wishlist_table_arn" { value = aws_dynamodb_table.wishlist.arn }

# --- STORAGE ---
output "product_images_bucket" { value = aws_s3_bucket.product_images.id }
output "product_images_base_url" { value = "https://${aws_s3_bucket.product_images.bucket}.s3.amazonaws.com" }

# --- FRONTEND ---
output "frontend_url" {
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
  description = "Access the IDPShop application securely via CloudFront"
}

# --- API ENDPOINTS (UNIFIED) ---
output "api_base_url" {
  value       = aws_apigatewayv2_api.api.api_endpoint
  description = "Base URL for the unified API Gateway"
}

output "public_endpoints" {
  value = {
    products = "${aws_apigatewayv2_api.api.api_endpoint}/products"
    login    = "${aws_apigatewayv2_api.api.api_endpoint}/login"
    register = "${aws_apigatewayv2_api.api.api_endpoint}/register"
  }
}

output "user_endpoints" {
  value = {
    cart     = "${aws_apigatewayv2_api.api.api_endpoint}/cart"
    orders   = "${aws_apigatewayv2_api.api.api_endpoint}/orders"
    profile  = "${aws_apigatewayv2_api.api.api_endpoint}/profile"
    reviews  = "${aws_apigatewayv2_api.api.api_endpoint}/reviews"
    wishlist = "${aws_apigatewayv2_api.api.api_endpoint}/wishlist"
  }
}

output "seller_endpoints" {
  value = {
    products   = "${aws_apigatewayv2_api.api.api_endpoint}/seller/products"
    orders     = "${aws_apigatewayv2_api.api.api_endpoint}/seller/orders"
    stats      = "${aws_apigatewayv2_api.api.api_endpoint}/seller-stats"
    upload_url = "${aws_apigatewayv2_api.api.api_endpoint}/get-upload-url"
  }
}
