from Levenshtein import ratio, distance
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import re

def clean_column(df: pd.DataFrame, col:str)->pd.DataFrame:
    '''
    Function to consistently remove all punctuation and spaces from column of pandas dataframe.
    Takes dataframe and column name.
    Returns clean column.
    '''
    return (df[col].astype(str).str.replace(r'[\W_]+', '', regex=True).str.lower())

def same_name_merge(dataframe:pd.DataFrame, col:str, disp_col:str, cutoff=0.7) -> pd.DataFrame:
    '''
    Runs through dataframe to see and prompts user with similar enough names.
    If user decides they are same name, set all of the less used name to the other.

    Takes pandas dataframe, column name, and cutoff criteria (for the similarity ratio)

    Outputs dataframe
    
    '''
    
    df = dataframe.copy()
    
    
    # Nested for loops to run through every combination
    unique_obs = df[col].unique()
    for i in range(len(unique_obs)):
        for j in range(i, len(unique_obs)):
            # Skip identical names
            if not unique_obs[i] == unique_obs[j]: 
                # Test if names are similar enough for user to check
                if ratio(unique_obs[i], unique_obs[j], score_cutoff=cutoff)>0:
                    # print names for user
                    print(unique_obs[i], unique_obs[j])
                    # Take user input (1 is change)
                    inp = str(input()).strip()
                    # See if user want to set as same
                    if inp=='1':
                        # Get number of rows needed to switch
                        i_len = len(df[df[col]==unique_obs[i]])
                        j_len = len(df[df[col]==unique_obs[j]])
                        
                        # Switch less frequent to more frequent
                        if  j_len > i_len:
                            # Confirm switch for user
                            print(f'{unique_obs[i]} set to {unique_obs[j]}')

                            # Switch i to j
                            df.loc[df[col] == unique_obs[i], 
                            col] = [unique_obs[j]]*i_len
                            
                            df.loc[df[col] == unique_obs[i], 
                            disp_col] = df.loc[df[col] == unique_obs[j], disp_col].to_list()[0]*i_len
                            
                            # Set future i to j so that they skip (I guess not really necessary)
                            unique_obs[i] = unique_obs[j]
                        else:

                            # Switch j to i
                            df.loc[df[col] == unique_obs[j], 
                            col] = [unique_obs[i]]*j_len

                            df.loc[df[col] == unique_obs[j], 
                            disp_col] = df.loc[df[col] == unique_obs[i], disp_col].to_list()[0]*j_len
                            
                            # Set future j to i so that they skip
                            unique_obs[j] = unique_obs[i]
                            
    return df