import boto3
import uuid
import playwright.sync_api import sync_playwright

def lambda_handler(event, context):
    # Configurar DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaSismos')

    # Usar Playwright para cargar la página
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados")

        # Esperar a que se cargue la tabla
        page.wait_for_selector('.table-hover')

        # Obtener las filas de la tabla
        rows = page.query_selector_all('.table-hover tbody tr')

        sismos = []
        for row in rows[:10]:
            columns = row.query_selector_all('td')
            reporte = columns[0].inner_text().strip()
            referencia = columns[1].inner_text().strip()
            fecha_hora = columns[2].inner_text().strip()
            magnitud = columns[3].inner_text().strip()

            sismo = {
                'id': str(uuid.uuid4()),
                'reporte': reporte,
                'referencia': referencia,
                'fecha_hora': fecha_hora,
                'magnitud': magnitud
            }
            sismos.append(sismo)

        # Limpiar la tabla DynamoDB antes de insertar nuevos datos
        scan = table.scan()
        with table.batch_writer() as batch:
            for each in scan['Items']:
                batch.delete_item(Key={'id': each['id']})

        # Insertar los nuevos datos
        for sismo in sismos:
            table.put_item(Item=sismo)

        browser.close()

    return {
        'statusCode': 200,
        'body': sismos
    }
