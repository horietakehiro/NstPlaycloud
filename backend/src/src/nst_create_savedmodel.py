import os
# suppress tesnsorflow logging down to DEBBUG
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


import tensorflow as tf
import sys
import argparse
import configparser
import shutil

from NstEngine.src.nst_engine import NstEngine
from NstEngine.src.nst_utils import retreive_cmd_option4create_savedmodel, load_config

def prepare_export_dir(options):
    export_dir = os.path.join(
        options['export_dir'],
        options['model'],
        str(options['version']),
    )
    if os.path.exists(export_dir):
        shutil.rmtree(export_dir)
    os.makedirs(export_dir)

    return export_dir

    

def create_savedmodel(options, config):
    
    export_dir = prepare_export_dir(options)
    c_h, c_w = options['c_size']
    s_h, s_w = options['s_size']

    engine = NstEngine(
        height=c_h,
        width=c_w,
        config=config,
    )

    # make vgg extractor concrete
    _ = engine.call(
        tf.zeros((1,c_h, c_w, 3), dtype=tf.float32,)
    )
    fit = engine.fit.get_concrete_function(
        tf.TensorSpec([1,c_h, c_w, 3], tf.float32),
        tf.TensorSpec([1,s_h, s_w, 3], tf.float32),
        tf.TensorSpec([1,c_h, c_w, 3], tf.float32),
    )

    tf.saved_model.save(
        obj=engine, 
        export_dir=export_dir,
        signatures=fit
    )

    print(f'===== SavedModel is saved in : {export_dir} =====')

    return 



if __name__ == '__main__':
    print('===== Start =====')
    options = retreive_cmd_option4create_savedmodel(sys.argv[1:])
    print('===== Retreived commnad line options =====')
    for k, v in options.items():
        print(f'{k} : {v}')
    print('========================================')

    config = load_config(options['config'], 'engine')
    print('===== Retreived config file =====')
    for k, v in config.items():
        print(f'{k} : {v}')
    print('=================================')

    print('===== Create saved model =====')
    create_savedmodel(options, config)
    print('==============================')


    print('===== Finish =====')
