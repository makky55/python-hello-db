from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
import os
import boto3
import mysql.connector

import os

DATABASE_HOST = os.environ['DATABASE_HOST']
DATABASE_PORT = os.environ['DATABASE_PORT']
DATABASE_USER = os.environ['DATABASE_USER']
DATABASE_NAME = os.environ['DATABASE_NAME']

os.environ['LIBMYSQL_ENABLE_CLEARTEXT_PLUGIN'] = '1'

PORT = int(os.environ.get('PORT'))

REGION = 'ap-northeast-1'

# Function for get_parameters
def get_parameters(param_key):
    ssm = boto3.client('ssm', region_name=REGION)
    response = ssm.get_parameters(
        Names=[
            param_key,
        ],
        WithDecryption=False
    )
    return response['Parameters'][0]['Value']    

def all_books(request):
    param_key = "db-pass"
    
    # get parameter value
    param_value = get_parameters(param_key)
    
    mydb =  mysql.connector.connect(
        host=DATABASE_HOST,
        user=DATABASE_USER,
        passwd=param_value,
        port=DATABASE_PORT,
        database=DATABASE_NAME
    )
    
    mycursor = mydb.cursor()
    mycursor.execute('SELECT name, title, year FROM authors, books WHERE authors.authorId = books.authorId ORDER BY year')
    title = 'Books'
    message = '<html><head><title>' + title + '</title></head><body>'
    message += '<h1>' + title + '</h1>'
    message += '<ul>'
    for (name, title, year) in mycursor:
        message += '<li>' + name + ' - ' + title + ' (' + str(year) + ')</li>'
    message += '</ul>'
    message += '</body></html>'
    return Response(message)

if __name__ == '__main__':

    with Configurator() as config:
        config.add_route('all_books', '/')
        config.add_view(all_books, route_name='all_books')
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', PORT, app)
    server.serve_forever()
