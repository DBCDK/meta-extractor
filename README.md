# meta-extractor
This project contains a description for how we pretrained a gemma3 model for metadata extraction from PDFs and how to use it in a microservice to convert PDFs to MARC records.

## Pretraining the Gemma3 Model
To pretrain the Gemma3 model for metadata extraction, follow these steps:

### 1. **Data Collection**: Gather a diverse dataset of PDFs along with their corresponding metadata in JSON format.
We cannot provide the real examples but see examples of synthetic data under `meta_extractor/training-gemma3/example-data`.

Example naming: example-\<no>.json 

We gathered 10.000 examples of public articles in PDF format along with their metadata in JSON format.
We had the metadata in MARC format and converted it into a simple JSON format. Script not provided. 

### 2. **Data Preprocessing**: Convert the PDFs into text. 

We used the library PyMuPDF for this purpose. See the script `src/meta_extractor/training-gemma3/pdf2text.py`

See synthetic examples of extracted text files under `meta_extractor/training-gemma3/example-data`.

Example naming: example-\<no>.txt

You can extract text from PDFs using the following script:

`pip install -e .`

`pdf2text -i path/to/pdfs -o path/to/output/texts [-s/--short]`

Where 
-i is the input folder with pdfs, 

-o is the output folder where the extracted text from the pdfs will be stored.

-o|--short is for extracting a shorter version of the text where we only look at the first 3 pages instead of the first 13 pages.

We always extract the last two pages of the text. 

The script assumes that pdf files are named filename.pdf, and will output a corresponding filename.txt

### 3. Divide data into training, validation and test sets
To divide the data into training, validation and test sets use the script
`train-test-val -t data/texts/ -m data/metadata/`
or
`train-test-val -t /data/meta-extractor/text/longer/ -m /data/meta-extractor/metadata/`


Where 
-t is the folder with the extracted texts from pdfs, 
-m is the folder with the json metadata with either English or Danish key names, assuming the json are named pid.json for English and pid_dan.json for danish.
--train is the train ratio (default: 0.8)
--val is the val ratio (default: 0.1)
--test is the test ratio (default: 0.1)
--seed is the random seed (default: 42)
--move will move the files into the created folders instead of copying them if added.

The script will create three folders in the texts and metadata folders named train, val and test and copy the files into these folders.
