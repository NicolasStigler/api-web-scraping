from requests_html import HTMLSession
import boto3
import uuid

def lambda_handler(event, context):
    session = HTMLSession()
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"
    response = session.get(url)
    response.html.render()  # Renderizar JavaScript

    # Seleccionar filas de la tabla
    rows = response.html.find('.table-hover tbody tr')

    sismos = []
    for row in rows[:10]:
        columns = row.find('td')
        sismo = {
            'id': str(uuid.uuid4()),
            'reporte': columns[0].text,
            'referencia': columns[1].text,
            'fecha_hora': columns[2].text,
            'magnitud': columns[3].text
        }
        sismos.append(sismo)

    # Configurar DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaSismos')

    # Insertar datos en DynamoDB
    with table.batch_writer() as batch:
        for sismo in sismos:
            batch.put_item(Item=sismo)

    return {
        'statusCode': 200,
        'body': sismos
    }
