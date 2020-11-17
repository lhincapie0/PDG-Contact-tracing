import numpy as np
import matplotlib.pyplot as plt
import psycopg2
import pandas as pd
import sys
import datetime
from psycopg2 import connect
from psycopg2 import OperationalError, errorcodes, errors


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


connection = None
try:
    connection = psycopg2.connect(
        user="postgres", password="postgres", host="127.0.0.1", port="5432", database="pdgdata")
    cursor = connection.cursor()
    postgreSQL_select_Query = "SELECT * FROM(SELECT json_array_elements(data->'data'->'observations')->>'clientMac' as mac,json_array_elements(data->'data'->'observations')->>'seenTime' as time,json_array_length(json_array_elements(data->'data'->'observations')->'deviceObservers') as observers FROM public.example ORDER BY mac,time) as res WHERE res.mac='2446C8A8C839';"

    cursor.execute(postgreSQL_select_Query)
    print("Doing select time, mac and observers")
    mobile_records = cursor.fetchall()

    df = pd.DataFrame(data=mobile_records, columns=[
                      'mac', 'time', 'observers'])

    df['time'] = pd.to_datetime(df['time'])
    df.index = df['time']
    df_g = df.groupby(pd.Grouper(freq='1Min')).aggregate(np.sum)
    print(df_g)

    df_g.plot.bar()
    plt.tight_layout()

    # fig, ax = plt.subplots(figsize=(20, 10))
    # ax.bar(df_g.index, df_g['observers'])
    plt.show()


finally:
    # closing database connection.
    if(connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")
