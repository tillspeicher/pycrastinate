# Pycrastinate

Pycrastinate is a library for structuring computations and for caching intermediate results with very little overhead.


## Why do I need it?

Suppose you are working on a data science project that involves a pipeline with multiple stages, like preprocessing data, selecting a model and tuning hyperparameters, training the final model and evaluating it.

Suppose you are preprocessing your data and training your model like this:
```python
def preprocess(data_file="./train.csv"):
    data = pd.load(data_file)
    data = data.drop("some_column")
    data = data.standardize("another_column")

    # More operations like removing rows with missing values, one-hot-encoding, etc
    # ...

    return data

def train():
    data = preprocess()

    model = Model(param_1=v_1, param_2=v_2)
    model.fit(data)

    return model
```

Now you would like to evaluate your model on the test data:
```python
def eval():
    model = train()
    test_data = preprocess("./test.csv")

    scores = model.score(test_data)
    return scores
```

The problem is that every time you want to reevaluate your model --- say with a different metric --- you need to preprocess the data and retrain the model again.
