from requests_html import HTMLSession
import boto3
import uuid

def lambda_handler(event, context):
    session = HTMLSession()
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"

    # Hacer la solicitud y renderizar el contenido dinámico
    response = session.get(url)
    response.html.render(sleep=4)  # Renderizar JavaScript con retraso

    # Encontrar la tabla de sismos
    rows = response.html.find('.table-hover tbody tr')

    if not rows:
        return {
            'statusCode': 404,
            'body': 'No se encontro la tabla de sismos (posible cambio de estructura)'
        }

    # Extraer los datos de los 10 ultimos sismos
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

    # Limpiar la tabla DynamoDB antes de insertar nuevos datos
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(Key={'id': each['id']})

    # Insertar los nuevos datos
    with table.batch_writer() as batch:
        for sismo in sismos:
            batch.put_item(Item=sismo)

    return {
        'statusCode': 200,
        'body': sismos
    }
