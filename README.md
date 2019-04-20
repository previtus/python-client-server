# python-client-server
Simple client to server pieces of code in python. The idea is to have several prepared versions (sending/receiving images etc).

## commands to connect ssh tunnel

Run the server code on distant machine.

Make a tunnel:

ssh -N -f -L localhost:8888:localhost:8123 USERNAME@HOST

Then you can connect to your:

localhost:8888