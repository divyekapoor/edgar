# Edgar
Converting and Extracting Summary of Statement of Accounts from Edgar Online XSLX files.

# Requirements

This code requires Python 3 (tested Python 3.6.5) and certain third party modules (listed in requirements.txt).

# Capabilities

   ```sh
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



        Options:
          -h, --help            show this help message and exit
          -i INPUT, --input=INPUT
                                CSV file that provides an ID and an Edgar URL to fetch
                                financial information for companies.
          -o OUTPUTDIR, --outputdir=OUTPUTDIR
                                Output directory where Summary of Accounting policies
                                will be extracted.
          -w WORKDIR, --workdir=WORKDIR
                                The working directory to use for saving downloaded
                                XLSX files.

   ```

# How to run

From Zip file distributable:

   ```sh
   $ unzip edgar.zip
   $ cd edgar
   $ python3 edgar.py -h
   ```

On Windows, change the last step to:
   ```sh
   $ %LOCALAPPDATA%\Programs\Python\Python36\python.exe edgar.py -h
   ```

## Sample inputs

Running on sample input data:

   ```sh
   $ python3 edgar.py -i samples/input.txt -o samples/output -w samples/workdir
   ```


# Developer Instructions: How to build

## Linux (Ubuntu Zesty)

   ```sh
   $ git clone https://github.com/divyekapoor/edgar
   $ cd edgar
   $ python3 -m venv venv
   $ source venv/bin/activate
   $ pip3 -r requirements.txt
   $ ./edgar.py -h
   ```

All these steps have to be done once. Subsequent runs require only the following:

   ```sh
   $ cd edgar
   $ source venv/bin/activate
   $ python edgar.py -h
   ```

To build the zip file used for windows distribution, please run:

   ```sh
   $ make
   ```

To clean up,
   ```sh
   $ make clean
   ```

## Windows

For Windows, we require the latest version of Python 3 and Git installed on the system.
Please download them from <https://www.python.org/downloads/windows/> and <https://git-scm.com/download/win>


