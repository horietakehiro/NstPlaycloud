
import tensorflow as tf


class NstEngine(tf.Module):

    def __init__(self, height, width, config):
        self.epoch = int(config['epoch'])
        self.content_layers = eval(config['content_layers'])
        self.style_layers = eval(config['style_layers'])

        self.content_image = tf.Variable(
            tf.zeros((1,height, width ,3)), 
            dtype=tf.float32
        )
        self.style_image = None
        vgg = tf.keras.applications.VGG19(include_top=False, weights='imagenet') 
        outputs = [vgg.get_layer(target_layer).output for target_layer in self.content_layers + self.style_layers]
        self.model = tf.keras.Model([vgg.input], outputs)
        self.model.trainable = False
        self.content_image_org = None
        self.style_image_org = None
        self.content_target = None
        self.style_target = None

        self.learning_rate = eval(config['learning_rate'])
        self.beta_1 = eval(config['beta_1'])
        self.epsilon = eval(config['epsilon'])
        self.optimizer = tf.keras.optimizers.Adam(
            learning_rate=self.learning_rate,
            beta_1=self.beta_1,
            epsilon=self.epsilon,
        )

        self.content_weights = eval(config['content_weights'])
        self.style_weights = eval(config['style_weights'])
        self.total_variation_weights = eval(config['total_variation_weights'])

        self.loss = tf.Variable(tf.zeros((1)), dtype=tf.float32)

    @tf.function(
        input_signature=(
            tf.TensorSpec(shape=[None, None, None, None], dtype=tf.float32),
            tf.TensorSpec(shape=[None, None, None, None], dtype=tf.float32),
            tf.TensorSpec(shape=[None, None, None, None], dtype=tf.float32),
        )
    )
    def fit(self, content, style, content_org):

        self.content_image_org = content_org
        self.style_image_org = style
        self.content_image.assign(content)
        self.style_image = style

        self.content_target = self.call(self.content_image_org)['content']
        self.style_target = self.call(self.style_image_org)['style']

        for e in range(self.epoch):
            loss = self.step()
        self.loss.assign([loss])
        return self.content_image, self.loss
    
    @tf.function
    def step(self):
        with tf.GradientTape() as tape:
            outputs = self.call(self.content_image)
            loss = self._calc_style_content_loss(outputs)
            loss += self.total_variation_weights*self._total_variation_loss()
        grad = tape.gradient(loss, self.content_image)
        self.optimizer.apply_gradients(
            [(grad, self.content_image)])
        self.content_image.assign(self._clip_0_1())
        return loss

    def _calc_style_content_loss(self, outputs):
        style_outputs = outputs['style']
        content_outputs = outputs['content']
        style_loss = tf.add_n([tf.reduce_mean((style_outputs[name]-self.style_target[name])**2)
                               for name in style_outputs.keys()])
        style_loss *= self.style_weights / len(self.style_layers)
        content_loss = tf.add_n([tf.reduce_mean((content_outputs[name]-self.content_target[name])**2)
                                 for name in content_outputs.keys()])
        content_loss *= self.content_weights / len(self.content_layers)
        loss = style_loss + content_loss
        return loss

    def _total_variation_loss(self):
        x_deltas, y_deltas = self._high_pass_x_y()
        return tf.reduce_sum(tf.abs(x_deltas)) + tf.reduce_sum(tf.abs(y_deltas))

    def _clip_0_1(self):
        return tf.clip_by_value(self.content_image,
                                clip_value_min=0.0, clip_value_max=1.0)

    def _high_pass_x_y(self):
        x_var = self.content_image[:, :, 1:, :] - self.content_image[:, :, :-1, :]
        y_var = self.content_image[:, 1:, :, :] - self.content_image[:, :-1, :, :]
        return x_var, y_var


    def call(self, input_image):
        input_image = input_image * 255.
        image = tf.keras.applications.vgg19.preprocess_input(input_image)
        outputs = self.model(image)
        
        content_outputs = outputs[:len(self.content_layers)]
        style_outputs = outputs[len(self.content_layers):]

        style_matrix = self._calc_gram_matrix(style_outputs)

        # gather all outputs into a dictionary
        style_dict = {name: output for name, output in zip(
            self.style_layers, style_matrix)}
        content_dict = {name: output for name, output in zip(
            self.content_layers, content_outputs)}

        return {'style': style_dict, 'content': content_dict}

    def _calc_gram_matrix(self, input_tensors):
        results = []
        for input_tensor in input_tensors:
            result = tf.linalg.einsum('bijc,bijd->bcd', input_tensor, input_tensor)
            input_shape = tf.shape(input_tensor)
            num_locations = tf.cast(input_shape[1]*input_shape[2], tf.float32)
            results.append(result / num_locations)
        return results
