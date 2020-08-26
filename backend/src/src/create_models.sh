#!/bin/bash

python -c "import tensorflow as tf; \
            print('tensorflow version : ', tf.__version__); \
            print('Available GPU : ', tf.config.list_physical_devices('GPU'))"

# square
python nst_create_savedmodel.py \
    --ed ../models/ \
    --version 1 \
    --model nst_engine_square \
    --cs 512 512 \
    --ss 512 512 \
    --config ../config/config.ini

# wide
python nst_create_savedmodel.py \
    --ed ../models/ \
    --version 1 \
    --model nst_engine_wide \
    --cs 448 576 \
    --ss 448 576 \
    --config ../config/config.ini

# tall
python nst_create_savedmodel.py \
    --ed ../models/ \
    --version 1 \
    --model nst_engine_tall \
    --cs 576 448 \
    --ss 576 448 \
    --config ../config/config.ini


# superwide
python nst_create_savedmodel.py \
    --ed ../models/ \
    --version 1 \
    --model nst_engine_superwide \
    --cs 384 640 \
    --ss 384 640 \
    --config ../config/config.ini

# supertall
python nst_create_savedmodel.py \
    --ed ../models/ \
    --version 1 \
    --model nst_engine_supertall \
    --cs 640 384 \
    --ss 640 384 \
    --config ../config/config.ini
