import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler



from tensorflow.keras.initializers import GlorotUniform


print(tf.__version__)
import h5py

# Load the model file
with h5py.File('MLP_11agosto.h5', 'r') as f:
    # Check TensorFlow version
    tensorflow_version = f.attrs.get('tensorflow_version')
    print("TensorFlow version used for saving the model:", tensorflow_version)
    keras_version = f.attrs.get('keras_version')
    print("Keras version used for saving the model:", keras_version)

class CustomGlorotUniform(tf.keras.initializers.Initializer):
    def __init__(self, seed=None):
        self.seed = seed

    def __call__(self, shape, dtype=None):
        return tf.keras.initializers.glorot_uniform(seed=self.seed)(shape)

    def get_config(self):
        return {"seed": self.seed}

# Usage:
custom_objects = {"CustomGlorotUniform": CustomGlorotUniform}
loaded_model = tf.keras.models.load_model('MLP_11agosto.h5', custom_objects=custom_objects)



config = tf.compat.v1.ConfigProto()
config.gpu_options.allow_growth = True
sess = tf.compat.v1.Session(config=config)

# Load the model with explicit initializer
custom_objects = {'GlorotUniform': GlorotUniform}
#classifierLoad = tf.keras.models.load_model('MLP_11agosto.h5', compile=True, custom_objects=custom_objects)
classifierLoad = tf.compat.v1.keras.models.load_model('MLP_11agosto.h5',  custom_objects=custom_objects)




# Scale the data if needed
scaler = StandardScaler()
fields_scaled = scaler.fit_transform([1,1,1,1,1,0,0,1,1,1])

# Predict using the classifier
y = classifierLoad.predict(fields_scaled)
print(y)
