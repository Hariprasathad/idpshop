<div align="center">
  <img src="frontend/public/idp_shop_logo.png" alt="IDPShop Logo" width="300" />
</div>

# 🛒 IDPShop — Serverless E-Commerce Platform

A fully serverless, highly-scalable e-commerce platform built on AWS microservices and modern frontend technologies.

**🌐 Live Demo:** [https://d3r1l4tg7odjwk.cloudfront.net/pages/auth/login.html](https://d3r1l4tg7odjwk.cloudfront.net/pages/auth/login.html)
---

## 📌 Project Overview

IDPShop is a comprehensive, cloud-native application designed to provide a robust shopping experience:
- **Customers** can browse, search, manage their carts/wishlists, and place orders securely.
- **Sellers** have access to a dedicated dashboard to manage products, inventory, and order fulfillment.
- **Backend APIs** are entirely serverless, powered by AWS Lambda and orchestrated by API Gateway.
- **Database** operations rely on DynamoDB for high-throughput NoSQL storage.
- **Frontend** assets are served globally via AWS S3 and CloudFront CDN.

---

## 🧪 Demo Credentials (Admin/Seller Access)
To evaluate the platform's restricted seller capabilities, use the following test credentials to log into the Seller Dashboard:
- **Email**: `idpseller@gmail.com`
- **Password**: `1234`

*(Note: Seller accounts are strictly Admin-only and cannot be created via the public registration page. They possess exclusive read/write access to product management and real-time order tracking.)*

---

## 🏗️ Architecture Design

![IDPShop System Architecture](architecture.png)

### User (Customer) Flow:
1. Register/Login (JWT Token Generated)
2. Browse/Search Products 
3. View Product → Add to Cart / Wishlist / Review
4. Place Order → Inventory/Stock Update
5. Order Success

### Seller Flow:
1. Login to Seller Dashboard
2. Add/Edit Products and Upload Images to S3
3. Manage Inventory & Stock
4. View and Update Order Statuses (Processing → Shipped → Delivered)

### 🖼️ Serverless Image Storage Flow (A to Z)
To ensure maximum performance and scalability, product image uploads bypass the backend using a secure serverless pattern:
1. **Request**: Seller selects an image in the frontend UI.
2. **Pre-signed URL**: The frontend requests a secure, temporary upload link from the API Gateway & Lambda (`get_upload_url`).
3. **Direct Upload**: The image is uploaded directly from the browser to the **Amazon S3** Bucket using the pre-signed URL (bypassing Lambda limits).
4. **Database Record**: The resulting permanent S3 image URL is saved directly into DynamoDB alongside the product details.
5. **Global Delivery**: When customers browse the catalog, images are delivered lightning-fast globally via the **CloudFront CDN**.

### 📊 Observability & Alerting Architecture
To ensure high availability and rapid debugging, the platform implements a comprehensive DevOps observability stack:
1. **Distributed Tracing**: **AWS X-Ray** maps end-to-end request latency as traffic flows from API Gateway → Lambda → DynamoDB & SNS.
2. **Centralized Monitoring**: A **CloudWatch Dashboard** provides a single-pane-of-glass view of API traffic, Lambda invocations, throttling, and DynamoDB capacity.
3. **Automated Alerting**: **CloudWatch Alarms** monitor Lambda error thresholds and automatically trigger **SNS Topics** to send real-time email alerts to administrators if an issue occurs.

---

## 🚀 Key Features

### 👤 Customer Features
- **Authentication**: Secure JWT-based registration and login.
- **Catalog**: Dynamic product browsing, search, and detailed views.
- **Cart & Wishlist**: Persistent cart and wishlist management.
- **Checkout**: Seamless order placement with real-time stock checks and profile validation.
- **Orders**: Tracking order history and status.
- **Reviews**: Ability to rate and review purchased products.

### 🛍️ Seller Features
- **Dashboard**: Centralized hub for metrics and operations.
- **Product Management**: Create, edit, and categorize products with image uploads.
- **Inventory Control**: Real-time stock tracking with "Low Stock" and "Out of Stock" alerts.
- **Order Fulfillment**: Track incoming orders and update delivery statuses.

### 🎨 UI & User Experience
- **Modern Aesthetic**: A sleek, professional "white and blue" color scheme providing a clean and trustworthy shopping environment.
- **Real-Time Interface**: Dynamic DOM updates for instant visual feedback when adding to carts, viewing live stock, or tracking orders.

### 📊 Monitoring & Observability
- **Event-Driven Notifications (SNS)**: Real-time email alerts for new business orders and critical system crashes.
- **Distributed Tracing (X-Ray)**: Full end-to-end request tracing mapping API Gateway, Lambda, DynamoDB, and SNS interactions.
- **Centralized Dashboards (CloudWatch)**: Single pane of glass monitoring API traffic, Lambda invocations/errors, and DynamoDB capacity.
- **Automated Alarms (CloudWatch)**: Self-monitoring infrastructure that automatically alerts administrators upon consecutive Lambda failures.

---

## ☁️ AWS Services Stack

| Service | Purpose |
|---|---|
| **AWS Lambda** | Isolated backend microservices (Auth, Product, Cart, Wishlist, Order, Review, Profile). |
| **API Gateway** | RESTful API routing and management. |
| **DynamoDB** | Fully managed NoSQL database for structured data storage. |
| **Amazon S3** | Static website hosting and persistent product image storage. |
| **CloudFront** | Global Content Delivery Network (CDN) for fast asset serving. |
| **Amazon SNS** | Event-driven email notifications for business (New Orders) and system alerts (Errors). |
| **CloudWatch** | Centralized dashboards, metrics, log aggregation, and automated alarms. |
| **AWS X-Ray** | Distributed tracing for end-to-end request latency and bottleneck visualization. |

---

## 📂 Project Structure

```text
idpshop/
├── .github/workflows/    # CI pipelines (GitHub Actions)
├── backend/              # AWS Lambda microservices
│   ├── auth/             # Login, Registration & JWT handlers
│   ├── cart/             # Cart operations
│   ├── layers/           # AWS Lambda Layers (bcrypt, pyjwt)
│   ├── orders/           # Customer order placement & fulfillment
│   ├── product/          # Browsing and Search logic
│   ├── profile/          # User profile operations
│   ├── review/           # Product rating & review handlers
│   ├── s3/               # S3 Pre-signed URL generation for image uploads
│   ├── seller/           # Seller-specific restricted endpoints (orders, products, stats)
│   ├── tests/            # Pytest unit testing suite
│   └── wishlist/         # Wishlist operations
├── frontend/             # Static Web Assets
│   ├── css/              # Global & modular styling
│   ├── js/               # API clients, authentication, & page logic
│   ├── pages/            # HTML Views (Auth, Customer, Seller)
│   └── public/           # Logos & static icons
├── terraform/            # Infrastructure as Code (IaC)
└── architecture.png      # System architecture diagram
```

---

## 🤖 Continuous Integration (CI)

This repository implements a **Continuous Integration (CI)** pipeline via **GitHub Actions** (`.github/workflows/ci.yml`) to ensure high code quality and infrastructure integrity. 

**Note: This is a CI-only workflow. It does NOT automatically deploy to production.**

### Pipeline Tasks (Triggered on `git push`):
1. ✅ **Checkout Code**: Retrieves the latest commit.
2. ✅ **Setup Python 3.12**: Provisions the runtime environment.
3. ✅ **Install Dependencies**: Installs required libraries (`boto3`, `pyjwt`, `bcrypt`).
4. ✅ **Python Syntax Check**: Validates syntax across all `backend/**/*.py` files.
5. ✅ **Terraform Setup & Init**: Prepares the HashiCorp Terraform environment.
6. ✅ **Terraform Validate**: Ensures all IaC configuration files are structurally correct.

### Benefits
- Catches logic and syntax errors early.
- Enforces professional development workflows.
- Prevents breaking infrastructure configurations from being merged.
- Mitigates the risk of unintended automatic deployments to live AWS environments.

---

*Developed for the IDPShop E-Commerce Initiative.*