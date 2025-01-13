from sqlalchemy import create_engine, Column, Integer, String, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = 'mysql+mysqlconnector://root:contrasena@127.0.0.1:3306/factura'
engine = create_engine(DATABASE_URL, echo=True)

Base = declarative_base()

class Factura(Base):
    __tablename__ = 'facturas'

    id = Column(Integer, primary_key=True)
    numero_factura = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)
    monto_total = Column(Float, nullable=False)
    impuestos = Column(Float, nullable=False)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# incompatibilidad con librerias de AZURE
from pathlib import Path
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from utility import client, load_file_as_base64

document_dir = Path(r'C:\Users\danie\Downloads\Postulación Skandia\AI Azure')
file_path = document_dir / 'PCO091020818_00354_W_73017_14771817.pdf'

if not file_path.exists():
    raise FileNotFoundError(f'File {file_path} not found')

model_id = 'facturas'

document_ai_client = client()

file_base64 = load_file_as_base64(file_path)

poller = document_ai_client.begin_analyze_document(
    model=model_id,
    document={"base64Source": file_base64},
    locale="en-US"
)

result = poller.result()

for document in result.documents:
    document_fields = document.fields
    
    numero_factura = None
    fecha = None
    monto_total = None
    impuestos = None

    for field, value in document_fields.items():
        if field == 'InvoiceNumber':
            numero_factura = value.content
        elif field == 'InvoiceDate':
            fecha = datetime.strptime(value.content, '%Y-%m-%d') 
        elif field == 'TotalAmount':
            monto_total = float(value.content)
        elif field == 'TaxAmount':
            impuestos = float(value.content)

    if numero_factura and fecha and monto_total is not None and impuestos is not None:
        factura = Factura(
            numero_factura=numero_factura,
            fecha=fecha,
            monto_total=monto_total,
            impuestos=impuestos
        )

        session.add(factura)
        session.commit()

        print(f'Factura {numero_factura} insertada en la base de datos.')

session.close()
