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


