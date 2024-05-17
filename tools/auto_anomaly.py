from tools import anomaly
from tools.utilities import get_code_with_max_score


def get_anomaly_counts(code: str) -> dict[str, int]:
    """
    Calculates the counts of different anomalies in the given code.

    Args:
        code (str): The code to analyze.

    Returns:
        dict[str, int]: A dictionary containing the counts of different anomalies.
            The keys are the names of the anomalies, and the values
            are the corresponding counts.
    """
    anomaly_counts = {}
    for a in anomaly.style_anomalies:
        num_found, _ = anomaly.get_single_anomaly_score(code, a)
        anomaly_counts[a.name] = num_found
    return anomaly_counts


def auto_anomaly(data: dict, selected_labs: list[float]) -> dict:
    """Find the number of each style anomaly used by each student.

    Args:
        data (dict): A dictionary of all lab submissions for each student.
        selected_labs (list[float]): A list of lab IDs to look for style anomalies in.

    Returns:
        dict: A dictionary containing the anomaly counts for each user and lab.
            The structure of the dictionary is as follows:
            {
                user_id_1: {
                    lab_id_1: [
                        anomalies_found: {
                            'Anomaly 1': num_found,
                            'Anomaly 2': num_found,
                            ...
                        },
                        code
                    ]
                    ...
                },
                user_id_2: {
                    lab_id_1: [
                        anomalies_found: {...},
                        code
                    ]
                    ...
                },
                ...
            }
    """
    output = {}
    for lab in selected_labs:
        for user_id in data:
            if user_id not in output:
                output[user_id] = {}
            if lab in data[user_id]:
                code = get_code_with_max_score(user_id, lab, data)
                anomaly_counts = get_anomaly_counts(code)
                output[user_id][lab] = [anomaly_counts, code]
    return output
