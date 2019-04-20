from threading import Thread
import time

from PIL import Image
import flask
import os
from timeit import default_timer as timer
from multiprocessing.pool import ThreadPool
import numpy as np
import socket
import cv2

# Thanks to the tutorial at: https://blog.keras.io/building-a-simple-keras-deep-learning-rest-api.html

app = flask.Flask(__name__)
serverside_model = None
pool = ThreadPool()


times_del = []

class Server(object):
    """
    Server
    """

    def __init__(self):
        print("Server ... starting server and loading model ... please wait until its started ...")

        self.load_serverside_model()

        frequency_sec = 10.0
        t = Thread(target=self.mem_monitor_deamon, args=([frequency_sec]))
        t.daemon = True
        t.start()

        # hack to distinguish server by hostnames
        hostname = socket.gethostname()  # gpu048.etcetcetc.edu
        if hostname[0:3] == "gpu":
            app.run(host='0.0.0.0', port=8123)
        else:
            app.run()

    def mem_monitor_deamon(self, frequency_sec):
        import subprocess
        while (True):
            out = subprocess.Popen(['ps', 'v', '-p', str(os.getpid())],
                                   stdout=subprocess.PIPE).communicate()[0].split(b'\n')
            vsz_index = out[0].split().index(b'RSS')
            mem = float(out[1].split()[vsz_index]) / 1024

            print("Memory:", mem)
            time.sleep(frequency_sec)  # check every frequency_sec sec

    def load_serverside_model(self):
        global serverside_model
        serverside_model = None # model_handler.load_model()
        print('Model loaded.')



@app.route("/handshake", methods=["POST"])
def handshake():
    # Handshake

    data = {"success": False}
    start = timer()

    if flask.request.method == "POST":
        if flask.request.files.get("client"):
            client_message = flask.request.files["client"].read()
            print("Handshake, received: ",client_message)

            backup_name = flask.request.files["backup_name"].read()
            # try to figure out what kind of server we are, what is our name, where do we live, what are we like,
            # which gpu we occupy
            # and return it at an identifier to the client ~

            try:
                hostname = socket.gethostname() # gpu048.etcetcetc.edu
                machine_name = hostname.split(".")[0]
                buses = get_gpus_buses()
                print("Bus information =",buses)
                if len(buses) > 0:
                    buses = ":"+buses
                data["server_name"] = machine_name + buses
            except Exception as e:
                data["server_name"] = backup_name

            end = timer()
            data["internal_time"] = end - start
            data["success"] = True

    # return the data dictionary as a JSON response
    return flask.jsonify(data)

@app.route("/evaluate_image_batch", methods=["POST"])
def evaluate_image_batch():
    # Evaluate data
    data = {"success": False}
    if flask.request.method == "POST":
        uids = []
        imgs_data = []

        t_start_decode = timer()
        for key in flask.request.files:
            im_data = flask.request.files[key].read()

            imgs_data.append(im_data)
            uids.append(key)

        images = pool.map(lambda i: (
            cv2.imdecode(np.asarray(bytearray(i), dtype=np.uint8), 1)
        ), imgs_data)

        t_start_eval = timer()
        print("Received",len(images),"images (Decoded in",(t_start_eval-t_start_decode),".", uids, [i.shape for i in images])

        results = [] #serverside_model do something
        for image in images:
            results.append(image.shape)

        # send back an image:
        image = images[0]
        data["image_response"] = image.tolist()

        t_end_eval = timer()

        data["results"] = results
        data["uids"] = uids
        data["time_pure_eval"] = t_end_eval-t_start_eval
        data["time_pure_decode"] = t_start_eval-t_start_decode

        # indicate that the request was a success
        data["success"] = True

    t_to_jsonify = timer()
    as_json = flask.jsonify(data)
    t_to_jsonify = timer() - t_to_jsonify
    print("JSONify took", t_to_jsonify, "sec.")

    return as_json

from tensorflow.python.client import device_lib
def get_gpus_buses():
    local_device_protos = device_lib.list_local_devices()
    gpu_devices = [x for x in local_device_protos if x.device_type == 'GPU']
    buses = ""
    for device in gpu_devices:
        desc = device.physical_device_desc # device: 0, name: Tesla P100-PCIE-16GB, pci bus id: 0000:81:00.0
        bus = desc.split(",")[-1].split(" ")[-1][5:] # split to get to the bus information
        bus = bus[0:2] # idk if this covers every aspect of gpu bus
        if len(buses)>0:
            buses += ";"
        buses += str(bus)
    return buses


if __name__ == "__main__":
    server = Server()