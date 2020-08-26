import os
# suppress tesnsorflow logging down to DEBBUG
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import configparser
import argparse
from PIL import Image
import sys
import tqdm
import numpy as np
from copy import deepcopy
import shutil
import json
import requests

from NstEngine.src.nst_utils import retreive_cmd_option4request_engine, automatically_decide_image_size, IMAGE_SIZE_CHOICES


def detect_modelname(options):
    size = options['c_size']
    for k, v in IMAGE_SIZE_CHOICES.items():
        if v['size'] == size:
            options['modelname'] = f'nst_engine_{k}'
            return options


def preprocess_image(path, size):
    image = Image.open(path)
    image = image.convert('RGB')
    print(f'original image height/width : {image.height}/{image.width}')
    image = image.resize(tuple(size[::-1]))
    print(f'resized image height/width : {image.height}/{image.width}')

    image = np.array(image, dtype='f')
    image = image / 255.
    image = image[np.newaxis, ]
    print(f'image array dtype/shape/min/max : {image.dtype}/{image.shape}/{image.min()}/{image.max()}')
    return image
    
def create_path4transfer(options):
    t_path = f'{os.path.basename(options["c_path"]).split(".")[0]}' + \
            '_' + \
            f'{str(options["c_size"][0])}_{str(options["c_size"][1])}' + \
            '_' + \
            f'{os.path.basename(options["s_path"]).split(".")[0]}' + \
            '_' + \
            f'{str(options["s_size"][0])}_{str(options["s_size"][1])}' + \
            '_' + \
            f'step_{int(options["step"])}.png'
    return t_path


def request_engine(content, style, options):

    transfer = deepcopy(content)

    print('transfer' ,transfer.shape)
    print('style' ,style.shape)
    print('cote' ,content.shape)


    transfer = transfer[0,:,:,:].tolist()
    content = content[0,:,:,:].tolist()
    style = style[0,:,:,:].tolist()

    headers = {"content-type": "application/json"}
    rest_api = f'http://{options["addr"]}:{options["port"]}/' + \
                f'v1/models/{options["modelname"]}/versions/{options["version"]}:predict'


    for step in tqdm.tqdm(range(int(options['step']))):
        data = json.dumps(
            {
                "signature_name": "serving_default",
                "instances" : [
                    {
                        "content" : transfer,
                        "style" : style,
                        "content_org" : content
                    }
                ]
            }
        )
        response = requests.post(
            rest_api,
            data=data,
            headers=headers
        )
        json_response = json.loads(response.text)
        if 'predictions' in json_response.keys():
            transfer = json_response['predictions'][0]['output_0']

    transfer = np.array(transfer, dtype='f')[np.newaxis, ]
    return transfer

        
def postprocess(image, options):
    print(f'image array dtype/shape/min/max : {image.dtype}/{image.shape}/{image.min()}/{image.max()}')
    image = image[0,:,:,:]
    image = image * 255.
    image = image.astype(np.uint8)
    image = Image.fromarray(image,mode='RGB')
    print(f'original image height/width : {image.height}/{image.width}')
    
    return image

def save_image(image, options):
    path = os.path.join(os.path.dirname(options['c_path']), options['t_path'])
    image.save(path)
    return 


def main(args=None):

    print('===== Start =====')

    options = retreive_cmd_option4request_engine(args[1:])
    print('===== Automatiaclly decide image size =====')
    options = automatically_decide_image_size(options)
    print('===========================================')
    options = detect_modelname(options)
    if not options['t_path']:
        options['t_path'] = create_path4transfer(options)

    print('===== Retreived commnad line options =====')
    for k, v in options.items():
        print(f'{k} : {v}')
    print('========================================')

    print('===== Preprocess content image =====')
    content = preprocess_image(options['c_path'], options['c_size'])
    print('====================================')

    print('===== Preprocess style image =====')
    style = preprocess_image(options['s_path'], options['s_size'])
    print('==================================')

    transfer = request_engine(content, style, options)

    print('===== Postprocess transfer image =====')
    transfer = postprocess(transfer, options)
    print('======================================')
    save_image(transfer, options)

    print('===== Finish =====')

    return 


if __name__ == '__main__':
    main(sys.argv)

