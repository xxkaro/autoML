import pandas as pd
from train import train
import os
from plots import makeplots
import pickle
import sys
import os
from project.preprocessing.preprocessing import Preprocessing

class medaid:
    allowed_models = ["logistic", "tree", "random_forest", "xgboost", "lightgbm"]
    allowed_metrics = [ "accuracy", "f1", "recall", "precision"] #TODO ktore metryki ?
    def __init__(self
                 , X
                 , y
                 , dataframe
                 , target_column
                 , mode = "perform"
                 , models = None
                 , metric = "f1"
                 , path = None
                 , search  = None
                 , cv = 3
                 , n_iter = 20
                 ):

        if type(X) is not pd.DataFrame:
            raise ValueError("X must be a pandas DataFrame")
        if type(y) is not pd.Series and type(y) is not pd.DataFrame:
            raise ValueError("y must be a pandas Series or DataFrame")
        if len(X) != len(y):
            raise ValueError("X and y must have the same number of rows")
        self.X = X
        self.y = y
        self.dataframe = dataframe

        if mode not in ["explain", "perform"]:
            raise ValueError("mode must be either 'explain' or 'perform'")
        self.mode = mode

        if models is not None:
            if type(models) is not list:
                raise ValueError("models must be a list")
            for model in models:
                if model not in self.allowed_models:
                    raise ValueError(f"model {model} is not allowed, must be one of {self.allowed_models}")
            self.models = models
        elif mode == "perform":
            self.models = self.allowed_models
        else:
            self.models = ["logistic", "tree"]


        if metric not in self.allowed_metrics:
            raise ValueError(f"metric {metric} is not allowed, must be one of {self.allowed_metrics}")
        self.metric = metric

        self.best_models_scores = None
        self.best_models = None
        self.best_metrics = None

        if path:
            self.path = path + "/medaid"
        else:
            self.path = os.path.dirname(os.path.abspath(__file__)) + "/medaid"
        
        self.target_column = target_column
        self.preprcessing = Preprocessing(target_column=self.target_column, output_file=f"{self.path}results/preprocessing_details.csv")

        if search:
            if search not in ["random", "grid"]:
                raise ValueError("search must be either 'random' or 'grid'")
            self.search = search
        else:
            self.search = "random" if mode == "explain" else "grid"

        if type(cv) is not int:
            raise ValueError("cv must be an integer")
        self.cv = cv
        if type(n_iter) is not int:
            raise ValueError("n_iter must be an integer")
        self.n_iter = n_iter

    def __repr__(self):
        # TODO: trzeba jakos ladnie zaprezentowac i guess - techniczna wizualizacja
        return f"medaid(X, y, mode = {self.mode})"

    def __str__(self):
        # TODO trzeba jakos ladnie zaprezentowac i guess - ladna wizualizacja
        str = "medaid object\n"
        str+=f"mode: {self.mode}\n"
        str+=f"metric: {self.metric}\n"
        if self.best_models is not None:
            str+="trained\n"
            str+="models; scores: \n"
            for i in range(len(self.best_models)):
                str+=f"\t- {self.best_models[i]}: {self.best_models_scores[i]}\n"
        else:
            str+="not trained\n"

        return str
    
    def preprocess(self, dataframe):
        return self.preprcessing.preprocess(dataframe)


    def train(self):
        df_processed = self.preprocess(self.dataframe)
        y = df_processed[self.target_column]
        X = df_processed.drop(columns=[self.target_column])
        best_models, best_models_scores, best_metrics= train(X, y, self.models, self.metric, self.mode, self.path, self.search, self.cv, self.n_iter)
        self.best_models = best_models
        self.best_models_scores = best_models_scores
        self.best_metrics = best_metrics
        makeplots(self.best_models, X, y, self.path)

    def predict(self, X):
        if self.best_models is None:
            raise ValueError("You need to train the model first")
        if type(X) is not pd.DataFrame:
            raise ValueError("X must be a pandas DataFrame")
        if len(X.columns) != len(self.X.columns):
            raise ValueError("X must have the same columns as the training data")
        return self.best_models[0].predict(X)

    def models_ranking(self):
        return self.best_metrics

    def report(self):
        # Ensure log.txt is created
        if not os.path.exists('log.txt'):
            open('log.txt', 'w').close()

        original_stdout = sys.stdout  # Save a reference to the original standard output
        with open('log.txt', 'w') as f:
            sys.stdout = f  # Change the standard output to the file we created.
            print("Generating report...")
            print(f"Best models: {self.best_models}")
            print(f"Best models scores: {self.best_models_scores}")
            print(f"Best metrics: {self.best_metrics}")
            print("the end")
            print("is working")
            print("is only working when started from terminal")
            sys.stdout = original_stdout  # Reset the standard output to its original value

    def save(self):
        with open(f"{self.path}/medaid.pkl", 'wb') as f:
            pickle.dump(self, f)

if __name__ == "__main__":
    # Example usage
    import pandas as pd

    data = pd.read_csv('../../data/binary/cardio_train.csv', sep=';')
    X = data.drop(columns=['cardio', 'id'])
    y = data['cardio']
    # Create an instance of medaid
    aid = medaid(X, y)

    # Train the model
    #aid.train()

    # Generate a report
    aid.report()