import time

import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.tree import plot_tree
import matplotlib.pyplot as plt
from sklearn import tree
import graphviz
import dtreeviz
import os
import pandas as pd
import warnings
import sys
warnings.filterwarnings("ignore", category=UserWarning)
import seaborn as sns

def distribution_plots(aid):
        #create a folder for the plots
    df = aid.df_before
    X = df.drop(columns=[aid.target_column])
    y = df[aid.target_column]
    path = aid.path
    if not os.path.exists(f"{path}/distribution_plots"):
        os.makedirs(f"{path}/distribution_plots")

    #generate count plots for each feature not using sns
    for col in X.columns:
        #if more that 10 unique values make a histogram
        if len(X[col].unique()) > 10:
            plt.figure()
            X[col].hist()
            plt.title(f'{col} distribution')
            plt.savefig(f"{path}/distribution_plots/{col}_hist.png")
            plt.clf()
        else:
            #make countplots but sort the values on the x axis
            plt.figure()
            X[col].value_counts().sort_index().plot(kind='bar')
            plt.title(f'{col} distribution')
            plt.savefig(f"{path}/distribution_plots/{col}_count.png")
            plt.clf()

    return None

def correlation_plot(aid):
    #create a folder for the plots
    path = aid.path
    X = aid.X
    y = aid.y
    if not os.path.exists(f"{path}/correlation_plots"):
        os.makedirs(f"{path}/correlation_plots")

    corr = X.corr()
    #plot the correlation matrix the scale should be from -1 to 1
    plt.figure(figsize=(10, 10))
    sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('Correlation matrix')
    plt.savefig(f"{path}/correlation_plots/correlation_matrix.png")
    plt.clf()

    #make correlation with y plots
    for col in X.columns:
        plt.figure()
        sns.violinplot(x=y, y=X[col])
        plt.title(f'{col} correlation with y')
        plt.savefig(f"{path}/correlation_plots/{col}_correlation.png")
        plt.clf()

    return None

def make_confusion_matrix(aid):
    #create a folder for the plots
    path = aid.path
    X_test = aid.X_test
    y_test = aid.y_test
    if not os.path.exists(f"{path}/confusion_matrix"):
        os.makedirs(f"{path}/confusion_matrix")

    #generate confusion matrix for each model
    for model in aid.best_models:
        y_pred = model.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        plt.figure()
        sns.heatmap(cm, annot=True, cmap='Blues', fmt='d', vmin = 0)
        plt.title(f'{model.__class__.__name__} confusion matrix')
        plt.savefig(f"{path}/confusion_matrix/{model.__class__.__name__}_confusion_matrix.png")
        plt.clf()

    return None

def shap_feature_importance_plot(aid):
    import shap
    import os
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    # Create a folder for the plots
    path = aid.path
    # Use a subset of the data
    X = aid.X.head(int(len(aid.X) * 0.01))  # Adjust as needed
    if not isinstance(X, pd.DataFrame):
        X = pd.DataFrame(X, columns=aid.X.columns)
    if not os.path.exists(f"{path}/shap_feature_importance"):
        os.makedirs(f"{path}/shap_feature_importance")

    # Generate SHAP feature importance for each model
    for model in aid.best_models:
        if model.__class__.__name__ == "LogisticRegression":
            #get feature importance from the model
            importance_values = np.abs(model.coef_).mean(axis=0)
            feature_importance = pd.DataFrame({
                'Feature': X.columns,
                'Importance': importance_values
            }).sort_values(by='Importance', ascending=False)

            # Plot manually
            feature_importance.plot(kind='bar', x='Feature', y='Importance', legend=False)
            plt.title(f'{model.__class__.__name__} Feature Importance')
            plt.savefig(f"{path}/shap_feature_importance/{model.__class__.__name__}_custom_feature_importance.png") #TODO: make sure the names of columns aren't cropped in images
            plt.clf()
            continue

        # Select appropriate SHAP explainer
        if model.__class__.__name__ in ["DecisionTreeClassifier", "RandomForestClassifier", "XGBClassifier"]:
            explainer = shap.TreeExplainer(model)
        else:
            explainer = shap.Explainer(model)

        shap_values = explainer(X)

        # Handle multi-class models
        if len(shap_values.values.shape) > 2:  # Multi-class case
            shap_values_to_plot = shap_values.values.mean(axis=-1)  # Average across classes
        else:
            shap_values_to_plot = shap_values.values

        # Calculate feature importance
        importance_values = np.abs(shap_values_to_plot).mean(axis=0)
        feature_importance = pd.DataFrame({
            'Feature': X.columns,
            'Importance': importance_values
        }).sort_values(by='Importance', ascending=False)

        # Plot manually
        feature_importance.plot(kind='bar', x='Feature', y='Importance', legend=False)
        plt.title(f'{model.__class__.__name__} Shap Feature Importance')
        plt.savefig(f"{path}/shap_feature_importance/{model.__class__.__name__}_custom_feature_importance.png")
        plt.clf()
    return None

def makeplots(aid):
    best_models = aid.best_models
    X_train = aid.X_train
    y_train = aid.y_train
    path = aid.path
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

    if not os.path.exists(f"{path}/plots"): #TODO: fix the convergence plots
        os.makedirs(f"{path}/plots")

    for model in best_models:
        if model.__class__.__name__ == "DecisionTreeClassifier":
            viz = dtreeviz.model(model, X_train, y_train,
                                 target_name="target",
                                 feature_names=X_train.columns)
            viz.view().save(f"{path}/plots/tree.svg")
            #save to png
            plot_tree(model, filled=True)
            plt.savefig(f"{path}/plots/tree.png")

    for file in os.listdir(f"{path}/results/models"):
        if file.endswith(".csv"):
            df = pd.read_csv(f"{path}/results/models/{file}")
            print(df)
            plt.plot(df['f1'])
            plt.plot(df['accuracy'])
            plt.plot(df['precision'])
            plt.plot(df['recall'])
            plt.title(f'{file[:-4]} model')
            plt.ylabel('score')
            plt.xlabel('iteration')
            plt.legend(['f1', 'accuracy', 'precision', 'recall'], loc='upper left')
            plt.savefig(f"{path}/plots/{file}_convergence.png")
            plt.clf()

    sys.stdout.close()
    sys.stderr.close()
    sys.stdout =original_stdout
    sys.stderr = original_stderr

    distribution_plots(aid)
    correlation_plot(aid)
    make_confusion_matrix(aid)
    shap_feature_importance_plot(aid)

    return None

if __name__ == "__main__":
    from project.do_poprawy_code.medaid import medaid
    medaid = medaid(dataset_path='../../data/binary/cardio_train.csv', target_column='cardio', metric="recall", search="random", n_iter=1)
    print(medaid.path)
    medaid.train()
    print("finished_training")
    makeplots(medaid)
    medaid.save()

