import numpy as np
import matplotlib.pyplot as plt
import psycopg2
import pandas as pd
import sys
import datetime
from psycopg2 import connect
from psycopg2 import OperationalError, errorcodes, errors

# El siguiete script tiene como función generar las gráficas de número de observadores presentados por los datos recogidos con el Webhook de Aerohive.

# Metodo que define los errores y excepciones de impresión


def print_psycopg2_exception(err):
    # get details about the exception
    err_type, err_obj, traceback = sys.exc_info()
    # get the line number when exception occured
    line_num = traceback.tb_lineno
    print("\npsycopg2 ERROR:", err, "on line number:", line_num)
    print("psycopg2 traceback:", traceback, "-- type:", err_type)
    # psycopg2 extensions.Diagnostics object attribute
    print("\nextensions.Diagnostics:", err.diag)
    # print the pgcode and pgerror exceptions
    print("pgerror:", err.pgerror)
    print("pgcode:", err.pgcode, "\n")


# Variable que contiene la conexión a la base de datos de postgresql donde están cargados los archivos JSON con los datos de las pruebas
connection = None
try:
    # Conexión a la base de datos. Esta corre en un servidor local de postgresql
    connection = psycopg2.connect(
        user="postgres", password="postgres", host="127.0.0.1", port="5432", database="pdgdata")
    cursor = connection.cursor()
    # Consulta que obtiene los datos para cada día y dispositivo. Se deben cambiar el nombre de la tabla dependiendo del día para el que se necesiten los datos
    # Se debe cambiar la variable res.mac a la dirección del dispositivo para el que se desee generar la gráfica
    # El retorno consiste en una lista de tuplas que contienen la mac, tiempo y número de observadores
    postgreSQL_select_Query = "SELECT * FROM(SELECT json_array_elements(data->'data'->'observations')->>'clientMac' as mac,json_array_elements(data->'data'->'observations')->>'seenTime' as time,json_array_length(json_array_elements(data->'data'->'observations')->'deviceObservers') as observers FROM public.example15dic ORDER BY mac,time) as res WHERE res.mac='F81F32423A55';"

    cursor.execute(postgreSQL_select_Query)
    print("Doing select time, mac and observers")
    mobile_records = cursor.fetchall()

# Carga de los datos en un dataFrame del framework pandas
    df = pd.DataFrame(data=mobile_records, columns=[
                      'mac', 'time', 'observers'])

# Cambio de formato de la variable del tiempo. Se pasa de string a datetime
    df['time'] = pd.to_datetime(df['time'])
    df.index = df['time']
# Agrupación de las visitas por tiempo para que la gráfica salga ordenada por minutos
    df_g = df.groupby(pd.Grouper(freq='1Min')).aggregate(np.sum)
    print(df_g)
# Ploteo de la gráfica en formato de barras
    df_g.plot.bar()
    plt.tight_layout()
    plt.show()


finally:
    # Cierre de la conexión con la base de datos
    if(connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")
