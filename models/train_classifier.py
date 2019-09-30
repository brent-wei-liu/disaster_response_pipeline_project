import sys
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

import warnings
warnings.simplefilter('ignore')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
import re
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, make_scorer
import pickle


def load_data(database_filepath):
    """Load and merge messages and categories datasets
    
    Args:
    database_filename: string. Filename for SQLite database containing cleaned message data.
       
    Returns:
    X: dataframe. Dataframe containing features dataset.
    Y: dataframe. Dataframe containing labels dataset.
    category_names: list of strings. List containing category names.
    """
    # load data from database
    engine = create_engine('sqlite:///%s' % database_filepath)
    df = pd.read_sql_table(database_filepath, engine)

    # Create X and Y datasets
    X = df['message']
    Y = df.drop(['message', 'original', 'genre'], axis = 1)

    # Create sierial containing all category names
    category_names = Y.columns
    return X, Y, category_names

def tokenize(text):
    """Normalize, tokenize and stem text string
    
    Args:
    text: string. String containing message for processing
       
    Returns:
    stemmed: list of strings. List containing normalized and stemmed word tokens
    """
    # Convert text to lowercase and remove punctuation
    text = re.sub(r"[^a-zA-Z0-9]", " ", text.lower())
    
    # Tokenize words
    tokens = word_tokenize(text)
    
    # Stem word tokens and remove stop words
    stemmer = PorterStemmer()
    stop_words = stopwords.words("english")
    stemmed = [stemmer.stem(word) for word in tokens if word not in stop_words]
    
    return stemmed


def build_model():
    """Build a machine learning pipeline
    
    Args:
    None
       
    Returns:
    pipeline: the machine learning pipeline
    """
    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer = tokenize, min_df=1)),
        ('tfidf', TfidfTransformer(use_idf=False)),
        ('clf', MultiOutputClassifier(LogisticRegression(solver='liblinear', penalty='l1', C=10))),
    ])

    return pipeline

def get_eval_metrics(actual, predicted, col_names):
    """Calculate evaluation metrics for ML model
    
    Args:
    actual: array. Array containing actual labels.
    predicted: array. Array containing predicted labels.
    col_names: list of strings. List containing names for each of the predicted fields.
       
    Returns:
    metrics_df: dataframe. Dataframe containing the accuracy, precision, recall 
    and f1 score for a given set of actual and predicted labels.
    """
    metrics = []
    
    # Calculate evaluation metrics for each set of labels
    for i in range(len(col_names)):
        accuracy = accuracy_score(actual[:, i], predicted[:, i])
        precision = precision_score(actual[:, i], predicted[:, i])
        recall = recall_score(actual[:, i], predicted[:, i])
        f1 = f1_score(actual[:, i], predicted[:, i])
        metrics.append([accuracy, precision, recall, f1])
    
    # Create dataframe containing metrics
    metrics = np.array(metrics)
    metrics_df = pd.DataFrame(data = metrics, index = col_names, columns = ['Accuracy', 'Precision', 'Recall', 'F1'])
      
    return metrics_df

def evaluate_model(model, X_test, Y_test, col_names):
    """Returns test accuracy, precision, recall and F1 score for fitted model
    
    Args:
    model: model object. Fitted model object.
    X_test: dataframe. Dataframe containing test features dataset.
    Y_test: dataframe. Dataframe containing test labels dataset.
    col_names: list of strings. List containing column names.
    
    Returns:
    None
    """
    # Calculate evaluation metrics for test set
    Y_test_pred = model.predict(X_test)
    eval_metrics = get_eval_metrics(np.array(Y_test), Y_test_pred, col_names)
    print(eval_metrics)

    # Get summary stats for model
    print(eval_metrics.describe())
    

def save_model(model, model_filepath):
    """Pickle fitted model
    
    Args:
    model: model object. Fitted model object.
    model_filepath: string. Filepath for where fitted model should be saved
    
    Returns:
    None
    """
    pickle.dump(model, open(model_filepath, 'wb'))


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()
