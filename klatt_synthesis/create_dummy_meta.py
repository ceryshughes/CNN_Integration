import csv
import os

files = os.listdir("dummy_sounds")
token_names = list(set([file[0:file.index(".")] for file in files]))
tokens = {file_id: file_id[len(file_id)-1] for file_id in token_names}

with open("dummy_meta.csv", 'w', newline='') as csvfile:
    fieldnames = ["FileID", "Category"]
    col_writer = csv.writer(csvfile)
    col_writer.writerow(fieldnames)
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    for token in tokens:
        writer.writerow({"FileID": token + ".wav", "Category": tokens[token]})