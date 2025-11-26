from pydantic import BaseModel
from typing import Optional

class Customer(BaseModel):
    razonSocial: str
    nombreComercial: str
    rfc: str
    correo: str
    telefono: str

class Product(BaseModel):
    nombre: str
    unidadMedida: str
    precioBase: float

class Address(BaseModel):
    customerID: str
    domicilio: str
    colonia: str
    municipio: str
    estado: str
    tipoDireccion: str # FACTURACION | ENVIO