import psycopg2
from rssi import RSSI_Localizer

print("hola")
accessPoint = {
    'signalAttenuation': 3,
    'location': {
        'y': 74,
        'x': 231
    },
    'reference': {
        'distance': 4,
        'signal': -50
    },
    'name': 'dd-wrt'
}
rssi_localizer_instance = RSSI_Localizer(accessPoints=accessPoint)

signalStrength = -99

distance = rssi_localizer_instance.getDistanceFromAP(
    accessPoint, signalStrength)


try:
    connection = psycopg2.connect(user="postgres",
                                  password="firewall990612",
                                  host="127.0.0.1",
                                  port="5433",
                                  database="PDGAccessPointsDB")
    cursor = connection.cursor()
    postgreSQL_select_Query = "SELECT apsfiles.data ->>'clientMac' as MAC, jsonb_array_length(apsfiles.data -> 'deviceObservers') as Observers, CAST(apsfiles.data ->>'seenTime' AS TIMESTAMP) as SEENTIME, data -> 'deviceObservers' -> 0 ->>'apMac' as apmac1,data -> 'deviceObservers' -> 1 ->>'apMac' as apmac2,data -> 'deviceObservers' -> 2 ->>'apMac' as apmac3,data -> 'deviceObservers' -> 3 ->>'apMac' as apmac4 FROM apsfiles, jsonb_array_elements(data -> 'deviceObservers')  GROUP BY apsfiles.data ORDER BY apsfiles.data -> 'seenTime' "

    cursor.execute(postgreSQL_select_Query)
    print("Selecting rows from apinfo table using cursor.fetchall")
    aps_records = cursor.fetchall()

    print("Print each row and it's columns values")
    for row in aps_records:
        if(row[1] == 4 or row[1] == 3):
            print("MAC = ", row[0], )
            print("Observers = ", row[1])
            print("Seen Time  = ", row[2], "\n")
            print(row[3])
            print(row[4])
            print(row[5])
            print(row[6])


except (Exception, psycopg2.Error) as error:
    print("Error while fetching data from PostgreSQL", error)

finally:
    # closing database connection.
    if(connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")
print(distance)
