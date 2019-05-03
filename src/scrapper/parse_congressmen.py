import re
import argparse
from collections import defaultdict
from rawdata_preprocessing import load_data


def get_speaches_by_congressmen(text, date, congressmen_text=None):
    # Congressmen names start with the title prefix, so we use that as trigger
    trigger_pattern = re.compile("(Mr.|Ms.|Mrs.|Miss.) ([\w ]+)\.")
    # What's reported (after the trigger) is the surname all caps (with the 
    # exception of "Mc")
    name_pattern = re.compile(r'^(Mc|)[A-Z]+$')
    end_pattern = '_____+'
    list_of_names = []
    speach_starts = []

    if congressmen_text is None:
        # Set the default value an empty array with the date as key
        congressmen_text = defaultdict(lambda: {date: []})

    for match in re.finditer(trigger_pattern, text):
        name = match.groups()[1]
        if name_pattern.match(name):
            list_of_names.append(name)
            speach_starts.append(match.start())

    for idx, (name, start_pos) in enumerate(zip(list_of_names, speach_starts)):
        end_pos = re.search(end_pattern, text[start_pos:])
        end_pos = end_pos.start() if end_pos is not None else len(text)

        # TODO Idk id there's a more pythonic way of writing this
        if idx < len(speach_starts)-1:
            if end_pos > speach_starts[idx+1]:
                end_pos = speach_starts[idx+1]
        congressmen_text[name][date].append(
                                    {'text': text[start_pos:end_pos],
                                     'idx':  idx})
    return congressmen_text, list_of_names


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert the raw scrapped' +
                                     'data into an orderedDict by date')
    parser.add_argument('filename', type=str,
                        help='Name of the raw data file.')

    args = parser.parse_args()

    if not args.filename.split('.')[-1] == 'clean':
        raise NameError('Your filename should end with ".clean", did you '
                        'preprocess the data?')
    data = load_data(args.filename)
    for idx, (date, text) in enumerate(data.items()):
        congressmen_text, list_of_names =\
            get_speaches_by_congressmen(text, date)
        print(congressmen_text)
        print('\n---------------\n')
        print(set(list_of_names))
        if idx > 3:
            break
