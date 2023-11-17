import csv
import os

class ManuscriptRecallEvaluator():

    def get_data_for_special_issues(self, file_path):
        special_issues = {}
        with os.scandir(file_path) as it:
            for entry in it:
                if entry.name.endswith(".csv") and entry.is_file():
                    special_issue_id = entry.name.replace('.csv', '')
                    data = {}
                    data['EID'] = self._get_column_data(entry, "EID")
                    data['AUID'] = self._get_column_data(entry, "Author(s) ID")

                    special_issues[special_issue_id] = data

        return special_issues

    def _get_column_data(self, csv_file, column_name):
        data = []
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            if column_name not in reader.fieldnames:
                print(f"Error: Column '{column_name}' not found in the CSV file.")
                return None

            for row in reader:
                data.append(row[column_name])

        return data



######################################################################################
# Test
######################################################################################

if __name__ == "__main__":
    file = "/Users/curnowl/Downloads/Output/ACA_SI029685.csv"
    filePath = "/Users/curnowl/Downloads/Output"

    evaluator = ManuscriptRecallEvaluator()
    special_issues = evaluator.get_data_for_special_issues(filePath)
    print(special_issues['ACA_SI029685'])


