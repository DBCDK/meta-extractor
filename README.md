# meta-extractor
This project contains a description for how we pretrained a gemma3 model for metadata extraction from Danish PDFs and how to use it in a microservice to convert PDFs to Danish danMARC records.

The following is a description of how you might reproduce our results. We have tried to provide scripts and synthetic data examples to help you with this.

You will in our code see remnants of paths we went down during development. An example of this is that we tried a version with metadata 

tags in Danish or in English. We ended up using only English tags for the final model, as it performed just as well as the Danish version.

## Pretraining the Gemma3 Model
To pretrain the Gemma3 model for metadata extraction, follow these steps:

### 0. **Setup Environment**:
Ensure you have the necessary environment set up with required libraries. You can use the provided `requirements-training.txt` file to install dependencies.

### 1. **Data Collection**: 
Gather a diverse dataset of PDFs along with their corresponding metadata in JSON format.

We cannot provide the real examples but see examples of synthetic data under `meta_extractor/training-gemma3/example-data`.

Example naming: example-\<no>.json 

We gathered 10.000 examples of public articles in PDF format along with their metadata in JSON format.
We had the metadata in MARC format and converted it into a simple JSON format. 

You can see the json-schema for the metadata under `src/meta_extractor/training-gemma3/metadata-schema.json` 

### 2. **Data Preprocessing**: 
Convert the PDFs into text. 

We used the library PyMuPDF for this purpose. See the script `src/meta_extractor/training-gemma3/pdf2text.py`

See synthetic examples of extracted text files under `meta_extractor/training-gemma3/example-data`.

Example naming: example-\<no>.txt

You can extract text from PDFs using the following script:

`pip install -e .`

`pdf2text -i path/to/pdfs -o path/to/texts [-s/--short]`

Where 
-i is the input folder with pdfs, 

-o is the output folder where the extracted text from the pdfs will be stored.

-s|--short is for extracting a shorter version of the text where we only look at the first 3 pages instead of the first 13 pages.

We always extract the last two pages of the text. 

The script assumes that pdf files are named filename.pdf, and will output a corresponding filename.txt

### 3. **Splitting data set** 
Divide data into training, validation and test sets

Remember to split your data into training, validation and possible also test sets. 


### 4. **Build prompt-answers pairs**: 
Create prompt-answer pairs for training and validation the model.

To build the prompt conversations for training you can use the script.

`build_prompt -t path/to/texts -m path/to/metadata/ -p src/meta_extractor/data/prompt_production.json -o conversations.jsonl`

Where
-t is the folder with the extracted texts from pdfs,
-m is the folder with the json metadata files,
-p is the path to the prompt you want to use
-o is the path to the output file that will be saved with the conversations

e.g. 
`build_prompt -t src/meta_extractor/training_gemma3/example-data/texts/train/ -m src/meta_extractor/training_gemma3/example-data/metadata/train/ -p src/meta_extractor/data/prompt_production.json -o conversations_train.jsonl`
or
`build_prompt -t src/meta-extractor/example-data/texts/test -m src/meta-extractor/example-data/metadata/test -p src/meta_extractor/data/prompt_production.json -o conversations_test.jsonl`


### 5. **Model Training**: Use the Gemma3 model architecture and fine-tune it on your dataset.


