# 🛒 IDPShop — Serverless E-Commerce Platform

A fully serverless e-commerce platform built using AWS cloud services, microservices architecture, and modern frontend technologies.

---

# 📌 Project Overview

IDPShop is a cloud-native e-commerce application where:

- Customers can browse and purchase products
- Sellers can manage inventory and orders
- APIs are powered by AWS Lambda microservices
- Data is stored in DynamoDB
- Frontend is hosted using AWS S3 + CloudFront CDN

---

# 🏗️ Architecture Diagram

![alt image](image.png)

---

# 🚀 Features

## 👤 Customer Features

- User Registration & Login
- JWT Authentication
- Browse Products
- Search Products
- View Product Details
- Add to Cart
- Wishlist
- Place Orders
- View Order History
- Add Reviews

---

## 🛍️ Seller Features

- Seller Dashboard
- Add Products
- Upload Product Images
- Edit Products
- Manage Inventory
- View Orders
- Update Order Status

---

# ☁️ AWS Services Used

| AWS Service | Purpose |
|---|---|
| AWS Lambda | Backend Microservices |
| API Gateway | REST APIs |
| DynamoDB | NoSQL Database |
| S3 | Frontend Hosting + Product Images |
| CloudFront | CDN Delivery |
| IAM | Access Management |
| CloudWatch | Logs & Monitoring |

---

# 🧩 Microservices Architecture

The backend is divided into multiple Lambda services:

```text
Auth Service
Product Service
Cart Service
Wishlist Service
Order Service
Review Service
Profile Service