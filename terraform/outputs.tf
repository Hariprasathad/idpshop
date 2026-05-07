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

output "reviews_table_name" {
  value = aws_dynamodb_table.reviews.name
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

output "add_review_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}add-review"
}

output "get_reviews_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}reviews"
}

output "get_products_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}products"
}

output "search_products_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}search-products"
}

output "add_to_cart_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}add-to-cart"
}

output "get_cart_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}cart"
}

output "add_wishlist_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}add-to-wishlist"
}

output "get_wishlist_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}wishlist"
}

output "get_my_orders_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}my-orders"
}

output "place_order_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}place-order"
}

output "get_profile_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}profile"
}

output "update_profile_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}profile"
}
