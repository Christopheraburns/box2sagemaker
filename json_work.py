from __future__ import print_function
import json
import requests
from io import BytesIO
import io



token = 'nacho-token'


# Get the file info so we can see if this Lambda function has sufficient time to download it
#url = 'https://api.box.com/2.0/files/313239278455?access_token=' + token
#r = requests.get(url)

url = 'https://api.box.com/2.0/files/313238975331/content?access_token=' + token
r = requests.get(url)

with io.BytesIO() as buffer:
    buffer.write(r.content)
    buffer.seek(0)

what = r.content
print("return type: {}".format(type(what)))

bytes_ = BytesIO(r.content)
print("bytes_ type: {}".format(type(bytes_)))

print("buffer type: {}".format(type(buffer)))