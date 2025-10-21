# SDMO

This repository is for Software Development, Maintanance and Operations course

## Project 1: Developer de-duplication

This script identifies likely duplicate developer entries from Git repositories based on name and email similarity.

It is adapted from an existing baseline code:  
https://github.com/M3SOulu/SDMO2025Project/blob/main/project1developers.py 

The code has been refactored, added logging, and modified logic: developers are considered the same if their email addresses match **or** if at least two other similarity conditions are true. And if the part considered as the last name is empty, it will no longer cause a match between developers last names.

## Contents

project1devs/: Directory with data for Project 1

- `**devs.csv**``: List of developers mined from Dify  
- **devs_similarity.csv**: Similarity tests for each pair of developers (Dify)  
- **devs_similarity_t=0.9.csv**: Similarity tests for each pair of developers (Dify) with similarity threshold 0.9  

- **devs2.csv**: List of developers mined from Immich  
- **devs2_similarity.csv**: Similarity tests for each pair of developers (Immich)  
- **devs2_similarity_t=0.95.csv**: Similarity tests for each pair of developers (Immich) with similarity threshold 0.95  

- **project1developers.py**: Script for mining developer information and determining duplicate developers  
- **test_project1developers.py**: Test module for `project1developers.py`  
- **requirements.txt**: List of used libraries with specified versions  

## Features

- Fetch unique developer `(name, email)` pairs from a Git repository using Pydriller.
- Compute similarity between developers based on name and email similarity using modified Bird's heuristics.
- Filter developer pairs based on a threshold `t` and duplicate logic.
- Save all pairs or filtered results as CSV files in `project1devs/`.

## Dependency Installation

Install dependencies via:

```bash
pip install -r requirements.txt
```
## Running the Script

The script can either fetch developer data from a Git repository or read an existing CSV file in the project1devs/ folder. By default, it reads devs.csv and uses a similarity threshold of 0.7.

### To see available command-line options:

```bash
python project1developers.py --help
```
### Example Runs

#### Run with default settings (read devs.csv, threshold 0.7):

```bash
python project1developers.py
```

#### Specify a similarity threshold and/or output file prefix:

```bash
python project1developers.py -t 0.85 -f results
```
#### Fetch developer data from a GitHub repository: 

This repository was used in the project, and devs.csv will contain the developers from this repository:

```bash
python project1developers.py -r https://github.com/langgenius/dify
```

This is the second analyzed repository. Its developers will be saved in devs2.csv. You can also specify the output file prefix and threshold directly:

```bash
python project1developers.py -r https://github.com/immich-app/immich -t 0.9 -f devs2
```


### Command-line Arguments

-t, --threshold — Similarity threshold for filtering duplicate developers (default: 0.7).

-f, --file — CSV file prefix for input and output files (default: devs).

-r, --repo — Optional Git repository URL or local path. If provided, developer data is fetched from the repo instead of reading an existing CSV.

### The script will:

1. Fetch developers from the repository or read an existing CSV file in `project1devs/`.
2. Compute similarity between all developer pairs.
3. Save all pairs in `<outputfile>_similarity.csv`.
4. Save filtered duplicates in `<outputfile>_similarity_t=<t>.csv`.


## Tests

This project includes unit tests for project1developers.py, Tests are implemented using `unittest module`, 

You can run the tests:

```bash
python -m unittest discover
```

If you want to measure test coverage, you can run:

```bash
coverage run -m unittest discover
coverage report -m
```
