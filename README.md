# Azure ↔️ Postgres ELT Data Pipeline

This project provides a template for an ELT (Extract, Load, Transform) data pipeline that moves data between Azure Blob Storage and a PostgreSQL database, with transformation and reporting steps in between. The pipeline is implemented as an Azure Function App in Python.

## Overview

- **Extract**: Data is extracted from Azure Blob Storage (CSV files).
- **Load**: Extracted data is loaded into a PostgreSQL database.
- **Transform**: Data is transformed in Postgres (via stored procedures).
- **Export**: Transformed data is exported back to Azure Blob Storage (as Excel files).

## Pipeline Steps

1. **Upload CSV to Postgres**
   - Triggered via the `/upload_csv_to_postgres` HTTP endpoint (POST).
   - Downloads a CSV file from Azure Blob Storage.
   - Loads the CSV data into a Postgres table (table name matches the CSV filename).

2. **Data Cleaning & Export**
   - Triggered via the `/ELT_data_cleaning` HTTP endpoint (GET).
   - Calls a Postgres stored procedure to create a cleaned/filtered subset table.
   - Reads the subset table into a Pandas DataFrame.
   - Exports the DataFrame as an Excel file.
   - Uploads the Excel file back to Azure Blob Storage.

## File Structure

- `function_app.py` — Main Azure Function App with HTTP endpoints for pipeline steps.
- `queries.sql` — Placeholder for SQL queries and stored procedures used in transformation.
- `postgres/docker-compose.yml` — Local Postgres setup for development/testing.
- `requirements.txt` — Python dependencies.
- `local.settings.json` — Local Azure Functions settings (can be redirected for production).

## Environment Variables

The following environment variables must be set (e.g., in Azure or `local.settings.json`):
- `AzureWebJobsStorage` — Azure Blob Storage connection string
- `DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_SSL_MODE` — Postgres connection details

## Usage

1. **Start Postgres (locally):**
   ```sh
   cd postgres
   docker-compose up -d
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Run Azure Functions locally:**
   ```sh
   func start
   ```
4. **Trigger endpoints:**
   - POST `/upload_csv_to_postgres` with JSON `{ "target_file": "yourfile.csv" }`
   - GET `/ELT_data_cleaning`

## Notes
- The pipeline expects CSV files in a specified Azure Blob container.
- The transformation logic (subset creation, cleaning) should be implemented in Postgres (see `queries.sql`).
- The output Excel file is uploaded back to Azure Blob Storage for downstream use.

