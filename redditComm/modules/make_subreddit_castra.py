from pandas import Timestamp, NaT, DataFrame
from toolz import dissoc, peek, partition_all
from castra import Castra
import subreddit_dumps, output, json

columns = ['archived', 'author', 'author_flair_css_class', 'author_flair_text',
           'body', 'controversiality', 'created_utc', 'distinguished', 'downs',
           'edited', 'gilded', 'link_id', 'name', 'parent_id',
           'removal_reason', 'score', 'score_hidden', 'subreddit', 'ups']

def to_json(line):
    """Convert a line of json into a cleaned up dict."""
    # Convert timestamps into Timestamp objects
    date = line['created_utc']
    line['created_utc'] = Timestamp.utcfromtimestamp(int(date))
    edited = line['edited']
    line['edited'] = Timestamp.utcfromtimestamp(int(edited)) if edited else NaT

    # Convert deleted posts into `None`s (missing text data)
    if line['author'] == '[deleted]':
        line['author'] = None
    if line['body'] == '[deleted]':
        line['body'] = None

    # Remove 'id', and 'subreddit_id' as they're redundant
    # Remove 'retrieved_on' as it's irrelevant
    return dissoc(line, 'id', 'subreddit_id', 'retrieved_on')

def to_df(batch):
    """Convert a list of json strings into a dataframe"""
    blobs = map(to_json, batch)
    df = DataFrame.from_records(blobs, columns = columns)
    return df.set_index('created_utc')

def load(subreddit):
    with open('./subreddit_dumps/json/'+subreddit+'_dump.json', 'r') as f:
        data = json.load(f)
    f.closed
    return data

def execute(subreddit):
    categories = ['distinguished', 'subreddit', 'removal_reason']
    f = load(subreddit)
    batches = partition_all(2000, f)
    df, frames = peek(map(to_df, batches))
    castra = Castra('./subreddit_dumps/'+subreddit+'_data.castra', template = df, categories = categories)
    castra.extend_sequence(frames, freq = '3h')
