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

distance = rssi_localizer_instance.getDistanceFromAP(accessPoint, signalStrength)

print(distance)