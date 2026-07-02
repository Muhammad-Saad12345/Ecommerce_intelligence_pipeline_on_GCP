Project Overview
Project Name

E-Commerce Data Engineering Platform on GCP

Project Type

Batch data pipeline architecture using the Olist e-commerce CSV dataset.

Goal

The goal of this project is to build an end-to-end data engineering platform that ingests raw e-commerce CSV files, validates them, stores them in Google Cloud Storage, loads them into BigQuery Bronze tables, and prepares them for Silver and Gold transformations.

Business Problem

E-commerce data usually comes from different sources such as:

Orders
Customers
Products
Sellers
Payments
Reviews
Inventory or operational systems

When this data is not centralized, business reporting becomes slow, inconsistent, and difficult to trust.

This project solves the problem by creating a controlled pipeline where every uploaded file is validated, loaded, audited, and traceable.

Target Users

This platform is useful for:

Data analysts
Data engineers
Business intelligence teams
E-commerce operations teams
Finance and sales reporting teams
Current Completed Phase

The current completed phase is:

Foundation + Bronze Ingestion

Completed work includes:

GCP project setup
GCS bucket structure
BigQuery datasets
Cloud Run ingestion service
UI upload interface
CLI testing flow
CSV schema validation
Duplicate file detection
Rejected file handling
BigQuery Bronze loading
BigQuery audit logging
Current Architecture Scope

Current v1 scope:

Olist CSV Dataset
→ GCS tmp/raw/rejected
→ Cloud Run validation
→ BigQuery Bronze
→ Audit tables

Future phases:

Bronze → dbt Silver → dbt Gold → Looker Studio → AI Insights
What Is Not Included Yet

The following are not included in the current phase:

dbt Silver models
Gold facts and dimensions
Business marts
Looker Studio dashboards
Cloud Composer orchestration
Monitoring alerts
AI insights
Real-time clickstream
External APIs
Why This Project Matters

This project demonstrates real data engineering skills:

Cloud storage design
Serverless ingestion
Data validation
Data quality logging
BigQuery loading
Auditability
Medallion architecture
Production-style debugging
Portfolio-ready documentation
Current Status

The Bronze ingestion pipeline is working successfully.

The next step is to document the Bronze phase and then move to the dbt Silver layer.