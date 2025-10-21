"""This script is adapted from an existing baseline code 
from https://github.com/M3SOulu/SDMO2025Project/blob/main/project1developers.py
The code has been refactored and logging has been added as well as simple CLI. 
The logic has been modified so that developers are considered the same (i.e., a pair is formed) 
if their email address is identical or if at least two other conditions are true. 
"""

import csv
import unicodedata
import string
from itertools import combinations
import os
import logging
import argparse
from Levenshtein import ratio as sim
import pandas as pd
from pydriller import Repository

def setup_logging():
    """Setup for logger"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )
    logging.getLogger("pydriller").setLevel(logging.WARNING)

def get_developers_from_repo(repo_url):
    """Fetch unique name, email pairs from a Git repository using PyDriller."""
    logging.info("Fetching developers from repository: %s", repo_url)
    devs = set()
    try:
        for commit in Repository(repo_url).traverse_commits():
            devs.add((commit.author.name, commit.author.email))
            devs.add((commit.committer.name, commit.committer.email))
    except Exception as e:
        logging.error("Failed to fetch repository %s", e)

    devs_sorted = sorted(devs)
    logging.info("Found %d unique developer entries", len(devs_sorted))
    return devs_sorted

def save_developers_to_csv(devs, outputfile):
    """Saves name, email pairs to a CSV file."""
    # creates project1devs folder if it doesn't exists
    ensure_output_folder()
    with open(os.path.join("project1devs", f"{outputfile}.csv"),
              'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"')
        writer.writerow(["name", "email"])
        writer.writerows(devs)
    logging.info('Saved developers to "%s"', f"{outputfile}.csv")

def load_developers_from_repo(repo_url, outputfile):
    """
    calls get_developers_from_repo and then save_developers_to_csv
    """
    logging.info("Loading developers from repository...")
    devs = get_developers_from_repo(repo_url)
    if not devs:
        raise ValueError("No developers found. Repository URL might be invalid.")
    save_developers_to_csv(devs, outputfile)

def read_developers(filename):
    """Reads an existing CVS file of developers with name,dev columns."""
    logging.info("Reading existing CSV file of developers")
    devs = []
    # creates project1devs folder if it doesn't exists
    ensure_output_folder()
    with open(os.path.join("project1devs", f"{filename}.csv"),
              'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            devs.append(row)
    return devs[1:]   # First element is header, skip

def process(dev):
    """Function for pre-processing each name,email"""
    name: str = dev[0]

    # Remove punctuation
    trans = name.maketrans("", "", string.punctuation)
    name = name.translate(trans)
    # Remove accents, diacritics
    name = unicodedata.normalize('NFKD', name)
    name = ''.join([c for c in name if not unicodedata.combining(c)])
    # Lowercase
    name = name.casefold()
    # Strip whitespace
    name = " ".join(name.split())


    # Attempt to split name into firstname, lastname by space
    parts = name.split(" ")
    # Expected case
    if len(parts) == 2:
        first, last = parts
    # If there is no space, firstname is full name, lastname empty
    elif len(parts) == 1:
        first, last = name, ""
    # If there is more than 1 space, firstname is until first space, rest is lastname
    else:
        first, last = parts[0], " ".join(parts[1:])

    # Take initials of firstname and lastname if they are long enough
    i_first = first[0] if len(first) > 1 else ""
    i_last = last[0] if len(last) > 1 else ""

    # Determine email prefix
    email: str = dev[1]
    prefix = email.split("@")[0]

    return name, first, last, i_first, i_last, email, prefix

def compute_similarity(devs):
    """Compute similarity between all possible pairs"""
    logging.info("Computing similarity for developers")
    similarity = []
    for dev_a, dev_b in combinations(devs, 2):
        similarity.append(compute_pair_similarity(dev_a, dev_b))
    return similarity

def compute_pair_similarity(dev_a, dev_b):
    """Helper function for compute similarity for a single pair (dev_a, dev_b)"""
    # Pre-process both developers
    name_a, first_a, last_a, i_first_a, i_last_a, email_a, prefix_a = process(dev_a)
    name_b, first_b, last_b, i_first_b, i_last_b, email_b, prefix_b = process(dev_b)

    # Conditions of Bird heuristic
    c1 = sim(name_a, name_b)
    c2 = sim(prefix_b, prefix_a)
    c31 = sim(first_a, first_b)
    #If either last name is empty, no similarity is calculated for it. Modified from Bird.
    if last_a == "" or last_b == "":
        c32 = 0.0
    else:
        c32 = sim(last_a, last_b)
    c4 = c5 = c6 = c7 = False
    # Since lastname and initials can be empty, perform appropriate checks
    if i_first_a != "" and last_a != "":
        c4 = i_first_a in prefix_b and last_a in prefix_b
    if i_last_a != "":
        c5 = i_last_a in prefix_b and first_a in prefix_b
    if i_first_b != "" and last_b != "":
        c6 = i_first_b in prefix_a and last_b in prefix_a
    if i_last_b != "":
        c7 = i_last_b in prefix_a and first_b in prefix_a

    # Save similarity data for each conditions. Original names are saved
    return [dev_a[0], email_a, dev_b[0], email_b, c1, c2, c31, c32, c4, c5, c6, c7]

def filter_similarity(df, t):
    """Set similarity threshold, check c1-c3 against the threshold 
    and require >=2 conditions OR identical emails."""
    logging.info("Filtering similarity with threshold %.2f", t)
    df["c1_check"] = df["c1"] >= t
    df["c2_check"] = df["c2"] >= t
    df["c3_check"] = (df["c3.1"] >= t) & (df["c3.2"] >= t)
    # Count number of True conditions
    df["n_true_conditions"] = df[["c1_check", "c2_check",
                                  "c3_check", "c4", "c5", "c6", "c7"]].sum(axis=1)

    # Duplicates if:
    #  - emails are identical OR
    #  - at least two conditions are True
    df["duplicate"] = (df["email_1"] == df["email_2"]) | (df["n_true_conditions"] >= 2)

    # Keep only duplicates
    df = df[df["duplicate"]]

    return df

def save_similarity_df(df, t, outputfile):
    """Omit "check" columns, save to CSV"""
    # creates project1devs folder if it doesn't exists
    ensure_output_folder()
    df = df[["name_1", "email_1", "name_2", "email_2", "c1", "c2",
                 "c3.1", "c3.2", "c4", "c5", "c6", "c7"]]
    df.to_csv(os.path.join("project1devs", f"{outputfile}_similarity_t={t}.csv"),
              index=False, header=True)
    logging.info('Filtered similarity data saved to "%s"', f"{outputfile}_similarity_t={t}.csv")
    return df

def save_all_pairs(df, outputfile):
    """Save all possible developer pairs to CSV 
    before applying any threshold filtering"""
    # creates project1devs folder if it doesn't exists
    ensure_output_folder()
    df.to_csv(os.path.join("project1devs", f"{outputfile}_similarity.csv"),
              index=False, header=True)
    logging.info('All pairs similarity data saved to "%s"', f"{outputfile}_similarity.csv")
    return df

def create_similarity_dataframe(similarity):
    """Convert similarity list into dataframe."""
    cols = ["name_1", "email_1", "name_2", "email_2", "c1", "c2",
        "c3.1", "c3.2", "c4", "c5", "c6", "c7"]
    df = pd.DataFrame(similarity, columns=cols)
    return df

def ensure_output_folder():
    """Ensure that the output folder 'project1devs' exists."""
    os.makedirs("project1devs", exist_ok=True)


def parse_args():
    """
    Parse command-line arguments for the script.
    Returns:
        argparse.Namespace: parsed arguments
    """
    parser = argparse.ArgumentParser(
    description=("Compute developer similarity pairs "
    "from an existing CSV(default) or a Git repository."
        ),
        epilog=(
            "See examples of using arguments in the Readme.md file."

        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('-t', '--threshold', type=float, default=0.7,
                        metavar='', help='Similarity threshold (default: 0.7)')
    parser.add_argument('-f', '--file', type=str, default='devs',
                        metavar='', help='File name prefix for input CSV and ' \
                        'for output similarity files (default: devs)')
    parser.add_argument('-r', '--repo', type=str, default=None,
                        metavar='', help='Optional Git repo URL or path')

    return parser.parse_args()

def fetch_or_read_developers(file: str, repo_url: str = None):
    """
    Ensures developer data is available, either by fetching from repo or reading CSV.
    Returns a list of developers, or an empty list if data could not be retrieved.
    """
    if repo_url:
        logging.info("Fetching developers from repository: %s", repo_url)
        try:
            load_developers_from_repo(repo_url, file)
        except Exception as e:
            logging.error("Failed to load developers from repo: %s", e)
            return []

    else:
        logging.info("Using existing CSV file in project1devs folder: %s.csv", file)

    # Checks that the CSV exist
    csv_path = os.path.join("project1devs", f"{file}.csv")
    if not os.path.exists(csv_path):
        logging.error('CSV file "%s" not found. Run with --repo to fetch data first.', csv_path)
        return []

    return read_developers(file)

def main():
    """ 
    Main entry point of the script.

    Reads developer (name, email) pairs from an existing CSV in project1devs
    or fetches them from a Git repository if a URL is provided

    Computes similarity scores between all developers, filters pairs based on 
    a threshold, and saves the results.
    """
    
    setup_logging()
    args = parse_args()

    t = args.threshold
    file = args.file
    repo_url = args.repo

    devs = fetch_or_read_developers(file, repo_url)
    if not devs:
        return

    similarity = compute_similarity(devs)

    # Create a dataframe
    df = create_similarity_dataframe(similarity)

    # Save data on all pairs (might be too big -> comment out to avoid)
    df = save_all_pairs(df, file)

    df_filtered = filter_similarity(df, t)
    save_similarity_df(df_filtered, t, file)

if __name__ == "__main__":
    main()
