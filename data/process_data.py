import sys
import pandas as pd
import numpy as np
from collections import defaultdict
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from sqlalchemy import create_engine

def load_data(messages_filepath, categories_filepath):
    """Load and merge messages and categories datasets
    
    Args:
    messages_filepath: string. Filepath for csv file containing messages dataset.
    categories_filepath: string. Filepath for csv file containing categories dataset.
       
    Returns:
    df: dataframe. Dataframe containing merged content of messages and categories datasets.
    """
    # Load messages dataset
    messages = pd.read_csv(messages_filepath, index_col=0)

    # Load categories dataset
    categories = pd.read_csv(categories_filepath, index_col=0)

    # merge datasets
    df = messages.merge(categories, how = 'left', on = ['id'])
    return df

def clean_data(df):
    """Clean dataframe by removing duplicates and converting categories from strings 
    to binary values.
    
    Args:
    df: dataframe. Dataframe containing merged content of messages and categories datasets.
       
    Returns:
    df: dataframe. Dataframe containing cleaned version of input dataframe.
    """

    # Split `categories` into separate category columns.
    categories = df['categories'].str.split(';', expand=True)
    
    # Extract column names
    row = categories.iloc[0, ]
    category_colnames = row.apply(lambda x: x.split('-')[0]).tolist()
    categories.columns = category_colnames

    # Convert category values to just numbers 0 or 1.
    for column in categories:
        categories[column] = categories[column].apply(lambda x: x[-1])
        categories[column] = pd.to_numeric(categories[column])
    
    # Concatenate the original dataframe with the new `categories` dataframe
    df = pd.concat([df, categories], axis = 1)

    # Drop useless rows and columns
    df.drop('categories', axis = 1, inplace = True)
    df.drop('child_alone', axis = 1, inplace = True)
    df = df[df['related'] != 2]
    df.drop_duplicates(inplace=True)
    return df


def save_data(df, database_filename):
    """Save cleaned data into an SQLite database.
    
    Args:
    df: dataframe. Dataframe containing cleaned version of merged message and 
    categories data.
    database_filename: string. Filename for output database.
       
    Returns:
    None
    """
    engine = create_engine('sqlite:///%s' % database_filename)
    df.to_sql(database_filename, engine, index=False)  


def main():
    if len(sys.argv) == 4:

        messages_filepath, categories_filepath, database_filepath = sys.argv[1:]

        print('Loading data...\n    MESSAGES: {}\n    CATEGORIES: {}'
              .format(messages_filepath, categories_filepath))
        df = load_data(messages_filepath, categories_filepath)

        print('Cleaning data...')
        df = clean_data(df)
        
        print('Saving data...\n    DATABASE: {}'.format(database_filepath))
        save_data(df, database_filepath)
        
        print('Cleaned data saved to database!')
    
    else:
        print('Please provide the filepaths of the messages and categories '\
              'datasets as the first and second argument respectively, as '\
              'well as the filepath of the database to save the cleaned data '\
              'to as the third argument. \n\nExample: python process_data.py '\
              'disaster_messages.csv disaster_categories.csv '\
              'DisasterResponse.db')


if __name__ == '__main__':
    main()
