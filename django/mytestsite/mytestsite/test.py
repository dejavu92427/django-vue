import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.db import connections
with connections['overview'].cursor() as cursor:
    cursor.execute("SELECT domainName FROM nsone")

myresult = cursor.fetchall()

print(myresult)

for x in myresult:
  print(x)
