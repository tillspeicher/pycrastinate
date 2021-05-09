import pandas as pd
import Experiemnt, Result


exp = Experiment(
    storage_mode="files",
    storage_dir="./data/",
    results_dir="./results/",
)


@exp.stage("preproc")
def preprocessing(
    # File dependency checks whether the hash of the input file changed to decide
    # whether to rerun it
    # TODO: check whether using Path from pathlib here is possible instead of a new type
    data_file = FileDependency("./data/train.pkl"),
):
    data = ...
    return data

@exp.stage()
def hyperparameter_tuning(
    network_depth: list[int] = [2, 5, 7],
    data: pd.df = Result("preproc")
):
    best_performance = -1
    best_model = None
    # can be made experiment stages to cache the results efficiently and to
    # automatically parallelize the computation.
    # Show this in the docs.
    for param in network_depth:
        model = Model(param)
        performance = model.train(data)
        if performance > best_performance:
            best_performance = performance
            best_model = model

    return best_model

@exp.stage()
def evaluation(
    # Reruns every time the file changes
    # TODO: How to run this through the preprocessing stage as well with a different input?
    test_data_file = Result("preproc", data_file="./data/test.pkl"),
    # TODO: add name=... optiona to parameters to make refactoring the function arguments easier
    model = Result("hyperparameter_tuning"),
    # For input parameter specification support
    # one of n
    # multiple of n
    # a range, > x, < x, etc
    metric: str = Param(..., valid_options=["accurracy", "auc"], description="...")
):
    test_data = pd.load(test_data_file)
    performance = eval(model, test_data, metric)
    return performance


@exp.output()
def evaluation_output(
    performance = Result("evaluation"),
    evaluation_params = StageParams("evaluation"),
    writer = Writer(format="markdown"),
):
    # TODO: mimic the file interface with writer
    writer.writeln("## Evalutation results:\n")
    writer.writeln(f"Number of layers: {len(evaluation_params.model.layers)}")
    writer.writeln(f"Performance: {performance}")
    
    # TODO: add example for using figure
    # TODO: add example for displaying output in Jupyter notebook


eval_exp = Experiment()

@eval_exp.stage
def eval_accuracy(
    balanced: bool,
    test_data_file = Result("preproc", data_file="./data/test.pkl"),
    model = Result("hyperparameter_tuning"),
):
    return accurracy

@eval_exp.stage
def eval_auc():
    pass

# Now you can call all experiments defined for eval_exp for exp as well
exp.add_sub_exp(eval_exp)


# Commandline usage
if __name__ == "__main__":
    # Creates a cmd interface based on the experiment definition
    # TODO: rename function
    execute_cmd(exp)
    # Maybe like this?
    exp()

    # Now execute
    # Python exp.py evaluation --test_data_file="./data/test2.pkl" --metric=auc
    # python exp.py eval_accuracy
    # python exp.py evaluation_output

# api usage
exp.evaluation(test_data_file="./data/test2.pkl", metric="auc")
exp.evaluation_output(format="md") # + some macro to make it work with Jupyter cells


# TODO: experiment as class
class DinosaurExperiment(Experiment):

    @self.stage("dna")
    def find_dinosaur_dna(self):
        pass

    @self.stage()
    def clone_dinosaur(self, dna=Result("dna")):
        pass

    @self.stage()
    def build_theme_park(self, dinosaur=Result("clone_dinosaur")):
        pass

    @self.output()
    def theme_park_output(
        self, theme_park=Result("build_theme_park"), writer=SemanticWriter(format="md")
    ):
        writer.heading("## The theme park:")
        writer.list(["item 1", "item 2"]) # TODO: generate list items via writer


# TODO: show that you can use it for non-datasciency stuff as well



# Missing and considerations:
# Output: writer should have file-like interface, but also create "higher-level"
# Writer with semantic (write_heading, write_list) etc. commands
# Parallelization
# Save timings

# When running one experiments, the inputs to another one might need to be specified
# as well, i.e. when running eval, some data preprocessing switch might need to be set
# Should be doable via the Result() argument
