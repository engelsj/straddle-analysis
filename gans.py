import tensorflow as tf
import numpy as np
from training_data import *
import seaborn as sb
import matplotlib.pyplot as plt

sb.set()


def sample_Z(m, n):
    return np.random.uniform(-1., 1., size=[m, n])


def generator(Z, hsize=[16, 16], reuse=False):
    with tf.compat.v1.variable_scope("GAN/Generator", reuse=reuse):
        h1 = tf.compat.v1.layers.dense(Z, hsize[0], activation=tf.nn.leaky_relu)
        h2 = tf.compat.v1.layers.dense(h1, hsize[1], activation=tf.nn.leaky_relu)
        out = tf.compat.v1.layers.dense(h2, 2)

    return out


def discriminator(X, hsize=[16, 16], reuse=False):
    with tf.compat.v1.variable_scope("GAN/Discriminator", reuse=reuse):
        h1 = tf.compat.v1.layers.dense(X, hsize[0], activation=tf.nn.leaky_relu)
        h2 = tf.compat.v1.layers.dense(h1, hsize[1], activation=tf.nn.leaky_relu)
        h3 = tf.compat.v1.layers.dense(h2, 2)
        out = tf.compat.v1.layers.dense(h3, 1)

    return out, h3

tf.compat.v1.disable_eager_execution()
X = tf.compat.v1.placeholder(tf.float32, [None, 2])
Z = tf.compat.v1.placeholder(tf.float32, [None, 2])

G_sample = generator(Z)
r_logits, r_rep = discriminator(X)
f_logits, g_rep = discriminator(G_sample, reuse=True)

disc_loss = tf.reduce_mean(input_tensor=tf.nn.sigmoid_cross_entropy_with_logits(logits=r_logits, labels=tf.ones_like(
    r_logits)) + tf.nn.sigmoid_cross_entropy_with_logits(logits=f_logits, labels=tf.zeros_like(f_logits)))
gen_loss = tf.reduce_mean(input_tensor=tf.nn.sigmoid_cross_entropy_with_logits(logits=f_logits, labels=tf.ones_like(f_logits)))

gen_vars = tf.compat.v1.get_collection(tf.compat.v1.GraphKeys.GLOBAL_VARIABLES, scope="GAN/Generator")
disc_vars = tf.compat.v1.get_collection(tf.compat.v1.GraphKeys.GLOBAL_VARIABLES, scope="GAN/Discriminator")

gen_step = tf.compat.v1.train.RMSPropOptimizer(learning_rate=0.001).minimize(gen_loss, var_list=gen_vars)  # G Train step
disc_step = tf.compat.v1.train.RMSPropOptimizer(learning_rate=0.001).minimize(disc_loss, var_list=disc_vars)  # D Train step

sess = tf.compat.v1.Session()
tf.compat.v1.global_variables_initializer().run(session=sess)

batch_size = 254
nd_steps = 10
ng_steps = 10

x_plot = sample_data()

f = open('loss_logs.csv', 'w')
f.write('Iteration,Discriminator Loss,Generator Loss\n')

for i in range(8001):
    X_batch = sample_data()
    Z_batch = sample_Z(batch_size, 2)

    for _ in range(nd_steps):
        _, dloss = sess.run([disc_step, disc_loss], feed_dict={X: X_batch, Z: Z_batch})
    rrep_dstep, grep_dstep = sess.run([r_rep, g_rep], feed_dict={X: X_batch, Z: Z_batch})

    for _ in range(ng_steps):
        _,  gloss = sess.run([gen_step, gen_loss], feed_dict={Z: Z_batch})

    rrep_gstep, grep_gstep = sess.run([r_rep, g_rep], feed_dict={X: X_batch, Z: Z_batch})

    if i % 10 == 0:
        f.write("%d,%f,%f\n" % (i, dloss, gloss))

    if i % 1000 == 0:
        plt.figure()
        g_plot = sess.run(G_sample, feed_dict={Z: Z_batch})
        xax = plt.scatter(x_plot[:, 0], x_plot[:, 1])
        gax = plt.scatter(g_plot[:, 0], g_plot[:, 1])

        plt.legend((xax, gax), ("Real Data", "Generated Data"))
        plt.title('Samples at Iteration %d' % i)
        plt.tight_layout()
        plt.savefig('plots/iterations/iteration_%d.png'%i)
        plt.close()

        plt.figure()
        rrd = plt.scatter(rrep_dstep[:, 0], rrep_dstep[:, 1], alpha=0.5)
        rrg = plt.scatter(rrep_gstep[:, 0], rrep_gstep[:, 1], alpha=0.5)
        grd = plt.scatter(grep_dstep[:, 0], grep_dstep[:, 1], alpha=0.5)
        grg = plt.scatter(grep_gstep[:, 0], grep_gstep[:, 1], alpha=0.5)

        plt.legend((rrd, rrg, grd, grg), ("Real Data Before G step", "Real Data After G step",
                                          "Generated Data Before G step", "Generated Data After G step"))
        plt.title('Transformed Features at Iteration %d' % i)
        plt.tight_layout()
        plt.savefig('plots/features/feature_transform_%d.png' % i)
        plt.close()

        plt.figure()

        rrdc = plt.scatter(np.mean(rrep_dstep[:, 0]), np.mean(rrep_dstep[:, 1]), s=100, alpha=0.5)
        rrgc = plt.scatter(np.mean(rrep_gstep[:, 0]), np.mean(rrep_gstep[:, 1]), s=100, alpha=0.5)
        grdc = plt.scatter(np.mean(grep_dstep[:, 0]), np.mean(grep_dstep[:, 1]), s=100, alpha=0.5)
        grgc = plt.scatter(np.mean(grep_gstep[:, 0]), np.mean(grep_gstep[:, 1]), s=100, alpha=0.5)

        plt.legend((rrdc, rrgc, grdc, grgc), ("Real Data Before G step", "Real Data After G step",
                                              "Generated Data Before G step", "Generated Data After G step"))

        plt.title('Centroid of Transformed Features at Iteration %d' % i)
        plt.tight_layout()
        plt.savefig('plots/features/feature_transform_centroid_%d.png'%i)
        plt.close()

        plt.figure()
        log_returns_simulated = pd.DataFrame(g_plot[:, 1])
        log_returns_simulated = np.log(1 + log_returns_simulated.astype(float).pct_change())
        log_returns_simulated = log_returns_simulated.dropna()

        log_returns_actual = pd.DataFrame(X_batch[:, 1])
        log_returns_actual = np.log(1 + log_returns_actual.astype(float).pct_change())
        log_returns_actual = log_returns_actual.dropna()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 12))
        ax1.hist(log_returns_simulated.values, bins=50)
        ax1.set_xlabel('Theoretical Returns')
        ax1.set_ylabel('Frequency')
        ax2.hist(log_returns_actual.values, bins=50)
        ax2.set_xlabel('Observed Returns')
        ax2.set_ylabel('Frequency')
        plt.savefig('plots/iterations/hist_%d.png' % i)
        plt.close()

f.close()
