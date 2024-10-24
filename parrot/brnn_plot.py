"""
Plot training results for regression and classification tasks on both
sequence-mapped and residue-mapped data.

.............................................................................
idptools-parrot was developed by the Holehouse lab
     Original release ---- 2020

Question/comments/concerns? Raise an issue on github:
https://github.com/idptools/parrot

Licensed under the MIT license.
"""

import itertools
import os
import traceback

import matplotlib as mpl
import numpy as np
import pandas as pd
import seaborn as sn
from scipy.stats import linregress, pearsonr, spearmanr
from sklearn.metrics import (
    accuracy_score,
    auc,
    average_precision_score,
    f1_score,
    matthews_corrcoef,
    precision_recall_curve,
    roc_curve,
)

from parrot import encode_sequence

# Set global font size and line width for better publication clarity
mpl.rcParams["font.size"] = 12
mpl.rcParams["lines.linewidth"] = 2

import matplotlib.pyplot as plt


def training_loss(train_loss, val_loss, output_file_prefix=""):
    """Plot training and validation loss per epoch

    Figure is saved to file at "<output_file_prefix>_train_val_loss.png".

    Parameters
    ----------
    train_loss : list
            training loss across each epoch
    val_loss : list
            validation loss across each epoch
    output_file_prefix : str, optional
            File to which the plot will be saved as "<output_file_prefix>_train_val_loss.png"
    """

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 8))

    num_epochs = len(train_loss)

    # Loss per epoch
    (training_loss,) = ax.plot(np.arange(1, num_epochs + 1), train_loss, label="Train")
    (validation_loss,) = ax.plot(np.arange(1, num_epochs + 1), val_loss, label="Val")
    ax.set_xlabel("Epoch", fontsize=10)
    ax.set_ylabel("Avg loss", fontsize=10)
    plt.suptitle("Training and testing loss per epoch", size=12)
    plt.title(f"epochs={num_epochs}", size=11)

    # Shrink current axis's height by 10% on the bottom
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

    # Add legend at the bottom
    ax.legend(
        handles=[training_loss, validation_loss],
        loc="upper center",
        fontsize=8,
        facecolor="gainsboro",
        edgecolor="slategray",
        bbox_to_anchor=(0.5, -0.15),
        ncol=2,
        fancybox=True,
    )

    if num_epochs < 21:
        ax.set_xticks(np.arange(2, num_epochs + 1, 2))
    elif num_epochs < 66:
        ax.set_xticks(np.arange(5, num_epochs + 1, 5))
    elif num_epochs < 151:
        ax.set_xticks(np.arange(10, num_epochs + 1, 10))
    else:
        ax.set_xticks(np.arange(50, num_epochs + 1, 50))

    plt.savefig(
        output_file_prefix + "_train_val_loss.png",
        dpi=300,
        transparent=True,
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.savefig(
        output_file_prefix + "_train_val_loss.pdf",
        dpi=300,
        transparent=True,
        format="pdf",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.clf()


def sequence_regression_scatterplot(true, predicted, output_file_prefix=""):
    """Create a scatterplot for a sequence-mapped values regression problem

    Figure is saved to file at "<output_file_prefix>_seq_scatterplot.png".

    Parameters
    ----------
    true : list of PyTorch FloatTensors
            A list where each item is a [1 x 1] tensor with the true regression value
            of a particular sequence
    predicted : list of PyTorch FloatTensors
            A list where each item is a [1 x 1] tensor with the regression prediction
            for a particular sequence
    output_file_prefix : str, optional
            File to which the plot will be saved as "<output_file_prefix>_seq_scatterplot.png"
    """

    true_list = []
    pred_list = []

    for item in true:
        true_list.append(item.cpu().numpy()[0][0])
    for item in predicted:
        pred_list.append(item.cpu().numpy()[0][0])

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 8))
    ax.scatter(true_list, pred_list)
    edge_vals = [
        0.9 * min(min(true_list), min(pred_list)),
        1.1 * max(max(true_list), max(pred_list)),
    ]
    plt.xlim(edge_vals)
    plt.ylim(edge_vals)
    plt.plot(edge_vals, edge_vals, "k--")
    plt.xlabel("True", fontsize=10)
    plt.ylabel("Predicted", fontsize=10)

    r_value = 0
    try:
        slope, intercept, r_value, p_value, std_err = linregress(true_list, pred_list)
    except:
        traceback.print_exc()

    plt.suptitle(
        "Testing accuracy for a sequence-mapped values regression problem", size=12
    )
    plt.title("R^2=%.3f" % (r_value**2), size=11)
    plt.savefig(
        output_file_prefix + "_seq_scatterplot.png",
        dpi=300,
        transparent=True,
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.savefig(
        output_file_prefix + "_seq_scatterplot.pdf",
        dpi=300,
        transparent=True,
        format="pdf",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.clf()


def residue_regression_scatterplot(true, predicted, output_file_prefix=""):
    """Create a scatterplot for a residue-mapped values regression problem

    Each sequence is plotted with a unique marker-color combination, up to 70
    different sequences.

    Figure is saved to file at "<output_file_prefix>_res_scatterplot.png".

    Parameters
    ----------
    true : list of PyTorch FloatTensors
            A list where each item is a [1 x len(sequence)] tensor with the true
            regression values of each residue in a sequence
    predicted : list of PyTorch FloatTensors
            A list where each item is a [1 x len(sequence)] tensor with the
            regression predictions for each residue in a sequence
    output_file_prefix : str, optional
            File to which the plot will be saved as "<output_file_prefix>_res_scatterplot.png"
    """

    true_list = []
    pred_list = []

    marker = itertools.cycle((">", "+", ".", "o", "*", "v", "D"))

    for item in true:
        single_frag = item.cpu().numpy()[0].flatten()
        true_list.append(list(single_frag))
    for item in predicted:
        single_frag = item.cpu().numpy()[0].flatten()
        pred_list.append(list(single_frag))

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 8))

    for i in range(len(true_list)):
        ax.scatter(true_list[i], pred_list[i], s=6, marker=next(marker))

    left, right = plt.xlim()
    bottom, top = plt.ylim()
    edge_vals = [min(left, bottom), max(right, top)]
    plt.xlim(edge_vals)
    plt.ylim(edge_vals)
    plt.plot(edge_vals, edge_vals, "k--")
    plt.xlabel("True", fontsize=10)
    plt.ylabel("Predicted", fontsize=10)
    r_value = 0

    try:
        slope, intercept, r_value, p_value, std_err = linregress(
            sum(true_list, []), sum(pred_list, [])
        )
    except:
        traceback.print_exc()

    plt.suptitle(
        "Testing accuracy for a sequence-mapped values regression problem", size=12
    )
    plt.title("R^2=%.3f" % (r_value**2), size=11)
    plt.savefig(
        output_file_prefix + "_res_scatterplot.png",
        dpi=300,
        transparent=True,
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.savefig(
        output_file_prefix + "_res_scatterplot.pdf",
        dpi=300,
        transparent=True,
        format="pdf",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.clf()


def plot_roc_curve(
    true_classes, predicted_class_probs, num_classes, output_file_prefix=""
):
    """Create an ROC curve for a sequence classification problem

    Figure is saved to file at "<output_file_prefix>_ROC_curve.png".

    Parameters
    ----------
    true_classes : list of PyTorch IntTensors
            A list where each item is a [1 x 1] tensor with the true class label of a
            particular sequence
    predicted_class_probs : list of PyTorch FloatTensors
            A list where each item is a [1 x num_classes] tensor of the probabilities
            of assignment to each class
    num_classes : int
            Number of distinct data classes
    output_file_prefix : str, optional
            File to which the plot will be saved as "<output_file_prefix>_ROC_curve.png"
    """

    y_test = np.zeros((len(true_classes), num_classes), dtype=int)
    for i in range(len(true_classes)):
        label = true_classes[i].numpy()[0]
        y_test[i, label] = 1
    y_score = np.vstack(predicted_class_probs)

    # Compute ROC curve and ROC area for each class
    fpr = dict()
    tpr = dict()
    roc_auc = dict()
    for c in range(num_classes):
        fpr[c], tpr[c], _ = roc_curve(y_test[:, c], y_score[:, c])
        roc_auc[c] = auc(fpr[c], tpr[c])

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 8))
    if num_classes > 2:
        # Compute micro-average ROC curve and ROC area (if multiclass)
        fpr["micro"], tpr["micro"], _ = roc_curve(y_test.ravel(), y_score.ravel())
        roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

        # Plot all ROC curves
        ax.plot(
            fpr["micro"],
            tpr["micro"],
            label="Average (area = {0:0.2f})" "".format(roc_auc["micro"]),
            color="deeppink",
            linestyle=":",
            linewidth=4,
        )

        for c in range(num_classes):
            ax.plot(
                fpr[c],
                tpr[c],
                lw=2,
                label="Class {0} (area = {1:0.2f})" "".format(c, roc_auc[c]),
            )

    elif num_classes == 2:  # If binary classification
        # Plot only one curve (doesn't matter which one, they are symmetric)
        ax.plot(
            fpr[1],
            tpr[1],
            lw=2,
            label="Binary class (area = {0:0.2f})" "".format(roc_auc[1]),
        )

    ax.plot([0, 1], [0, 1], "k--", lw=2)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate", fontsize=10)
    plt.ylabel("True Positive Rate", fontsize=10)

    plt.suptitle("Receiver operating characteristic (ROC) curve", size=12)
    plt.title("for a sequence-mapped values classification problem", size=11)

    # Shrink current axis's height by 10% on the bottom
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

    # Add legend at the bottom
    ax.legend(
        loc="upper center",
        fontsize=8,
        facecolor="gainsboro",
        edgecolor="slategray",
        bbox_to_anchor=(0.5, -0.15),
        ncol=5,
        fancybox=True,
    )

    plt.savefig(
        output_file_prefix + "_ROC_curve.png",
        dpi=300,
        transparent=True,
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.savefig(
        output_file_prefix + "_ROC_curve.pdf",
        dpi=300,
        transparent=True,
        format="pdf",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.clf()


def plot_precision_recall_curve(
    true_classes, predicted_class_probs, num_classes, output_file_prefix=""
):
    """Create an PR curve for a sequence classification problem

    Figure is saved to file at "<output_file_prefix>_PR_curve.png".

    Parameters
    ----------
    true_classes : list of PyTorch IntTensors
            A list where each item is a [1 x 1] tensor with the true class label of a
            particular sequence
    predicted_class_probs : list of PyTorch FloatTensors
            A list where each item is a [1 x num_classes] tensor of the probabilities
            of assignment to each class
    num_classes : int
            Number of distinct data classes
    output_file_prefix : str, optional
            File to which the plot will be saved as "<output_file_prefix>_PR_curve.png"
    """

    y_test = np.zeros((len(true_classes), num_classes), dtype=int)
    for i in range(len(true_classes)):
        label = true_classes[i].numpy()[0]
        y_test[i, label] = 1
    y_score = np.vstack(predicted_class_probs)

    # For each class
    precision = dict()
    recall = dict()
    average_precision = dict()
    for i in range(num_classes):
        precision[i], recall[i], _ = precision_recall_curve(y_test[:, i], y_score[:, i])
        average_precision[i] = average_precision_score(y_test[:, i], y_score[:, i])

    # A "micro-average": quantifying score on all classes jointly
    precision["micro"], recall["micro"], _ = precision_recall_curve(
        y_test.ravel(), y_score.ravel()
    )
    average_precision["micro"] = average_precision_score(
        y_test, y_score, average="micro"
    )

    # Plot
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 8))
    ax.plot(
        recall["micro"],
        precision["micro"],
        color="deeppink",
        linestyle=":",
        linewidth=4,
        label="Average (area = {0:0.2f})" "".format(average_precision["micro"]),
    )
    for c in range(num_classes):
        ax.plot(
            recall[c],
            precision[c],
            lw=2,
            label="Class {0} (area = {1:0.2f})" "".format(c, average_precision[c]),
        )

    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("Recall", fontsize=10)
    plt.ylabel("Precision", fontsize=10)
    plt.suptitle("Precision-Recall curve", size=12)
    plt.title("for a sequence-mapped values classification problem", size=11)

    # Shrink current axis's height by 10% on the bottom
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

    # Add legend at the bottom
    ax.legend(
        loc="upper center",
        fontsize=8,
        facecolor="gainsboro",
        edgecolor="slategray",
        bbox_to_anchor=(0.5, -0.15),
        ncol=5,
        fancybox=True,
    )

    plt.savefig(
        output_file_prefix + "_PR_curve.png",
        dpi=300,
        transparent=True,
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.savefig(
        output_file_prefix + "_PR_curve.pdf",
        dpi=300,
        transparent=True,
        format="pdf",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.clf()


def confusion_matrix(
    true_classes, predicted_classes, num_classes, output_file_prefix=""
):
    """Create a confusion matrix for a sequence classification problem

    Figure is saved to file at "<output_file_prefix>_seq_CM.png".

    Parameters
    ----------
    true_classes : list of PyTorch IntTensors
            A list where each item is a [1 x 1] tensor with the true class label of a
            particular sequence
    predicted_classes : list of PyTorch FloatTensors
            A list where each item is a [1 x num_classes] tensor prediction of the
            class label for a particular sequence
    num_classes : int
            Number of distinct data classes
    output_file_prefix : str, optional
            File to which the plot will be saved as "<output_file_prefix>_seq_CM.png"
    """

    cm = np.zeros((num_classes, num_classes))
    for i in range(len(true_classes)):
        cm[np.argmax(predicted_classes[i][0].cpu().numpy()), true_classes[i][0]] += 1

    df_cm = pd.DataFrame(cm, range(num_classes), range(num_classes))
    sn.set_theme(font_scale=1.4)  # for label size
    sn.heatmap(
        df_cm, cmap="Blues", annot=True, annot_kws={"size": 8}, fmt="g"
    )  # font size

    plt.xlabel("True labels", fontsize=10)
    plt.ylabel("Predicted labels", fontsize=10)
    plt.suptitle("Test set confusion matrix", size=12)
    plt.title("for a sequence-mapped values classification problem", size=11)

    plt.tight_layout()

    plt.savefig(
        output_file_prefix + "_seq_CM.png",
        dpi=300,
        transparent=True,
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.savefig(
        output_file_prefix + "_seq_CM.pdf",
        dpi=300,
        transparent=True,
        format="pdf",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.clf()


def res_confusion_matrix(
    true_classes, predicted_classes, num_classes, output_file_prefix=""
):
    """Create a confusion matrix for a residue classification problem

    Figure is saved to file at "<output_file_prefix>_res_CM.png".

    Parameters
    ----------
    true_classes : list of PyTorch IntTensors
            A list where each item is a [1 x len(sequence)] tensor with the true class
            label of the residues in a particular sequence
    predicted_classes : list of PyTorch FloatTensors
            A list where each item is a [1 x num_classes x len(sequence)] tensor
            with predictions of the class label for each residue in a particular
            sequence
    num_classes : int
            Number of distinct data classes
    output_file_prefix : str, optional
            File to which the plot will be saved as "<output_file_prefix>_res_CM.png"
    """

    true_list = []
    pred_list = []

    for item in true_classes:
        single_frag = list(item[0].cpu().numpy().flatten())
        true_list = true_list + single_frag

    for item in predicted_classes:
        single_frag = item[0].permute(1, 0).cpu().numpy()

        for residue in single_frag:
            pred_list.append(np.argmax(residue))

    cm = np.zeros((num_classes, num_classes))
    for i in range(len(true_list)):
        cm[pred_list[i], true_list[i]] += 1

    df_cm = pd.DataFrame(cm, range(num_classes), range(num_classes))
    sn.set_theme(font_scale=1.4)  # for label size
    sn.heatmap(
        df_cm, cmap="Blues", annot=True, annot_kws={"size": 8}, fmt="g"
    )  # font size
    plt.xlabel("True labels", fontsize=10)
    plt.ylabel("Predicted labels", fontsize=10)
    plt.suptitle("Test set confusion matrix ", size=12)
    plt.title("for a residue-mapped values classification problem", size=11)

    plt.tight_layout()

    plt.savefig(
        output_file_prefix + "_res_CM.png",
        dpi=300,
        transparent=True,
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.savefig(
        output_file_prefix + "_res_CM.pdf",
        dpi=300,
        transparent=True,
        format="pdf",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.clf()


def write_performance_metrics(
    sequence_data, dtype, problem_type, prob_class, output_file_prefix=""
):
    """Writes a short text file describing performance on a variety of metrics

    Writes different output depending on whether a classification or regression task
    is specified. Also produces unique output if in probabilistic classification mode.
    File is saved to "<output_file_prefix>_performance_stats.txt".

    Parameters
    ----------
    sequence_data : list of lists
            Details of the output predictions for each of the sequences in the test set. Each
            inner list represents a sample in the test set, with the format: [sequence_vector,
            true_value, predicted_value, sequence_ID]
    dtype : str
            The format of values in the dataset. Should be 'sequence' for datasets
            with a single value (or class label) per sequence, or 'residues' for
            datasets with values (or class labels) for every residue in a sequence.
    problem_type : str
            The machine learning task--should be either 'regression' or 'classification'.
    prob_class : bool
            Flag indicating if probabilistic classification was specified by the user.
    output_file_prefix : str
            Path and filename prefix to which the test set predictions will be saved. Final
            file path is "<output_file_prefix>_performance_stats.txt"
    """

    true_vals = [l[1] for l in sequence_data]
    pred_vals = [l[2] for l in sequence_data]

    perform_metrics = {
        "File": os.path.basename(output_file_prefix),
        "Dataset_Type": dtype,
        "Problem_Type": problem_type,
        "Prob_Class": prob_class,
        "Pearson_R": None,
        "Spearman_R": None,
        "Area_under_Precision_Recall_curve": None,
        "Area_under_ROC": None,
        "Matthews_Correlation_Coef": None,
        "F1_Score": None,
        "Accuracy": None,
    }

    if dtype == "residues":
        true_vals = np.hstack(true_vals)
        pred_vals = np.hstack(pred_vals)

    if problem_type == "classification":
        # Take care of probabilistic-classification case first
        if prob_class:
            # Reformat
            pred_vals = np.vstack(pred_vals)
            true_vals_array = np.zeros((len(true_vals), len(pred_vals[0])), dtype=int)
            for i in range(len(true_vals)):
                true_vals_array[i, true_vals[i]] = 1

            # AUROC, AUPRC
            perform_metrics["Area_under_Precision_Recall_curve"] = round(
                average_precision_score(true_vals_array, pred_vals, average="micro"), 3
            )
            fpr, tpr, _ = roc_curve(true_vals_array.ravel(), pred_vals.ravel())
            perform_metrics["Area_under_ROC"] = round(auc(fpr, tpr), 3)

            # Change probs to discrete classes
            pred_vals = np.argmax(pred_vals, axis=1)

        # Then take care of general classification stats: accuracy, F1, MCC
        perform_metrics["Matthews_Correlation_Coef"] = round(
            matthews_corrcoef(true_vals, pred_vals), 3
        )
        perform_metrics["F1_Score"] = round(
            f1_score(true_vals, pred_vals, average="weighted"), 3
        )
        perform_metrics["Accuracy"] = round(accuracy_score(true_vals, pred_vals), 3)

    elif problem_type == "regression":
        # Pearson R, Spearman R
        pears_r, p_val = pearsonr(true_vals, pred_vals)
        perform_metrics["Pearson_R"] = round(pears_r, 3)
        spearman_r, p_val = spearmanr(true_vals, pred_vals)
        perform_metrics["Spearman_R"] = round(spearman_r, 3)

    # Write performance metrics to file
    with open(output_file_prefix + "_performance_stats.txt", "w") as f:
        for key, value in perform_metrics.items():
            if isinstance(value, (int, float)):
                outstr = "%s: %.3f\n" % (key, float(value))
            else:
                outstr = "%s: %s\n" % (
                    key,
                    value,
                )
            print(outstr)
            f.write(outstr)

    # Convert the dictionary to a DataFrame (Note: it's a single row dictionary)
    df = pd.DataFrame([perform_metrics])

    # Save the DataFrame to a CSV file, formatting floats with 6 decimals
    df.to_csv(
        output_file_prefix + "_performance_stats.csv", index=False, float_format="%.3f"
    )


def output_predictions_to_file(
    sequence_data,
    excludeSeqID,
    encoding_scheme,
    probabilistic_class,
    encoder=None,
    output_file_prefix="",
):
    """Output sequences, their true values, and their predicted values to a file

    Used on the output of the test_unlabeled_data() function in the train_network module in
    order to detail the performance of the trained network on the test set. Produces the
    file "test_set_predictions.tsv" in output_dir. Each pair of lines in this tsvfile
    corresponds to a particular test set sequence, with the first containing the true data
    values, and the second line having the predicted data values.

    Parameters
    ----------
    sequence_data : list of lists
            Details of the output predictions for each of the sequences in the test set. Each
            inner list represents a sample in the test set, with the format: [sequence_vector,
            true_value, predicted_value, sequence_ID]
    excludeSeqID : bool
            Boolean indicating whether or not each line in `tsvfile` has a sequence ID
            (default is False)
    encoding_scheme : str
            Description of how an amino acid sequence should be encoded as a numeric
            vector. Providing a string other than 'onehot', 'biophysics', or 'user'
            will produce unintended consequences.
    probabilistic_class : bool
            Flag indicating if probabilistic classification was specified by the user. If True,
            instead of class labels, predictions will be output as probabilities of each class.
    encoder: UserEncoder object, optional
            If encoding_scheme is 'user', encoder should be a UserEncoder object
            that can convert amino acid sequences to numeric vectors. If
            encoding_scheme is not 'user', use None.
    output_file_prefix : str
            Path and filename prefix to which the test set predictions will be saved. Final
            file path is "<output_file_prefix>_predictions.tsv"
    """

    seq_vectors = []
    true_vals = []
    pred_vals = []
    names = []
    count = 0
    for sequence in sequence_data:
        seq_vector, true_val, pred_val, name = sequence
        seq_vectors.append(seq_vector)
        true_vals.append(true_val)
        pred_vals.append(pred_val)

        if excludeSeqID:
            names.append("test" + str(count))
            count += 1
        else:
            names.append(name)

    # Decode the sequence vectors
    if encoding_scheme == "onehot":
        sequences = encode_sequence.rev_one_hot(seq_vectors)
    elif encoding_scheme == "biophysics":
        sequences = encode_sequence.rev_biophysics(seq_vectors)
    else:
        sequences = encoder.decode(seq_vectors)

    # Write to file
    with open(output_file_prefix + "_predictions.tsv", "w") as tsvfile:
        for i in range(len(names)):

            # Adjust formatting for residues or sequence data
            if isinstance(true_vals[i], np.ndarray):
                true_vals_format = " ".join(true_vals[i].astype(str))
                pred_vals_format = " ".join(pred_vals[i].astype(str))
            elif probabilistic_class:
                true_vals_format = true_vals[i]
                pred_vals_format = " ".join(
                    np.around(pred_vals[i], decimals=4).astype(str)
                )
            else:
                true_vals_format = true_vals[i]
                pred_vals_format = pred_vals[i]

            """
			Format:
			NAME_TRUE SEQUENCE TRUE_VALUE(S)
			NAME_PRED SEQUENCE PRED_VALUE(S)
			"""
            output_str = "%s_TRUE %s %s\n" % (names[i], sequences[i], true_vals_format)
            output_str = output_str + "%s_PRED %s %s\n" % (
                names[i],
                sequences[i],
                pred_vals_format,
            )

            tsvfile.write(output_str)
