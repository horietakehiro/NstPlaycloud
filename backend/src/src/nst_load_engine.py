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

from NstEngine.src.nst_utils import retreive_cmd_option4load_engine, load_config

import tensorflow as tf

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

def prepare_logdir(options):
    logdir = os.path.join(options['log'], options['t_path'].split('.')[0])
    if os.path.exists(logdir):
        shutil.rmtree(logdir)
    return logdir
        

def load_engine(content, style, options, config):

    engine = tf.saved_model.load(options['m_path'])
    fit = engine.signatures["serving_default"]

    if options['log']:
        logdir = prepare_logdir(options)
        image_writer = tf.summary.create_file_writer(logdir)
        loss_writer = tf.summary.create_file_writer(logdir)

    transfer = deepcopy(content)
    transfer = tf.constant(transfer)
    content = tf.constant(content)
    style = tf.constant(style)
    for step in tqdm.tqdm(range(int(options['step']))):

        # transfer, loss = fit(content=transfer, style=style, content_org=content)
        outputs = fit(content=transfer, style=style, content_org=content)
        transfer, loss = outputs['output_0'], outputs['output_1'][0]
        if options['log']:
            with image_writer.as_default():
                tf.summary.image(options['t_path'], transfer, step+1)
            with loss_writer.as_default():
                tf.summary.scalar('loss', loss, step+1)
        transfer = tf.constant(transfer)

    return transfer.numpy()

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

    options = retreive_cmd_option4load_engine(args[1:])
    options['t_path'] = create_path4transfer(options)
    print('===== Retreived commnad line options =====')
    for k, v in options.items():
        print(f'{k} : {v}')
    print('========================================')

    config = load_config(options['config'], 'engine')
    print('===== Retreived config file =====')
    for k, v in config.items():
        print(f'{k} : {v}')
    print('=================================')


    print('===== Preprocess content image =====')
    content = preprocess_image(options['c_path'], options['c_size'])
    print('====================================')

    print('===== Preprocess style image =====')
    style = preprocess_image(options['s_path'], options['s_size'])
    print('==================================')

    transfer = load_engine(content, style, options, config)

    print('===== Postprocess transfer image =====')
    transfer = postprocess(transfer, options)
    print('======================================')
    save_image(transfer, options)

    print('===== Finish =====')

    return 


if __name__ == '__main__':
    main(sys.argv)

