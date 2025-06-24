import azure.functions as func
import pandas as pd
import io
from azure.storage.blob import BlobServiceClient
import os
from sqlalchemy import create_engine, text, MetaData, Table, select

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# azure connection
def get_blob_service_client():
    conn_str = os.getenv("AzureWebJobsStorage")
    if not conn_str:
        raise ValueError("AzureWebJobsStorage environment variable is not set.")
    return BlobServiceClient.from_connection_string(conn_str)


# postgres connection
DB_CONNECTION_STRING = (
    f"postgresql+psycopg2://{os.environ['DB_USERNAME']}:"
    f"{os.environ['DB_PASSWORD']}@"
    f"{os.environ['DB_HOST']}:"
    f"{os.environ['DB_PORT']}/"
    f"{os.environ['DB_NAME']}?sslmode={os.environ['DB_SSL_MODE']}"
)
engine = create_engine(DB_CONNECTION_STRING)
connection = engine.connect()
metadata = MetaData()

## Util Fns


def download_blob_to_bytes(blob_service_client, container, filename):
    blob_client = blob_service_client.get_blob_client(
        container=container, blob=filename
    )
    blob_data = blob_client.download_blob().readall()
    file_in_memory = io.BytesIO(blob_data)
    return file_in_memory


def upload_bytes_to_blob(blob_service_client, container, filename):
    blob_client = blob_service_client.get_blob_client(
        container=container, blob=filename
    )
    blob_client.upload_blob(overwrite=True)


def get_table_as_dataframe(table_name):
    stmt = select(table_name)
    results = connection.execute(stmt)
    df = pd.DataFrame(results.fetchall(), columns=results.keys())
    return df


@app.route(route="ELT_data_cleaning")
def ELT_data_cleaning(req: func.HttpRequest) -> func.HttpResponse:
    CONTAINER_NAME = "container_name"
    subset_data = "teis_subset_data()"
    with engine.begin() as conn:
        conn.execute(text(f"CALL {subset_data}"))
    subset_table = Table("teis_subset_records", metadata, autoload_with=engine)
    subset_df = get_table_as_dataframe(subset_table)
    subset_df.to_excel("teis_subset_records.xlsx")
    try:
        blob_service_client = get_blob_service_client()
        upload_bytes_to_blob(
            blob_service_client, CONTAINER_NAME, "teis_subset_records.xlsx"
        )

        return func.HttpResponse(
            "TEIS data cleaning and upload complete.",
            status_code=200,
            mimetype="text/plain",
        )
    except Exception as e:
        return func.HttpResponse(
            f"Error uploading files to Azure Blob Storage: {str(e)}",
            status_code=500,
            mimetype="text/plain",
        )


@app.route(route="upload_csv_to_postgres", methods=["POST"])
def upload_csv_to_postgres(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        target_file = req_body.get("target_file")
        blob_service_client = get_blob_service_client()
        CONTAINER_NAME = "container_name"
        file_in_memory = download_blob_to_bytes(
            blob_service_client, CONTAINER_NAME, target_file
        )
        df = pd.read_csv(file_in_memory)
        postgres_table_name = target_file.replace(".csv", "")
        df.to_sql(postgres_table_name, engine, index=False, if_exists="replace")

        return func.HttpResponse("Success", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
