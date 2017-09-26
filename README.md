# Edgar
Most companies that file financial reporting documents in the US have an XSLX file
on Edgar Online that details its financial statements as filed with the SEC. These
financial statements also include a summary of accounting policies used to determine
how and where money / assets will be recorded in their financial statements.

The edgar script extracts the "Summary of Accounting Policies" from Edgar Online XSLX files.
Examples can be found in the samples/ and examples/ directories.

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

## Handling .xls files

The following need to be installed to handle .xls files in addition to .xlsx files (supported only on Windows):

  * The Office Compatibility Pack <http://go.microsoft.com/fwlink/p/?LinkID=77512>
  * The Office Migration Planning Manager <https://www.microsoft.com/en-us/download/details.aspx?id=11454>


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
edgar.zip will be built in the build/ directory.

To clean up,
   ```sh
   $ make clean
   ```

## Windows

For Windows, we require the latest version of Python 3 and Git installed on the system.
Please download them from <https://www.python.org/downloads/windows/> and <https://git-scm.com/download/win>

It should be possible to build and run the code on Windows as well with Git + Python + Make installed, 
but this has not been verified.

# Release Instructions

## Linux

The best way to release a new piece of code is to call
```make release``` and a release will be created and tagged. To push the
release, use ```git push --tags```

Dependencies:
<https://github.com/flazz/semver> for semantic version management.