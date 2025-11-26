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

@app.get("/customers")
def list_customers():
    try:
        response = TABLE_CUSTOMERS.scan()
        return response.get('Items', [])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    try:
        response = TABLE_CUSTOMERS.get_item(Key={'ID': customer_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return response['Item']
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/customers/{customer_id}")
def update_customer(customer_id: str, customer: Customer):
    # En DynamoDB, put_item con el mismo ID sobrescribe (actualiza) el elemento
    item = customer.dict()
    item['ID'] = customer_id
    try:
        TABLE_CUSTOMERS.put_item(Item=item)
        return {"message": "Cliente actualizado", "ID": customer_id}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: str):
    try:
        TABLE_CUSTOMERS.delete_item(Key={'ID': customer_id})
        return {"message": "Cliente eliminado"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/products")
def create_product(product: Product):
    product_id = str(uuid.uuid4())
    item = product.dict()
    item['ID'] = product_id
    item['precioBase'] = str(item['precioBase']) # Convertir float a string para DynamoDB
    try:
        TABLE_PRODUCTS.put_item(Item=item)
        return {"message": "Producto creado", "ID": product_id}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products")
def list_products():
    try:
        response = TABLE_PRODUCTS.scan()
        return response.get('Items', [])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/{product_id}")
def get_product(product_id: str):
    try:
        response = TABLE_PRODUCTS.get_item(Key={'ID': product_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return response['Item']
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/products/{product_id}")
def update_product(product_id: str, product: Product):
    item = product.dict()
    item['ID'] = product_id
    item['precioBase'] = str(item['precioBase'])
    try:
        TABLE_PRODUCTS.put_item(Item=item)
        return {"message": "Producto actualizado", "ID": product_id}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    try:
        TABLE_PRODUCTS.delete_item(Key={'ID': product_id})
        return {"message": "Producto eliminado"}
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

@app.get("/addresses")
def list_addresses():
    try:
        response = TABLE_ADDRESSES.scan()
        return response.get('Items', [])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/addresses/{address_id}")
def get_address(address_id: str):
    try:
        response = TABLE_ADDRESSES.get_item(Key={'ID': address_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Domicilio no encontrado")
        return response['Item']
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/addresses/{address_id}")
def update_address(address_id: str, address: Address):
    item = address.dict()
    item['ID'] = address_id
    try:
        TABLE_ADDRESSES.put_item(Item=item)
        return {"message": "Domicilio actualizado", "ID": address_id}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/addresses/{address_id}")
def delete_address(address_id: str):
    try:
        TABLE_ADDRESSES.delete_item(Key={'ID': address_id})
        return {"message": "Domicilio eliminado"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))