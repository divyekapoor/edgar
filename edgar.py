#!/usr/bin/env python3
import csv
import requests
import logging
import sys
import os
import gflags
import openpyxl
from logging import INFO, ERROR, WARN, WARNING
from optparse import OptionParser

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
        
        """

logger = logging.getLogger('main')

def usage():
    print(USAGE)
    sys.stdout.flush()


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
    os.makedirs(options.workdir)

    with open(options.input, 'r') as input_csv:
        reader = csv.DictReader(input_csv)
        inputs = [InputRow(record['ID'], record['URL']) for record in reader]
        logger.info('Inputs: %s', inputs)
        for input in inputs:
            input.fetch_file(options.workdir)



if __name__ == '__main__':
    main()
