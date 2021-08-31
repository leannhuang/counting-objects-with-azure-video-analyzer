# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import threading
from datetime import datetime
from azure.iot.device import IoTHubModuleClient
import json
import logging

class ListenThread(threading.Thread):
    def __init__(self, infer_cache):
        super().__init__()
        self.infer_cache = infer_cache
        self.daemon = True
        self.module_client = IoTHubModuleClient.create_from_edge_environment()
        
    def run(self):
        while True:
            try:
                input_message = self.module_client.receive_message_on_input('input1')  # blocking call
                if input_message.data:
                    now = datetime.now()
                    print("--------inference collector thread--------")
                    print(f'{now} The data in the message received on azureeyemodule was {input_message.data}')
                    print(f'{now} Custom properties are {input_message.custom_properties}')

                    # Gather inferences from azureeyemodule to correspond with when AVA is sending data
                    # NB:  AVA is still sending images, but we are ignoring them
                    inference_list = json.loads(input_message.data)['NEURAL_NETWORK']
                    if isinstance(inference_list, list):
                        for item in inference_list:
                            xmin, ymin, xmax, ymax = [float(x) for x in item['bbox']]
                            ts = int(item['timestamp'])
                            json_data = {
                                'type': 'entity',
                                'entity' : {
                                    'tag' : {
                                        'value' : item['label'],
                                        'confidence': float(item['confidence'])
                                    },
                                    'box': {
                                        'l': xmin,
                                        't': ymin,
                                        'w': xmax-xmin,
                                        'h': ymax-ymin
                                    }
                                }
                            }
                            self.infer_cache.append(ts, json_data)

            except Exception as err:
                # PrintGetExceptionDetails()
                print(f'exception: {str(err)}')
                logging.error("thread error")

