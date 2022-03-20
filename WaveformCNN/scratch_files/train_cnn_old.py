import tensorflow as tf


def train_cat_cnn(data, output_dim):
    model = define_cnn.CnnCategorizer(output_dim,data)
    model_vars = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES)
    loss = loss_function(model, data)
    opt = tf.train.AdamOptimizer(
        learning_rate=2e-4,
        beta1=0.5)
    #From Donahue - "create training ops" - what does that mean?
    train_op = opt.minimize(loss, global_step = tf.train.get_or_create_global_step())



def loss_function(pred_model, gold):
    return tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=pred_model,labels=gold))