import datetime

date_time_str = '2020-10-31T21:23:23.052Z'
time = date_time_str.replace('T', ' ')
time = time.replace('Z', ' ')

print(time)
date_time_obj = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')

#print('Date:', date_time_obj.date())
