import json

def create_tsv_from_json(info_json_path: str, tsv_path: str):
    """
    Creates a tab seperated file for each utterance described
    in the json file.

    Each utterance in the json has the utterance ID as key.
    This function writes the utterance ID, the utterance text,
    and the utterance pronunciation to the tab seperated file.

    The text of utterance x is in json[x][text_info][text]
    The pronunciation of utterance x is in json[x][text_info][pron]

    """

    with open(info_json_path, 'r') as f:
        info_json = json.load(f)

    with open(tsv_path, 'w') as f:
        for utterance_id in info_json:
            f.write(utterance_id + '\t' + info_json[utterance_id]['text_info']['text'] + '\t' + info_json[utterance_id]['text_info']['pron'] + '\n')
