import owpy3
r = owpy3.Sensor("/","localhost",4304)
print("r",r)
e = r.entryList()
print("eentryList",e)
s=r.sensorList()
print("sensorList",s)

ss=r.sensors()
print("sensors",ss)

for x in ss:
    print("check",x)
    if hasattr(x,'temperature'):
        print(x,"temperature",x.temperature)