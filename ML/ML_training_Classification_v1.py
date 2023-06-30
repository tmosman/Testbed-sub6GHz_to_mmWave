# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 16:10:09 2021

@author: osman
"""

import numpy as np # advanced math library 
import matplotlib.pyplot as plt # MATLAB like plotting routines 
import random # for generating random numbers 
import scipy.io as scs
#%% Machine learning Frameworks
import keras 
from keras.layers.core import Dense, Dropout, Activation # Types of layers to be used in our model from keras.utils import np_utils # NumPy related tools
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from keras.utils import np_utils
from tensorflow.keras import regularizers
from keras.models import Sequential
from keras.layers.normalization import layer_normalization
#from keras.layers import LayerNormalization
import tensorflow as tf
from sklearn.metrics import confusion_matrix
import seaborn as sns
#size_estimates = 512

for fx in range(1):
    ## Load Data
    X_complex, y_1 = np.load('./Datasets/Trainset_sub6_channels_all.npy'),np.load('./Datasets/Trainset_locs_all.npy') 
    Xun=np.hstack((np.real(X_complex), np.imag(X_complex)))
    #Xun = np.abs(X_complex)
    x_maxvalue=np.max(Xun)
    
    X_1=Xun/x_maxvalue;
    #X_1=X_1/np.linalg.norm(X_1, axis=1).reshape((-1, 1))
    # print(X.shape)
    # print(y.shape)
    
    ## Split Dataset to Test and Train
    X_train, _, y_train, _ = train_test_split(X_1, y_1, test_size=0.0001, random_state=11)
    print("X_train shape", X_train.shape)
    print("y_train shape", y_train.shape)
    
    X_complex, y_2 = np.load('./Datasets/testset_channels_1.npy'),np.load('./Datasets/testset_locs_1.npy') 
    Xun=np.hstack((np.real(X_complex), np.imag(X_complex)))
    #Xun = np.abs(X_complex)
    x_maxvalue=np.max(Xun)
    X_2=Xun/x_maxvalue;
    #X_2=X_2/np.linalg.norm(X_2, axis=1).reshape((-1, 1))
    # print(X.shape)
    # print(y.shape)
    
    ## Split Dataset to Test and Train
    _, X_test, _, y_test = train_test_split(X_2, y_2, test_size=0.999, random_state=11)
    print("X_test shape", X_test.shape)
    print("y_test shape", y_test.shape)

    ## Normalize Dataset 
    # sc = StandardScaler()
    # sc.fit(X_train)
    # X_train = sc.transform(X_train)
    # X_test = sc.transform(X_test)
    # Count number of Unique beams in the y data
    nb_classes_1 = np.max(y_1)+1 # number of unique digits
    nb_classes_1 = 21
    Y_train = np_utils.to_categorical(y_train, nb_classes_1) ## Get One hot vector for each beam
    
    nb_classes_2 = np.max(y_2)+1 # number of unique digits  
    nb_classes_2 = 21
    Y_test = np_utils.to_categorical(y_test,nb_classes_2)
    
    size_estimates=X_train.shape[1]
    ## Create FC- Model
    model = Sequential()
    
    #Input Layer
    model.add(Dense(128, input_shape=(size_estimates,))) 
    model.add(Activation('relu'))   #other option relu
    model.add(Dropout(0.1))
    
    model.add(Dense(128))
    model.add(Activation('relu'))
    model.add(Dropout(0.1))
  
    # model.add(Dense(128))
    # model.add(Activation('relu'))
    # model.add(Dropout(0.1))
    
    model.add(Dense(64))
    model.add(Activation('relu'))
    
    # Output Layer
    model.add(Dense(max(nb_classes_1,nb_classes_2),activation = 'softmax'))
    
 
    topk_metrics = [ keras.metrics.TopKCategoricalAccuracy(name='Top-%i'%k, k = k) for k in [2,5,10,20]]
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy',topk_metrics])
    
    history = model.fit(X_train, Y_train,batch_size=32, epochs=20, #128 to 60000
                        verbose=1, validation_data=(X_test, Y_test)
                        ,validation_split=0.2,shuffle=True
                        )
                                #callbacks = [keras.callbacks.ModelCheckpoint( './', monitor='val_loss', verbose=0, save_best_only=True, mode='auto')])
    
    score = model.evaluate(X_test, Y_test)
    print('Test score:', score[0])
    print('Test accuracy:', score[1])
    predicted_classes = np.argmax(model.predict(X_test),axis=1)#model.predict(X_test)
    print(predicted_classes.shape)
    #predicted_classes =p_list
    #top_k_values, top_k_indices = tf.nn.top_k(predicted_classes, k=1)
    
    
    
    #  print(top_k_indices.numpy())
    # beam_list=[6, 9, 11, 12, 13, 16, 20, 21, 22, 24, 25, 27, 30, 31, 35, 36, 39, 42, 43, 45, 46, 49, 50, 53]
    # y_random=[]  
    # for rand in range(X_test.shape[0]):
    #     y_random.append(list(random.sample(beam_list, 1)))
    # y_random=np.asarray(y_random)
    
    
    
    new_Y_test = np.argmax(Y_test,axis=1)
    print(predicted_classes.shape)
    print(new_Y_test.shape)
   
    # Check which items we got right / wrong
    # correct_indices = np.nonzero(predicted_classes == y_test)[0]
    # #print(correct_indices)
    # incorrect_indices = np.nonzero(predicted_classes != y_test)[0]
    
    # Make predictions
    #y_pred = model.predict(X_test)
    cm=tf.math.confusion_matrix(new_Y_test,predicted_classes)
    # Build confusion metrics
    #cm = confusion_matrix(y_true=Y_test, y_pred=predicted_classes)
    #print(cm)
    
    # Plot confusion matrix in a beautiful manner
    ax= plt.figure(1,figsize=(12, 8), dpi=100)
    ax= plt.subplot()
    sns.heatmap(cm, annot=True, ax = ax, fmt = 'g'); #annot=True to annotate cells
    # labels, title and ticks
    ax.set_xlabel('Predicted', fontsize=20)
    ax.xaxis.set_label_position('top') 
    #ax.xaxis.set_ticklabels(['ham', 'spam'], fontsize = 15)
    ax.xaxis.tick_top()
    
    ax.set_ylabel('True', fontsize=20)
    #ax.yaxis.set_ticklabels(['spam', 'ham'], fontsize = 15)
    #ax=plt.savefig("./Results_class/Exp"+str(fx)+"_cm")
    #ax=plt.clf()
    
''' 
# print(history.history.keys())
# #  "Accuracy"
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'validation'], loc='upper left')
plt.show()
# # "Loss"
# plt.plot(history.history['loss'])
# plt.plot(history.history['val_loss'])
# plt.title('model loss')
# plt.ylabel('loss')
# plt.xlabel('epoch')
# plt.legend(['train', 'validation'], loc='upper left')
# plt.show()
'''