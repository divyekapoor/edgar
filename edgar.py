#!/usr/bin/env python3
import csv
import logging
import os
import sys
from functools import total_ordering
from optparse import OptionParser

import openpyxl
import requests
import requests_cache
from typing import List
from openpyxl.worksheet import Worksheet

USAGE = """
        Edgar Summary of Accounting Policies Extractor
        
        Usage: python3 edgar.py --input input.csv \ 
                    --output accounting_policies.csv
                    --workdir download_directory
                    
        Sample input CSV:
        =================
        ID,URL
        1285550,edgar/data/1285550/000143774915005283/Financial_Report.xlsx
        1259515,edgar/data/1259515/000110465915012580/Financial_Report.xlsx
        351789,edgar/data/351789/000089710115000350/Financial_Report.xlsx
        13372,edgar/data/13372/000007274115000013/Financial_Report.xlsx
        ...
        
        Sample output CSV:
        ==================
        ID,Sheet,Policy,Text
        13372,Description_of_Business,About,"NU Consolidated: NU is a public..."
        13372,Description_of_Business,Basis of Presentation,"The consolidate..."
        13372,Description_of_Business,Accounting Standards,"Recently Adopted..."
        13372,Description_of_Business,Cash and Cash Equivalents,"Cash and ..."
        ...
        
        """

logger = logging.getLogger('main')


def usage():
    print(USAGE)
    sys.stdout.flush()


class OutputRow:
    def __init__(self, id_value: str, policy: str, text: str):
        self.id = id_value
        self.policy = policy
        self.text = text


@total_ordering
class XLSWorksheet:
    def __init__(self, worksheet_index: int,
                 worksheet: openpyxl.worksheet.Worksheet):
        self.worksheet = worksheet
        self.rows = list(worksheet.values)
        self.num_rows = len(self.rows)
        self.worksheet_index = worksheet_index
        self.rows_without_tables = [
            row for row in self.rows if self._allColumnsAfterBAreNone(row)]
        self.num_non_table_rows = len(self.rows_without_tables)

    def is_summary_of_accounting_policies_sheet(self) -> bool:
        """
        Heuristics for detecting the summary of accounting policy sheet.
        We might be wrong (sometimes).
        
        1. Sheet must have more than 50 rows. 50 is tweakable.
        2. Sheet must have more than 50 non table rows. 50 is tweakable.
        3. First 10 rows must contain "Summary of Significant Accounting 
        Policies". 10 is tweakable.
        4. First 10 rows must contain "Significant Accounting Policies". 10 
        is tweakable.
        
        In all the examples, I've seen that the term is present in the first 
        4 or 5 rows. 
        """
        if self.num_rows < 50:
            return False

        if self.num_non_table_rows < 50:
            return False

        for row in self.rows[0:min(10, len(self.rows))]:
            for values in row:
                if values is None:
                    continue
                if not isinstance(values, str):
                    continue
                row_value = values  # type: str
                row_value = row_value.lower()
                if 'summary of significant accounting policies' in row_value:
                    return True
                if 'significant accounting policies' in row_value:
                    return True
        return False

    def _allColumnsAfterBAreNone(self, row):
        slice = row[2:]
        for entry in slice:
            if entry is not None:
                return False
        return True

    def __str__(self):
        return '(rows: {}, non_table_rows: {}, worksheet_index: {}, {})'.format(
            self.num_rows, self.num_non_table_rows,
            self.worksheet_index, self.worksheet.title)

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return self.num_rows < other.num_rows or (
            self.num_rows == other.num_rows
            and self.worksheet_index < other.worksheet_index)

    def __eq__(self, other):
        return self.worksheet == other.worksheet


class InputRow:
    def __init__(self, id_value: str, edgar_url: str):
        self.id = id_value
        self.edgar_url = edgar_url
        self.xls_file = None

    def fetch_file(self, working_dir: str):
        fully_qualified_url = 'https://www.sec.gov/Archives/' + self.edgar_url
        filename = os.path.abspath(
            os.path.join(working_dir, 'Financial_Report_' + self.id + '.xlsx'))
        logger.info('Starting fetch for %s', fully_qualified_url)
        r = requests.get(fully_qualified_url)
        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
        self.xls_file = filename
        logger.info('Fetched %s', self.xls_file)

    def get_accounting_policies(self) -> List[OutputRow]:
        logger.info('Processing accounting policy for %s', self)
        results = []
        workbook = openpyxl.load_workbook(self.xls_file)
        top_sheets = sorted(
            [XLSWorksheet(index, worksheet)
             for index, worksheet in enumerate(workbook.worksheets)],
            reverse=True)
        logger.info('Top sheets: %s', top_sheets)
        accounting_policy_sheets = [
            worksheet for worksheet in top_sheets
            if worksheet.is_summary_of_accounting_policies_sheet()]
        logger.info('Accounting Policy sheets: %s', accounting_policy_sheets)

        return results

    def __str__(self):
        return '({}, {})'.format(self.id, self.edgar_url)

    def __repr__(self):
        return self.__str__()


def main():
    logging.basicConfig(level=logging.INFO)

    logger.info('******** Starting up *******')
    logger.info('Args: %r', sys.argv)

    parser = OptionParser()
    parser.add_option('-i', '--input', dest='input',
                      help='CSV file that provides an ID and an '
                           'Edgar URL to fetch financial information '
                           'for companies.')
    parser.add_option('-o', '--output', dest='output',
                      help='CSV file name where Summary of Accounting '
                           'policies will be extracted.')
    parser.add_option('-w', '--workdir', dest='workdir',
                      help='The working directory to use for saving '
                           'downloaded XLSX files.')
    parser.set_usage(USAGE)
    options, args = parser.parse_args()

    logger.info('Options: %s', options)

    if options.input is None or options.output is None or \
                    options.workdir is None:
        usage()
        sys.exit(1)

    logger.info('Creating directories if not present: %s', options.workdir)
    try:
        os.makedirs(options.workdir)
    except FileExistsError as e:
        logger.info('Directory already present.')

    with open(options.input, 'r') as input_csv:
        reader = csv.DictReader(input_csv)
        inputs = [InputRow(record['ID'], record['URL']) for record in reader]
        logger.info('Inputs: %s', inputs)
        for input in inputs:
            requests_cache.install_cache(os.path.abspath(os.path.join(
                options.workdir, 'requests_cache')))
            input.fetch_file(options.workdir)
            input.get_accounting_policies()


if __name__ == '__main__':
    main()
