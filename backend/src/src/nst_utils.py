import configparser
import argparse
import os

from PIL import Image

IMAGE_SIZE_CHOICES={
    # [height, width]
    'square' : {'size' : [512, 512], 'ratio' : float(512) / float(512)},
    'tall' : {'size' : [512+64, 512-64], 'ratio' : float(512+64) / float(512-64)},
    'wide' : {'size' : [512-64, 512+64], 'ratio' : float(512-64) / float(512+64)},
    'supertall' : {'size' : [512+128, 512-128], 'ratio' : float(512+128) / float(512-128)},
    'superwide' : {'size' : [512-128, 512+128], 'ratio' : float(512-128) / float(512+128)},
}


def retreive_cmd_option4load_engine(args):
    """
    return command line options as dict
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--mp',
        required=True,
        dest='m_path',
        help='model path',
    )

    parser.add_argument(
        '--cp', 
        required=True, 
        dest='c_path', 
        help='content image path',
    )
    parser.add_argument(
        '--sp', 
        required=True, 
        dest='s_path', 
        help='style image path',
    )

    parser.add_argument(
        '--config', 
        required=True, 
        dest='config', 
        help='config file path',
    )

    parser.add_argument(
        '--auto',
        dest='auto',
        action='store_true',
        help='flag for automatically decide image size',
    )

    parser.add_argument(
        '--cs', 
        required=False, 
        dest='c_size', 
        type=int,
        nargs=2,
        default=[512, 512],
        help='content image size (h, w)',
    )
    parser.add_argument(
        '--ss', 
        required=False, 
        dest='s_size', 
        type=int,
        nargs=2,
        default=[512, 512],
        help='style image size (h, w)',
    )

    parser.add_argument(
        '--step', 
        required=False, 
        dest='step', 
        type=int,
        default=20,
        help='step',
    )

    parser.add_argument(
        '--log', 
        required=False, 
        dest='log',
        default='',
        help='logdir for tensorboard',
    )

    args = vars(parser.parse_args(args))
    return args


def retreive_cmd_option4call_engine(args):
    """
    return command line options as dict
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--cp', 
        required=True, 
        dest='c_path', 
        help='content image path',
    )
    parser.add_argument(
        '--sp', 
        required=True, 
        dest='s_path', 
        help='style image path',
    )

    parser.add_argument(
        '--config', 
        required=True, 
        dest='config', 
        help='config file path',
    )

    parser.add_argument(
        '--auto',
        dest='auto',
        action='store_true',
        help='flag for automatically decide image size',
    )

    parser.add_argument(
        '--cs', 
        required=False, 
        dest='c_size', 
        type=int,
        nargs=2,
        default=[512, 512],
        help='content image size (h, w)',
    )
    parser.add_argument(
        '--ss', 
        required=False, 
        dest='s_size', 
        type=int,
        nargs=2,
        default=[512, 512],
        help='style image size (h, w)',
    )

    parser.add_argument(
        '--step', 
        required=False, 
        dest='step', 
        type=int,
        default=20,
        help='step',
    )

    parser.add_argument(
        '--log', 
        required=False, 
        dest='log',
        default='',
        help='logdir for tensorboard',
    )

    args = vars(parser.parse_args(args))
    return args


def retreive_cmd_option4create_savedmodel(args):
    """
    return command line options as dict
    """
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        '--ed',
        required=True,
        dest='export_dir',
        help='base directory the model saved on',
    )

    parser.add_argument(
        '--model',
        required=True,
        dest='model',
        help='model name which saved as',
    )

    parser.add_argument(
        '--version',
        required=True,
        dest='version',
        type=int,
        help='model version which saved as',
    )

    parser.add_argument(
        '--config', 
        required=True, 
        dest='config', 
        help='config file path',
    )

    parser.add_argument(
        '--cs', 
        required=False, 
        dest='c_size', 
        type=int,
        nargs=2,
        default=[512, 512],
        help='content image size (h, w)',
    )
    parser.add_argument(
        '--ss', 
        required=False, 
        dest='s_size', 
        type=int,
        nargs=2,
        default=[512, 512],
        help='style image size (h, w)',
    )

    parser.add_argument(
        '--log', 
        required=False, 
        dest='log',
        default='',
        help='logdir for tensorboard',
    )

    args = vars(parser.parse_args(args))
    return args


def retreive_cmd_option4request_engine(args):
    """
    return command line options as dict
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--cp', 
        required=True, 
        dest='c_path', 
        help='content image path',
    )
    parser.add_argument(
        '--sp', 
        required=True, 
        dest='s_path', 
        help='style image path',
    )

    parser.add_argument(
        '--tp',
        dest='t_path',
        default='',
        required=False,
        help='transfer image path',
    )

    parser.add_argument(
        '--step', 
        required=False, 
        dest='step', 
        type=int,
        default=20,
        help='num steps of transfer',
    )

    parser.add_argument(
        '--version',
        required=False,
        dest='version',
        type=str,
        default='1',
        help='model version',
    )

    parser.add_argument(
        '--addr',
        dest='addr',
        required=False,
        default=os.environ.get('NST_ENGINE_ADDR', 'localhost'),
        help='nst_engine address',
    )
    parser.add_argument(
        '--port',
        dest='port',
        required=False,
        default=os.environ.get('NST_ENGINE_PORT', '8501'),
        help='nst_engine port',
    )

    args = vars(parser.parse_args(args))
    return args


def automatically_decide_image_size(options):
    # decide image size based on the original content image size
    image = Image.open(options['c_path'])
    width, height = image.size
    image.close()

    aspect_ratio = float(height) / float(width)
    # find the choice which have the least residual
    residuals = {
        k : abs(aspect_ratio - v['ratio']) 
        for k,v in IMAGE_SIZE_CHOICES.items()
    }
    residuals = sorted(residuals.items(), key=lambda item: item[1])
    choice = residuals[0][0]

    options['c_size'] = IMAGE_SIZE_CHOICES[choice]['size']
    options['s_size'] = IMAGE_SIZE_CHOICES[choice]['size']
    return options


def load_config(path, section):
    """
    return config loaded from file as dictionary
    """
    parser = configparser.ConfigParser()
    _ = parser.read(path)
    config = dict(parser.items(section))

    return config
