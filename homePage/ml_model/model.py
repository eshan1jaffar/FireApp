import dill as pickle
import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
import os
import firebase_admin
# from dill import settings
from firebase_admin import credentials, storage, db
from Cryptodome.Util.RFC1751 import binary
from django.conf import settings

# Path to the saved model file
key = os.path.join(settings.BASE_DIR, 'homePage/ml_model', settings.FIREBASE_JSON_KEY)
cred = credentials.Certificate(key)
firebase_admin.initialize_app(cred, {'storageBucket': settings.STORAGE_BUCKET,
                                     'databaseURL': settings.DATABASE_URL})
MODEL_PATH = os.path.join(settings.BASE_DIR, 'homePage/ml_model', 'detector.pkl')
WEIGHT_PATH = os.path.join(settings.BASE_DIR, 'homePage/ml_model', 'wildfire-classifier.weights.h5')
UNET_PATH = os.path.join(settings.BASE_DIR, 'homePage/ml_model', 'unet.keras')

class WildfireDetector:
    def __init__(self, unet_path, weights_path):
        self.unet_path = unet_path
        self.weights_path = weights_path
        self.model = None

    def create_model(self):
        unet = tf.keras.models.load_model(self.unet_path)
        mobilenet_model = tf.keras.models.Sequential()
        mobilenet_model.add(tf.keras.layers.Lambda(lambda x: x, input_shape=(256, 256, 3)))
        mobilenet_model.add(tf.keras.layers.Lambda(lambda x: tf.cast(unet(x) >= 0.85, tf.float32)))
        mobilenet_model.add(tf.keras.layers.Conv2D(3, (1, 1), padding='same', use_bias=False))
        pretrained_model = tf.keras.applications.MobileNetV2(include_top=False,
                                                             input_shape=(256, 256, 3),
                                                             pooling='avg',
                                                             weights='imagenet')
        for layer in pretrained_model.layers:
            layer.trainable = False

        mobilenet_model.add(pretrained_model)
        mobilenet_model.add(tf.keras.layers.Dense(1, activation='sigmoid'))
        mobilenet_model.load_weights(self.weights_path)
        mobilenet_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

        return mobilenet_model

    def overlay(self, image_path, alpha=0.15):
        alpha = 0.25
        img = tf.io.read_file(image_path)
        img = tf.image.decode_jpeg(img, channels=3)
        img = tf.image.resize(img, (256, 256))
        img = img / 255.0
        img = img.numpy()
        img = np.expand_dims(img, axis=0)

        mask = self.model.layers[1](img)[0]

        binary_mask = tf.cast(mask > 0.5, tf.float32)
        white_mask = tf.concat([tf.ones_like(binary_mask), tf.zeros_like(binary_mask), tf.zeros_like(binary_mask)],
                               axis=-1)
        red_background = tf.concat([tf.ones_like(binary_mask), tf.ones_like(binary_mask), tf.ones_like(binary_mask)],
                                   axis=-1)
        mask_rgb = white_mask * binary_mask + red_background * (1 - binary_mask)
        mask_rgb = tf.image.resize(mask_rgb, (256, 256))

        overlay = (1 - alpha) * img[0] + alpha * mask_rgb
        plt.imsave(os.path.join(settings.MEDIA_ROOT, 'images', 'overlay.jpg'), overlay.numpy())

        firebase_storage_path = 'images/overlay.jpg'
        bucket = storage.bucket()
        blob = bucket.blob(firebase_storage_path)
        blob.upload_from_filename(os.path.join(settings.MEDIA_ROOT, 'images', 'overlay.jpg'))
        blob.make_public()
        image_url = blob.generate_signed_url(version="v4", expiration=3600*24, method="GET")

        ref = db.reference('overlay')
        ref.update({
            'image_url': image_url
        })
        return

    def analyze_image(self, image_path):
        img = tf.io.read_file(image_path)
        img = tf.image.decode_png(img, channels=3)
        img = tf.image.resize(img, (256, 256))
        img = img / 255.0
        img = tf.expand_dims(img, axis=0)

        if self.model == None:
            self.model = self.create_model()

        self.overlay(image_path)
        return 1 if self.model.predict(img, verbose=0)[0] > 0.5 else 0, self.model.predict(img, verbose=0)[0]

def predict(img_path):
    detector = WildfireDetector(UNET_PATH, WEIGHT_PATH)
    return detector.analyze_image(img_path)