#!/usr/bin/env python3
#
# Author: Divye Kapoor (divyekapoor@gmail.com)
# Date: Sept 16, 2017
# Upwork Contract: https://www.upwork.com/d/contracts/18729685
#
# Code Tested with Python 3.5.3
#
import csv
import logging
import logging.config
import os
import platform
import re
import subprocess
import sys
import shutil
import zipfile
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
                    --output accounting_policies.csv \ 
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

#
# For converting between XLS and XLSX formats.
# Please see the attached ofc.ini file for documented explanations.
#
OFC_INI = r"""
[Run]
LogDestinationPath={log_destination}
Description= "{description}"
TimeOut = 300

[ConversionOptions]
CABLogs=0
MacroControl=0

[FoldersToConvert]
fldr={input_folder}

[ConversionInfo]
SourcePathTemplate=*\ 
DestinationPathTemplate={output_folder}
        """

logger = logging.getLogger(__name__)


def usage():
    print(USAGE)
    sys.stdout.flush()


def create_dir(directory_name):
    logger.info('Creating directories if not present: %s', directory_name)
    try:
        os.makedirs(directory_name)
    except FileExistsError as e:
        logger.info('Directory already present: %s', directory_name)


class OutputRow:
    def __init__(self, id_value: str, sheet_name: str, policy: str, text: str):
        self.id = id_value
        self.sheet_name = sheet_name
        self.policy = policy
        self.text = text

    def get_dict(self):
        return {
            'ID': self.id,
            'Sheet': self.sheet_name,
            'Policy': self.policy,
            'Text': self.text
        }


class OutputCSV:
    def __init__(self, file_name: str, rows: List[OutputRow]):
        self.file_name = file_name
        self.rows = rows

    def write(self):
        logger.info('Writing accounting policies to %s', self.file_name)
        with open(self.file_name, 'w') as output_csv_file:
            dict_writer = csv.DictWriter(
                output_csv_file, fieldnames=["ID", "Sheet", "Policy", "Text"])
            dict_writer.writeheader()
            for row in self.rows:
                dict_writer.writerow(row.get_dict())
        logger.info('Written %d rows', len(self.rows))
        if len(self.rows) == 0:
            logger.error('No rows written to file %s', self.file_name)


class AccountingPolicy:
    def __init__(self,
                 id_value: str,
                 sheet_name: str,
                 policy_name: str,
                 policy_values: List[str]):
        self.id = id_value
        self.sheet_name = sheet_name
        self.policy_name = policy_name
        self.policy_values = policy_values

    def get_output_row(self):
        policy_text = ' '.join(self.policy_values)
        policy_text = re.sub('[^a-zA-Z0-9.$ ]+', '', policy_text)
        return OutputRow(self.id, self.sheet_name, self.policy_name,
                         policy_text)


