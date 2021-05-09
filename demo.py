

@stage
def preprocess(norm_constant=5):
    data = ...
    data.normalize(norm_constant)
    data.standardize()
    return {
        "data": data,
        "stats": ...,
    }


@stage
def train_model(
    param = 0.5,
    data = UseRes(preprocess, args=Args(norm_constant=7))
    param =Depens(...)
):
    model = Model(param)
    model.fit(data)
    return model


@hook
def hook(model = UseTrigger(train_model)):
    print("model accuracy:", model.stats)



train_model()
