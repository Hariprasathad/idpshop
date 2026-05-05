output "users_table_arn" {
  value = aws_dynamodb_table.users.arn
}

output "products_table_arn" {
  value = aws_dynamodb_table.products.arn
}

output "cart_table_arn" {
  value = aws_dynamodb_table.cart.arn
}

output "orders_table_arn" {
  value = aws_dynamodb_table.orders.arn
}

output "reviews_table_arn" {
  value = aws_dynamodb_table.reviews.arn
}

output "product_images_bucket_name" {
  value = aws_s3_bucket.product_images.id
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.api.api_endpoint
}

output "frontend_website_url" {
  value = aws_s3_bucket_website_configuration.frontend.website_endpoint
}
output "add_product_url" {
  value = "${aws_apigatewayv2_api.api.api_endpoint}/add-product"
}

output "upload_url_api" {
  value = "${aws_apigatewayv2_api.api.api_endpoint}/get-upload-url"
}

output "seller_products_url" {
  value = "${aws_apigatewayv2_api.api.api_endpoint}/seller-products"
}

output "update_product_url" {
  value = "${aws_apigatewayv2_api.api.api_endpoint}/update-product"
}

output "delete_product_url" {
  value = "${aws_apigatewayv2_api.api.api_endpoint}/delete-product"
}

output "seller_stats_url" {
  value = "${aws_apigatewayv2_api.api.api_endpoint}/seller-stats"
}

output "seller_orders_url" {
  value = "${aws_apigatewayv2_api.api.api_endpoint}/seller-orders"
}

output "update_order_status_url" {
  value = "${aws_apigatewayv2_api.api.api_endpoint}/update-order-status"
}

output "product_images_base_url" {
  value = "https://${aws_s3_bucket.product_images.bucket}.s3.amazonaws.com"
}
