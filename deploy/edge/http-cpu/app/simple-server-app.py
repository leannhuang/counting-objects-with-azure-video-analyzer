# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import json
import logging
from datetime import datetime, timezone

from flask import Flask, Response, Request, abort, request
from azure.iot.device import IoTHubModuleClient

from exception_handler import PrintGetExceptionDetails
from infer_cache import infer_cache
from listen_thread import ListenThread

def init_logging():
    gunicorn_logger = logging.getLogger('gunicorn.error')
    if gunicorn_logger != None:
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

app = Flask(__name__)
init_logging()

# Gives ability to recieve and send iot edge hub messages to/from
# different modules on the edge.
try:
    # The client object is used to interact with your Azure IoT hub.
    logging.info("Creating iot hub module client from edge env")
    module_client = IoTHubModuleClient.create_from_edge_environment()
    # connect the client
    logging.info("Connecting to iot hub module client")
    module_client.connect()
except Exception as err:
    # PrintGetExceptionDetails()
    logging.error("Execption in creating and connecting to iot hub module client: {}".format(err))

# / routes to the default function
@app.route('/', methods=['GET'])
def default_page():
    """Default route/page"""
    return Response(response='Hello from simple server!', status=200)

# /score routes to scoring function 
@app.route("/score", methods=['POST'])
def score():
    """This function returns a JSON object with inference duration and detected objects"""
    # Current date and time - might be overwritten by avaedge timestamp
    now = datetime.now()
    try:
        respBody = {
                 "inferences" : []
                 }
        print("--------http request handler--------")
        print("Get the frame from AVA")
        print(f'time: {now}')
        # get bounding box with closest timestamp
        infer_result, closest_ts = infer_cache.get(now)
        respBody = {
                        "timestamp" : str(closest_ts),
                        "inferences" : infer_result
                    }

        respBody = json.dumps(respBody)
        print(f'resp: {respBody}')
        print('*************************************')
        
        return Response(respBody, status=200, mimetype='application/json')


    except Exception as err:
        # PrintGetExceptionDetails()
        logging.error("Exception in score function.")      
        return Response(json.dumps({"Execption in score function: {}".format(err)}), status=500)

# /score-debug routes to score_debug
# This function scores the image and stores an annotated image for debugging purposes
@app.route('/score-debug', methods=['POST'])
def score_debug():
    """This function returns a JSON object with inference duration and detected objects"""
    try:
        detected_objects = []
        # send mock bounding box to AVA w/o collecting msg with “receive_message_on_input" function
        json_data = {
                        "type": "entity",
                        "entity" : {
                            "tag" : {
                                "value" : "person",
                                "confidence": float(0.9),
                            },
                            "box": {
                                "l": 0.2,
                                "t": 0.3,
                                "w": 0.5,
                                "h": 0.5
                            }
                        }
                    }
        
        detected_objects.append(json_data)
        respBody = {
                        "inferences" : detected_objects
                    }
        respBody = json.dumps(respBody)
        return Response(respBody, status=200, mimetype='application/json')
    
    
    except Exception as err:
        # PrintGetExceptionDetails()
        print(f'exception: {str(err)}')
        logging.error("Exception in score_debug function.")
        return Response(json.dumps({"Execption in score_debug function: {}".format(err)}), status=500)

listen_thread = ListenThread(infer_cache)
listen_thread.start()

if __name__ == '__main__':
    # Running the file directly
    app.run(host='0.0.0.0', port=8888)