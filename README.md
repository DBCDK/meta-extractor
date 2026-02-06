# meta-extractor
This project contains a description for how we pretrained a gemma3 model for metadata extraction from Danish PDFs and how to use it in a microservice to convert PDFs to Danish danMARC records.

The following is a description of how you might reproduce our results. We have tried to provide scripts and synthetic data examples to help you with this.

You will in our code see remnants of paths we went down during development. An example of this is that we tried a version with metadata keys in Danish or in English. We ended up using only English keys for the final model, as it performed just as well as the Danish version.

Table of contents:
- [Pretraining the Gemma3 Model](#pretraining-the-gemma3-model)
  - [0. Setup Environment](#0-setup-environment)
  - [1. Data Collection](#1-data-collection)
  - [2. Data Preprocessing](#2-data-preprocessing)
  - [3. Splitting data set](#3-splitting-data-set)
  - [4. Build prompt-answers pairs](#4-build-prompt-answers-pairs)
  - [5. Model Training](#5-model-training)
  - [6. Model Evaluation](#6-model-evaluation)
- [Evaluation Results](#evaluation-results)
- [Published model on huggingface](#published-model-on-huggingface)

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

You can try it out on the one sample pdf we have provided under `src/meta_extractor/training-gemma3/example-data/pdfs/example-11.pdf`


### 3. **Splitting data set** 
Divide data into training, validation and test sets

Remember to split your data into training, test and possible also validation sets. 


### 4. **Build prompt-answers pairs**: 
Create prompt-answer pairs for training and testing the model.

To build the prompt conversations for training you can use the script.

`build_prompt -t path/to/texts -m path/to/metadata/ -p src/meta_extractor/data/prompt_production.json -o conversations.jsonl`

Where
-t is the folder with the extracted texts from pdfs,
-m is the folder with the json metadata files,
-p is the path to the prompt you want to use
-o is the path to the output file where the conversations will be saved (one pr row)

e.g. for training data you can run:
`build_prompt -t src/meta_extractor/training_gemma3/example-data/texts/train/ -m src/meta_extractor/training_gemma3/example-data/metadata/train/ -p src/meta_extractor/data/prompt_production.json -o conversations_train.jsonl`
or for test data you can run:
`build_prompt -t src/meta-extractor/example-data/texts/test -m src/meta-extractor/example-data/metadata/test -p src/meta_extractor/data/prompt_production.json -o conversations_test.jsonl`


### 5. **Model Training**: Use the Gemma3 model architecture and fine-tune it on your dataset.

To train the model, you can use the Axolotl library.
`CUDA_VISIBLE_DEVICES=0,1 axolotl train finetuning_config_gemma3.yml`

The command assumes you have 2 GPUs available and only use GPUs 0 and 1. Change the command to fit your setup.

The finetuning_config_gemma3.yml file contains the configuration for training the model. You can change the parameters in the file to fit your needs.
Make sure to change the paths to the conversations file and the output folder for the model in **finetuning_config_gemma3.yml**.

The default output folder is usually `./outputs/out/` and the model will be saved in a subfolder named checkpoint-xx where xx is the number of training steps.

You can then point to this checkpoint folder when evaluating the model.

### 6. **Model Evaluation**: Evaluate the model's performance on a test set.

After finetuning the model, you can evaluate it using the test conversations file created earlier.

We recommend using a different python environment for evaluating the model.
Requirements for evaluation are listed in the `requirements-eval.txt` file located in the root of the repository.

We have created a command for evaluating the model called `test-and-eval`.

You can either evaluate a model on a set of test conversations and get analysis of the results from this test set
or you can just get the analysis based on a previously saved results file.

To evaluate a model on a set of conversations run the following command:

`test-and-eval /path/to/trained-model/ /path/to/results-dir file-prefix-name -c /path/to/conversations.jsonl`
For example:
`test-and-eval ./outputs/out/checkpoint-25 data/results/ test-run-1 -c conversations_test.jsonl`

The output will be saved in the results directory under different files starting with the file-prefix-name provided.

The following files will be created:
```
test-run-1.rapport.txt
test-run-1.results.jsonl
```

Because we wanted to check how much the model output deviated from the provided text (how much did it hallucinate) from the pdf we also created a validation step. 

Normalized values in the model output that were not found in the original text (also normalized) were removed.  

The validated results are saved in the file:
`test-run-1.validated_results.jsonl`

If you provide the -j flag you will also get generated json for each test example:
```
test-run-1.validated_generated.jsonl
test-run-1.generated.jsonl
```

If you already have a results file and just want to get the analysis you can run the following command:

`test-and-eval /path/to/trained-model/ /path/to/results-dir file-prefix-name -e`

## Evaluation Results
Using the above method we trained a Gemma3 model on about 9.000 examples and evaluated it on 990 test examples which had 10.890 different metadata fields.
The following results cover pair-wise comparisons of these 10.890 fields.


```

########################################
Evaluation results:
########################################
TP= True Positives - The model output matches the ground truth.
FP= False Positives - The model output contains values not present in the ground truth (hallucinations).
FN= False Negatives - The model fails to output values present in the ground truth (but maybe the value wasn't extracted correctly from the original pdf).
TN= True Negatives - The model correctly does not output values that are not present in the ground truth.
Hallucinations= Number of hallucinations for the specific field.

Hallucinations are counted per metadata field: If a prediction for a field contains any extra (incorrect) value(s), it counts as one hallucination for that field, regardless of how many extra values there are.
False Positives are counted per value: Every extra, incorrect value is counted as a separate FP.
Example:
If a single prediction for a field has 3 extra publishers (all wrong), it counts as 3 FPs but only 1 hallucination.

-------------------EXACT MATCH-------------------
Overall accuracy: 82.26% (8958/10890)
Total hallucinations: 1442 | TP=6703 FP=1601 FN=1487 TN=3190
Micro P/R/F1: P=80.72% R=81.84% F1=81.28%
TITLE accuracy: 76.16% (754/990) | TP=754 FP=231 FN=5, TN=0 | P=76.55% R=99.34% F1=86.47% | Hallucinations=231
SUBTITLE accuracy: 71.01% (703/990) | TP=404 FP=231 FN=56, TN=299 | P=63.62% R=87.83% F1=73.79% | Hallucinations=231
PUBLICATION_YEAR accuracy: 94.24% (933/990) | TP=933 FP=52 FN=5, TN=0 | P=94.72% R=99.47% F1=97.04% | Hallucinations=52
LANGUAGE_AS_ISO639-2 accuracy: 98.18% (972/990) | TP=972 FP=13 FN=5, TN=0 | P=98.68% R=99.49% F1=99.08% | Hallucinations=13
IDENTIFIERS.ISBN accuracy: 81.31% (805/990) | TP=569 FP=140 FN=45, TN=236 | P=80.25% R=92.67% F1=86.02% | Hallucinations=140
PUBLISHER accuracy: 72.73% (720/990) | TP=800 FP=243 FN=282, TN=0 | P=76.70% R=73.94% F1=75.29% | Hallucinations=238
CREATOR_PERSONS accuracy: 68.99% (683/990) | TP=998 FP=288 FN=471, TN=280 | P=77.60% R=67.94% F1=72.45% | Hallucinations=177
CREATOR_CORPORATIONS accuracy: 60.10% (595/990) | TP=809 FP=341 FN=456, TN=37 | P=70.35% R=63.95% F1=67.00% | Hallucinations=300
COUNTRY_OF_PUBLICATION_ISO639-1 accuracy: 99.70% (987/990) | TP=0 FP=0 FN=4, TN=987 | P=— R=0.00% F1=— | Hallucinations=0
SERIES accuracy: 88.89% (880/990) | TP=289 FP=34 FN=101, TN=600 | P=89.47% R=74.10% F1=81.07% | Hallucinations=33
SERIES_NUMBER accuracy: 93.54% (926/990) | TP=175 FP=28 FN=57, TN=751 | P=86.21% R=75.43% F1=80.46% | Hallucinations=27
-------------------LEVENSHTEIN DISTANCE-------------------
Overall average Levenshtein distance: 5.42
Overall average Levenshtein ratio: 0.90
TITLE: Average Levenshtein distance: 5.90, ratio: 0.92
SUBTITLE: Average Levenshtein distance: 12.03, ratio: 0.82
PUBLICATION_YEAR: Average Levenshtein distance: 0.08, ratio: 0.98
LANGUAGE_AS_ISO639-2: Average Levenshtein distance: 0.06, ratio: 0.99
IDENTIFIERS.ISBN: Average Levenshtein distance: 1.94, ratio: 0.85
PUBLISHER: Average Levenshtein distance: 7.57, ratio: 0.86
CREATOR_PERSONS: Average Levenshtein distance: 13.84, ratio: 0.86
CREATOR_CORPORATIONS: Average Levenshtein distance: 14.05, ratio: 0.82
COUNTRY_OF_PUBLICATION_ISO639-1: Average Levenshtein distance: 0.01, ratio: 1.00
SERIES: Average Levenshtein distance: 3.69, ratio: 0.90
SERIES_NUMBER: Average Levenshtein distance: 0.43, ratio: 0.95

```

As mentioned we also validated the results to see how many of the predicted values were actually found in the original text extracted from the pdf.
The results after validation were as follows:

```
########################################
Evaluation results:
(After validation against source text)
########################################
-------------------EXACT MATCH-------------------
Overall accuracy: 79.82% (8692/10890)
Total hallucinations: 1166 | TP=6344 FP=1297 FN=1964 TN=3230

Micro P/R/F1: P=83.03% R=76.36% F1=79.55%

TITLE accuracy: 73.94% (732/990) | TP=732 FP=188 FN=70, TN=0 | P=79.57% R=91.27% F1=85.02% | Hallucinations=188
SUBTITLE accuracy: 67.78% (671/990) | TP=359 FP=162 FN=157, TN=312 | P=68.91% R=69.57% F1=69.24% | Hallucinations=162
PUBLICATION_YEAR accuracy: 93.64% (927/990) | TP=927 FP=51 FN=12, TN=0 | P=94.79% R=98.72% F1=96.71% | Hallucinations=51
LANGUAGE_AS_ISO639-2 accuracy: 98.18% (972/990) | TP=972 FP=13 FN=5, TN=0 | P=98.68% R=99.49% F1=99.08% | Hallucinations=13
IDENTIFIERS.ISBN accuracy: 80.91% (801/990) | TP=558 FP=115 FN=74, TN=243 | P=82.91% R=88.29% F1=85.52% | Hallucinations=115
PUBLISHER accuracy: 70.71% (700/990) | TP=778 FP=206 FN=304, TN=0 | P=79.07% R=71.90% F1=75.31% | Hallucinations=201
CREATOR_PERSONS accuracy: 68.99% (683/990) | TP=995 FP=265 FN=474, TN=280 | P=78.97% R=67.73% F1=72.92% | Hallucinations=165
CREATOR_CORPORATIONS accuracy: 48.18% (477/990) | TP=631 FP=245 FN=634, TN=52 | P=72.03% R=49.88% F1=58.94% | Hallucinations=220
COUNTRY_OF_PUBLICATION_ISO639-1 accuracy: 99.70% (987/990) | TP=0 FP=0 FN=4, TN=987 | P=— R=0.00% F1=— | Hallucinations=0
SERIES accuracy: 83.23% (824/990) | TP=226 FP=27 FN=164, TN=604 | P=89.33% R=57.95% F1=70.30% | Hallucinations=27
SERIES_NUMBER accuracy: 92.73% (918/990) | TP=166 FP=25 FN=66, TN=752 | P=86.91% R=71.55% F1=78.49% | Hallucinations=24

-------------------LEVENSHTEIN DISTANCE-------------------
Overall average Levenshtein distance: 7.02
Overall average Levenshtein ratio: 0.87

TITLE: Average Levenshtein distance: 8.72, ratio: 0.86
SUBTITLE: Average Levenshtein distance: 17.53, ratio: 0.74
PUBLICATION_YEAR: Average Levenshtein distance: 0.11, ratio: 0.97
LANGUAGE_AS_ISO639-2: Average Levenshtein distance: 0.06, ratio: 0.99
IDENTIFIERS.ISBN: Average Levenshtein distance: 2.17, ratio: 0.83
PUBLISHER: Average Levenshtein distance: 8.21, ratio: 0.83
CREATOR_PERSONS: Average Levenshtein distance: 14.11, ratio: 0.85
CREATOR_CORPORATIONS: Average Levenshtein distance: 20.26, ratio: 0.67
COUNTRY_OF_PUBLICATION_ISO639-1: Average Levenshtein distance: 0.01, ratio: 1.00
SERIES: Average Levenshtein distance: 5.52, ratio: 0.84
SERIES_NUMBER: Average Levenshtein distance: 0.53, ratio: 0.94
```

The precision and recall for these two evaluations can be compared to see how much the validation affected the results.
```
 Precision before validation: 80.72% , after validation: 83.03%
 Recall before validation: 81.84% , after validation: 76.36%
```
A manuel inspection of some of the hallucinations showed that some of them were actually correct, but the values were not found in the extracted text from the pdf.
The expected metadata also sometimes contained translated values that were not present in the original text, which were removed during validation.

So the validation step is quite strict and might remove some correct values.

## Published model on huggingface
The model we pretrained is published on Huggingface and can be found here: 

https://huggingface.co/DBCDigital/gemma-3-4b-it_qlora_pdf_metadata_extractor