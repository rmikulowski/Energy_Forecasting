import pandas as pd 
import numpy as np 
import os 
import pickle as pkl 

def prepare_data(raw_data):

    """
    This function is preparing the raw_data ("Data1.xlsx") to be changed to pickle, if loaded for the first time.
    To use it, put the file called as above in folder "data" -> "raw".
    Pickle file should be in folder "data" -> "cleaned".
    """
    print("Trying to load data from cache...")    

    try: # try loading the processed data
        
        # Change 'Data1' to name used in the raw_data!
        gas_data = pkl.load(open(os.getcwd() +"\\data\\cleaned\\" + "Data1" + "_import_cleaned.pkl","rb"))
        print("Loaded data from cache.")
        print("Here are the names of the worksheets:")
        print(*list(gas_data.keys()))

    except: # if the file doesn't exist then we need to process it
        # Takes raw data and transforms it by cleaning the transition and collection loans.
        # Also saves the output in /data/cleaned as a pickle file that can directly be loaded.
        print("Unable to load from cache, loading from raw file and starting preprocessing. Might take some time...")

        gas_data_raw = pd.ExcelFile(raw_data)

        # reading all sheets to a map 
        gas_data = {}
        for sheet_name in gas_data_raw.sheet_names:
            gas_data[sheet_name] = gas_data_raw.parse(sheet_name)

        # Printing the names of worksheets for analyst further purposes
        print("Here are the names of the worksheets:")
        print(*list(gas_data.keys()))
        print("Saved data from the worksheets to the defined file.")

        # Change 'Data1' to name used in the raw_data!
        output = open(os.getcwd() +"\\data\\cleaned\\" + "Data1" + "_import_cleaned.pkl","wb")
        pkl.dump(gas_data,output)


    return gas_data