@total_ordering
class XLSWorksheet:
    def __init__(self,
                 id_value: str,
                 workbook: openpyxl.Workbook,
                 worksheet_index: int,
                 worksheet: openpyxl.worksheet.Worksheet):
        self.id = id_value
        self.workbook = workbook
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

    def extract_accounting_policies(self) -> List[AccountingPolicy]:
        accounting_policies = []
        current_accounting_policy = None
        # Start from the 4th row.
        for row in self.rows_without_tables[4:]:
            b_column_value = row[1]
            if b_column_value is None or not isinstance(b_column_value, str):
                continue
            if self._isHeader(b_column_value):
                if current_accounting_policy is None:
                    current_accounting_policy = AccountingPolicy(
                        self.id,
                        self.worksheet.title,
                        b_column_value, [])
                else:
                    accounting_policies.append(current_accounting_policy)
                    current_accounting_policy = AccountingPolicy(
                        self.id,
                        self.worksheet.title,
                        b_column_value, [])
            else:
                if current_accounting_policy is None:
                    current_accounting_policy = AccountingPolicy(
                        self.id,
                        self.worksheet.title,
                        'Preamble',
                        [b_column_value])
                else:
                    current_accounting_policy.policy_values.append(
                        b_column_value)
        if current_accounting_policy is not None:
            accounting_policies.append(current_accounting_policy)
        return accounting_policies

    def _allColumnsAfterBAreNone(self, row):
        slice = row[2:]
        for entry in slice:
            if entry is not None:
                return False
        return True

    def _isHeader(self, b_column_value: str):
        """
        Sensitive piece of code:
         The choice of parameter for the number of words here determines
         whether we will get all the accounting policies or miss a few.

        The current parameter value is 8 which is short enough to capture
        most headings while excluding short sentences before tables. This
        value is tweakable.
        """
        if len(b_column_value.split(' ', 9)) > 8:
            return False
        if 'year' in b_column_value \
                or '$' in b_column_value:
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
        filename_from_url, extension = os.path.splitext(self.edgar_url)
        filename = os.path.abspath(
            os.path.join(
                working_dir, 'Financial_Report_' + self.id + extension))
        logger.info('Starting fetch for %s', fully_qualified_url)
        r = requests.get(fully_qualified_url)
        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
        self.xls_file = filename
        logger.info('Fetched %s', self.xls_file)
        logger.info('Testing whether %s is an XLSX file', self.xls_file)
        if not zipfile.is_zipfile(self.xls_file):
            logger.info('%s is not an XLSX file. Trying to convert (Windows '
                        'only)', self.xls_file)
            self._convert_xls_to_xlsx(working_dir)

    def _convert_xls_to_xlsx(self, working_dir: str):
        if not platform.system() == 'Windows':
            raise NotImplementedError(
                'XLS to XLSX conversion supported only on Windows.')

        convert_dir = os.path.abspath(
            os.path.join(working_dir, 'convert_' + str(self.id)))
        create_dir(convert_dir)
        target_dir = os.path.abspath(
            os.path.join(working_dir, 'xlsx_target_dir'))
        create_dir(target_dir)
        logger.info('Copying {} to {}'.format(self.xls_file, convert_dir))
        shutil.copy2(self.xls_file, convert_dir)
        ofc_ini_file_contents = OFC_INI.format_map({
            "log_destination": os.path.join(target_dir, 'convert.log'),
            "description": 'Conversion for {}'.format(self),
            "input_folder": convert_dir,
            "output_folder": target_dir
        })
        ofc_ini_file_path = os.path.join(convert_dir, 'ofc.ini')
        logger.info('Writing ofc.ini at {}'.format(ofc_ini_file_path))
        with open(ofc_ini_file_path, 'w') as ofc_file:
            ofc_file.write(ofc_ini_file_contents)
        logger.info('Executing ofc.exe')
        ofc_output = subprocess.check_output(
            ['C:\OMPM\TOOLS\ofc.exe', ofc_ini_file_path],
            shell=True,
            universal_newlines=True,
            stderr=subprocess.STDOUT)
        logger.info('OFC output: {}'.format(ofc_output))
        all_converted_files = os.listdir(target_dir)
        logger.info('All Converted Files: {}', str(all_converted_files))
        converted_files = [file for file in all_converted_files if
                           os.path.splitext(file)[1].lower() == 'xlsx']
        logger.info('Output files: {}. Picking first one if available.'.format(
            converted_files))

        if len(converted_files) > 0:
            converted_file = converted_files[0]
            logger.info('Overwriting {} with {}'.format(
                self.xls_file, converted_file))
            shutil.copy2(converted_file, self.xls_file)
            logger.info('Conversion done.')
        else:
            logger.error('XLS to XLSX Conversion failed.')

    def get_accounting_policies(self) -> List[AccountingPolicy]:
        logger.info('Processing accounting policy for %s', self)
        workbook = openpyxl.load_workbook(self.xls_file)
        top_sheets = sorted(
            [XLSWorksheet(self.id, workbook, index, worksheet)
             for index, worksheet in enumerate(workbook.worksheets)],
            reverse=True)
        logger.info('Top sheets: %s', top_sheets)
        accounting_policy_sheets = [
            worksheet for worksheet in top_sheets
            if worksheet.is_summary_of_accounting_policies_sheet()]
        logger.info('Accounting Policy sheets: %s', accounting_policy_sheets)
        results = []
        for worksheet in accounting_policy_sheets:
            results.extend(worksheet.extract_accounting_policies())
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
    parser.add_option('-o', '--outputdir', dest='outputdir',
                      help='Output directory where Summary of Accounting '
                           'policies will be extracted.')
    parser.add_option('-w', '--workdir', dest='workdir',
                      help='The working directory to use for saving '
                           'downloaded XLSX files.')
    parser.set_usage(USAGE)
    options, args = parser.parse_args()

    logger.info('Options: %s', options)

    if options.input is None or options.outputdir is None or \
                    options.workdir is None:
        usage()
        sys.exit(1)

    create_dir(options.workdir)
    create_dir(options.outputdir)

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'basic': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s %(name)-8s %(levelname)-6s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'basic'
            },
            'file_info': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'filename': os.path.abspath(os.path.join(options.outputdir,
                                                         'edgar_info.log')),
                'mode': 'w',
                'formatter': 'basic'
            },
            'file_errors': {
                'class': 'logging.FileHandler',
                'level': 'ERROR',
                'filename': os.path.abspath(os.path.join(options.outputdir,
                                                         'edgar_errors.log')),
                'mode': 'w',
                'formatter': 'basic'
            }
        },
        'loggers': {
            '__main__': {
                'handlers': ['console', 'file_info', 'file_errors'],
                'propagate': False,
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'file_info', 'file_errors']
        }
    })

    requests_cache.install_cache(os.path.abspath(os.path.join(
        options.workdir, 'requests_cache')))

    with open(options.input, 'r') as input_csv:
        reader = csv.DictReader(input_csv)
        inputs = [InputRow(record['ID'], record['URL']) for record in reader]
        logger.info('Inputs: %s', inputs)
        master_csv_output_rows = []
        for input_row in inputs:
            try:
                input_row.fetch_file(options.workdir)
                accounting_policies = input_row.get_accounting_policies()
                output_csv_file_name = os.path.abspath(os.path.join(
                    options.outputdir, input_row.id + ".csv"))
                output_rows = [policy.get_output_row() for policy in
                               accounting_policies]
                output_csv = OutputCSV(output_csv_file_name, output_rows)
                output_csv.write()
                master_csv_output_rows.extend(output_rows)
            except Exception as e:
                logger.error('Exception during processing of %s: %s',
                             input_row, e, exc_info=1)
        master_csv_file_name = os.path.abspath(os.path.join(
            options.outputdir, 'master.csv'))
        logger.info('Writing master csv to %s', master_csv_file_name)
        try:
            master_csv = OutputCSV(
                master_csv_file_name, master_csv_output_rows)
            master_csv.write()
        except Exception as e:
            logger.error('Exception during processing of %s: %s',
                         master_csv_file_name, e, exc_info=1)
    logger.info('All done.')


if __name__ == '__main__':
    main()
