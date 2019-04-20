import requests
from timeit import default_timer as timer

# = HANDSHAKE =================================================
PORT = "5000"
Handshake_REST_API_URL = "http://localhost:"+PORT+"/handshake"

payload = {"client": "client", "backup_name":"Bob"}
r = requests.post(Handshake_REST_API_URL, files=payload).json()
print("Handshake request data", r)

# = SEND BATCH OF IMAGES =====================================

PORT = "5000"
Images_REST_API_URL = "http://localhost:"+PORT+"/evaluate_image_batch"
IMAGE_PATH = "small.jpg"

BATCH_SIZE = 8 # 8, 16

payload = {}
for i in range(BATCH_SIZE):
    image = open(IMAGE_PATH, "rb").read()
    payload[str(i)] = image

# submit the request
start = timer()
r = requests.post(Images_REST_API_URL, files=payload).json()
total_time = timer() - start
print("Time total", total_time, "divby"+str(BATCH_SIZE)+" =", total_time/float(BATCH_SIZE))
print("request data", r)
for i,item in enumerate(r['results']):
    print(r['uids'][i]," = len results", len(item), item)
