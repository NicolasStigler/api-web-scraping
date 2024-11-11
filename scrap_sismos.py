import requests
from bs4 import BeautifulSoup
import boto3
import uuid

def lambda_handler(event, context):
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"
    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder la página web'
        }

    # Parsear el contenido HTML de la pagina web
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Seleccionar filas de la tabla
    table = soup.find('table')
    if not table:
        return {
            'statusCode': 404,
            'body': 'No se encontro la tabla (posible rate limit)'
        }

    headers = [header.text.strip() for header in table.find_all('th')]
    
    sismos = []
    for row in table.find_all('tr')[1:11]:
        fields = row.find_all('td')
        sismos.append({headers[i]: field.text.strip() for i, field in enumerate(fields)})

    # Configurar DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaSismos')

    # Eliminar todos los elementos de la tabla antes de agregar los nuevos datos
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(
                Key={
                    'id': each['id']
                }
            )
    
    # Insertar datos en DynamoDB
    for sismo in sismos:
        sismo['id'] = str(uuid.uuid4())  # Generar un UUID para cada entrada
        table.put_item(Item=sismo)

    return {
        'statusCode': 200,
        'body': sismos
    }
