import os
import pandas as pd
import numpy as np
import re
import string
from scipy.sparse import csr_matrix, hstack
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn import svm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import MultinomialNB, GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
import nltk

nltk.download('stopwords')
nltk.download('punkt')


class TwitterSemanticModel():
    def load_dataset(self, filename):
        dataset = pd.read_csv(filename, encoding='latin-1')
        # dataset.columns = cols
        return dataset

    def remove_unwanted_cols(self, dataset, cols):
        for col in cols:
            del dataset[col]
        return dataset

    def preprocess_tweet_text(self, tweet):
        stop_words = set(stopwords.words('english'))
        tweet.lower()
        # Remove urls
        tweet = re.sub(r"http\S+|www\S+|https\S+", '', tweet, flags=re.MULTILINE)
        # Remove user @ references and '#' from tweet
        tweet = re.sub(r'\@\w+|\#', '', tweet)
        # Remove punctuations
        tweet = tweet.translate(str.maketrans('', '', string.punctuation))
        # Remove stopwords
        tweet_tokens = word_tokenize(tweet)
        filtered_words = [w for w in tweet_tokens if not w in stop_words]

        # ps = PorterStemmer()
        # stemmed_words = [ps.stem(w) for w in filtered_words]
        # lemmatizer = WordNetLemmatizer()
        # lemma_words = [lemmatizer.lemmatize(w, pos='a') for w in stemmed_words]

        return " ".join(filtered_words)

    def get_feature_vector(self, train_fit):
        vector = TfidfVectorizer(sublinear_tf=True)
        vector.fit(train_fit)
        return vector

    def amount_positive_negative(self, tweets):
        # Global Parameters
        stop_words = set(stopwords.words('english'))
        positive_words_txt = os.path.join('positive_words.txt')
        negative_words_txt = os.path.join('negative_words.txt')

        pos_words = []
        neg_words = []

        for pos_word in open(positive_words_txt, 'r').readlines():
            # pos_words.append(({pos_word.rstrip(): True}, 'positive'))
            pos_words.append(pos_word.rstrip())

        for neg_word in open(negative_words_txt, 'r').readlines():
            # neg_words.append(({neg_word.rstrip(): True}, 'negative'))
            neg_words.append(neg_word.rstrip())

        a = []
        positives = []
        negatives = []
        for tweet in tweets:
            words = tweet.split()
            positive_counter, negative_counter = 0, 0
            for word in words:
                if word in pos_words:
                    positive_counter += 1
                if word in neg_words:
                    negative_counter += 1
            positives.append(positive_counter)
            negatives.append(negative_counter)
        a.append(positives)
        a.append(negatives)
        return csr_matrix(a).transpose()

    def int_to_string(self, sentiment):
        if sentiment == 0:
            return "Negative"
        elif sentiment == 2:
            return "Neutral"
        else:
            return "Positive"

    def get_tweet_features_by_TfidfVectorizer(self, dataset, tf_vector):
        X = tf_vector.transform(np.array(dataset.iloc[:, 1]).ravel())
        return X

    def cross_validation(self, X_train, Y_train, scoring):
        models = []
        models.append(("LR", LogisticRegression(solver='lbfgs')))
        # models.append(("KNN", KNeighborsClassifier()))
        # models.append(("NB", GaussianNB()))
        # models.append(("NB", MultinomialNB()))
        # models.append(("SVM", svm.SVC()))
        results = []
        names = []
        for name, model in models:
            cv_results = cross_val_score(model, X_train, Y_train, cv=10, scoring=scoring)
            results.append(cv_results)
            names.append(name)
            msg = f"{name}, {cv_results.mean()}, {cv_results.std()}"
            print(msg)
        return results, models

    def fit_predict_model(self, model, X_train, y_train, X_test):
        model.fit(X_train, y_train)
        y_predict = model.predict(X_test)
        return y_predict

    def combine_features(self, X, other_features):
        # other_feature shoul be a list
        combined_features = X.copy()
        for feature in other_features:
            other_feature = csr_matrix(feature).transpose()
            combined_features = hstack(combined_features, other_feature)
        return combined_features



if __name__ == '__main__':
    TSM = TwitterSemanticModel()
    # Load dataset
    dataset = TSM.load_dataset("Train.csv")
    # Preprocess data
    dataset.SentimentText = dataset['SentimentText'].apply(TSM.preprocess_tweet_text)
    # Same tf vector will be used for Testing sentiments on unseen trending data
    tf_vector = TSM.get_feature_vector(np.array(dataset.iloc[:, 1]).ravel())
    X = TSM.get_tweet_features_by_TfidfVectorizer(dataset, tf_vector)

    other_features = []
    # TODO: add to combine_features more features
    # X = TSM.combine_features(X, other_features)

    y = np.array(dataset.iloc[:, 0]).ravel()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=30)
    ##########CROSS VALIDATION################
    # cross_val_results, models = TSM.cross_validation(X_train, y_train, scoring='accuracy')
    #########TRAINING MODEL####################
    model = LogisticRegression(solver='lbfgs')  # choose model
    y_predict = TSM.fit_predict_model(model, X_train, y_train, X_test)
    ########GET ACCURACY SCORE################
    print(accuracy_score(y_test, y_predict))

    ###############GET TEST PREDICT RESULTS FOR KAGGEL CHALLANGE###################
    # Load dataset
    test_file_name = "Test.csv"
    test_ds = TSM.load_dataset(test_file_name)
    # Preprocess data
    test_ds.SentimentText = test_ds['SentimentText'].apply(TSM.preprocess_tweet_text)

    X = TSM.get_tweet_features_by_TfidfVectorizer(test_ds, tf_vector)
    other_features = []
    # TODO: add to combine_features more features
    # X = TSM.combine_features(X, other_features)

    y_predict = model.predict(X)
    # save results
    test_result_ds = pd.DataFrame({'ID': test_ds["ID"], 'Sentiment': y_predict})
    test_result_ds.to_csv('real_sample.csv', index=False)

##############################################################################
# # Training Naive Bayes model
# NB_model = MultinomialNB()
# NB_model.fit(X_train, y_train)
# y_predict_nb = NB_model.predict(X_test)
# print(accuracy_score(y_test, y_predict_nb))
#
# # Training Logistics Regression model
# LR_model = LogisticRegression(solver='lbfgs')
# LR_model.fit(X_train, y_train)
# y_predict_lr = LR_model.predict(X_test)
# print(accuracy_score(y_test, y_predict_lr))

########################################################################################

# test_file_name = "Train.csv"
# test_ds = load_dataset(test_file_name)
#
# # Creating text feature
# test_ds.SentimentText = test_ds["SentimentText"].apply(preprocess_tweet_text)
# test_feature = tf_vector.transform(np.array(test_ds.iloc[:, 1]).ravel())
# # test_feature = hstack(test_feature, feature_1)
#
# # Using Logistic Regression model for prediction
# test_prediction_lr = LR_model.predict(test_feature)
# # numpy.savetxt("real_sample.csv", test_prediction_lr, delimiter=",")
# test_result_ds = pd.DataFrame({'real': test_ds["Sentiment"], 'prediction': test_prediction_lr})
#
# print(test_result_ds)
# print(accuracy_score(test_result_ds['real'], test_result_ds['prediction']))

########################################################################################
