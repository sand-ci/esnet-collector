#!/usr/bin/env python3
import urllib.request
import datetime
import json
import mysql.connector

db_connect = mysql.connector.connect(host="", user="", password="", database="" )
print(db_connect)
my_cursor = db_connect.cursor()   

with urllib.request.urlopen("https://esnet-netbeam.appspot.com/api/network/esnet/prod/interfaces") as url:
    data = json.load(url)
    seconds = datetime.datetime.utcnow().timestamp()
    timestamp_in_millis = round(seconds * 1000)
    i = 0;

    for datum in data:
        datum['timestamp'] = timestamp_in_millis
        status = 1
        sql = "INSERT INTO int_test (name, status, active_from) SELECT * FROM (select %s, %s, %s) as tmp WHERE NOT EXISTS (SELECT name FROM int_test WHERE name = %s AND status = %s)LIMIT 1 "
        val = (datum['resource'], status, datum['timestamp'], datum['resource'], status)
        my_cursor.execute(sql, val)

        i+= 1;

db_connect.commit()
print( "{} record(s) inserted".format(i))   

