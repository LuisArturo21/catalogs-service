import time
import os
import uuid
import boto3
from fastapi import FastAPI, Request, HTTPException
from botocore.exceptions import ClientError
from models import Customer, Product, Address
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Catalogs Service Microservice")


ENV = os.getenv("APP_ENVIRONMENT", "local")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION)

TABLE_CUSTOMERS = dynamodb.Table(os.getenv("TABLE_CUSTOMERS", "Customers"))
TABLE_PRODUCTS = dynamodb.Table(os.getenv("TABLE_PRODUCTS", "Products"))
TABLE_ADDRESSES = dynamodb.Table(os.getenv("TABLE_ADDRESSES", "Addresses"))

def send_metric(name, value, unit='Count'):
    """Envía métricas a CloudWatch solo si NO estamos en local"""
    if ENV == 'local':
        print(f"📊 [METRIC - {ENV}] {name}: {value} {unit}")
        return

    try:
        cloudwatch.put_metric_data(
            Namespace='SalesApp/Catalogs',
            MetricData=[
                {
                    'MetricName': name,
                    'Dimensions': [{'Name': 'Environment', 'Value': ENV}],
                    'Value': value,
                    'Unit': unit
                },
            ]
        )
    except Exception as e:
        print(f"Error enviando métrica: {e}")

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    send_metric('ExecutionTime', process_time, 'Milliseconds')
    
    if 200 <= response.status_code < 300:
        send_metric('2xx_Responses', 1)
    elif 400 <= response.status_code < 500:
        send_metric('4xx_Errors', 1)
    elif response.status_code >= 500:
        send_metric('5xx_Errors', 1)
        
    return response


@app.get("/")
def health_check():
    return {"status": "ok", "service": "catalogs-service", "env": ENV}

@app.post("/customers")
def create_customer(customer: Customer):
    customer_id = str(uuid.uuid4())
    item = customer.dict()
    item['ID'] = customer_id
    
    try:
        TABLE_CUSTOMERS.put_item(Item=item)
        return {"message": "Cliente creado", "ID": customer_id}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products")
def create_product(product: Product):
    product_id = str(uuid.uuid4())
    item = product.dict()
    item['ID'] = product_id
 
    item['precioBase'] = str(item['precioBase']) 
    
    try:
        TABLE_PRODUCTS.put_item(Item=item)
        return {"message": "Producto creado", "ID": product_id}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/addresses")
def create_address(address: Address):
    address_id = str(uuid.uuid4())
    item = address.dict()
    item['ID'] = address_id
    
    try:
        TABLE_ADDRESSES.put_item(Item=item)
        return {"message": "Domicilio creado", "ID": address_id}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))