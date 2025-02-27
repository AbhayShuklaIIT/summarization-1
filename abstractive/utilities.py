import glob
from nltk import tokenize
import nltk
import transformers
from torch.utils.data import DataLoader, TensorDataset, random_split, RandomSampler, Dataset
import pandas as pd
import numpy as np
import torch.nn.functional as F
import pytorch_lightning as pl
import torch
from pytorch_lightning.callbacks import ModelCheckpoint

def get_summary_data(dataset, train):
    '''
    function to get names, documents, and summaries

    change the path variable to the path of the dataset
    '''
    if dataset == "N2":
        path = '../Datasets/N2/Full-Text/India'
        all_files = glob.glob(path + "/*.txt")

        data_source = []
        names = []
        for filename in all_files:
            with open(filename, 'r') as f: 
                p = filename.rfind("/")
#                 print(filename[p+1:])
                names.append(filename[p+1:])
                a = f.read()
                data_source.append(a)
        return names, data_source, []
    
    path = '../Datasets/Summary-Data-' + dataset + '/' + train + '-data/judgement'
    all_files = glob.glob(path + "/*.txt")
    data_source = []
    names = []
    for filename in all_files:
        with open(filename, 'r') as f:
            p = filename.rfind("/")
            names.append(filename[p+1:])
            a = f.read()
            data_source.append(a)
    path = '../Datasets/Summary-Data-' + dataset + '/' + train + '-data/summary'
    all_files = glob.glob(path + "/*.txt")
    data_summary = []
    for filename in all_files:
        with open(filename, 'r') as f: 
            a = f.read()
            l = len(a)
            data_summary.append(a)
            
    return names, data_source, data_summary

def get_summary_data_rhet_train(dataset):
    '''
    function to get names, documents, and summaries for Rhetorical labeled documents - train

    change the path variable to the path of the Rhetorical labeled dataset
    '''
    path = '../Datasets/rhet/' + dataset.lower() + '_ft_rhet' # use your path
    all_files = glob.glob(path + "/*.txt")

    data_source = []
    names = []
    for filename in all_files:
        with open(filename, 'r') as f: 
            p = filename.rfind("/")
            names.append(filename[p+1:])
            a = f.read()
            data_source.append(a)

    path = '../Datasets/rhet/RhetSumm_Dataset/raw_files/'+ dataset +'/summary' # use your path
    all_files = glob.glob(path + "/*.txt")

    data_summary = {}
    for filename in all_files:
        with open(filename, 'r') as f: 
            p = filename.rfind("/")
            a = f.read()
            l = len(a)
            data_summary[filename[p+1:]] = (a)
    return names, data_source, data_summary

def get_summary_data_rhet_test(dataset):
    '''
    function to get names, documents, and summaries for Rhetorical labeled documents - test

    change the path variable to the path of the Rhetorical labeled dataset
    '''
    path = '../Datasets/rhet/RhetSumm_Dataset/rhet/' + dataset + "/" # use your path
    all_files = glob.glob(path + "/*.txt")

    data_source = []
    names = []
    for filename in all_files:
        with open(filename, 'r') as f: 
            p = filename.rfind("/")
#             print(filename[p+1:])
            names.append(filename[p+1:])
            a = f.read()
            data_source.append(a)

    return names, data_source


def get_req_len_dict(dataset, istrain):
    '''
    function to required length data for each summary

    change the path variable to the path to Summary_Length_India.txt/ Summary_Length_Uk.txt file
    '''
    
    if dataset == "N2":
        f = open("../Datasets/N2/Summary_Length_India.txt", "r")
        a = (f.read())
        a = a.split("\n")
        dict_names = {}
        for i in a:
            b = i.split("	")
            dict_names[b[0] + ".txt"] = int(b[1])
        return dict_names 
    
    f = open("../Datasets/Summary-Data-"+ dataset +"/length-file-" + istrain +".txt", "r")
    a = (f.read())
    a = a.split("\n")
    dict_names = {}
    for i in a:
        b = i.split("	")
        try:
            tp = int(b[2])
            dict_names[b[0]] = tp
        except:
            print(b)
    return dict_names  

def split_to_sentences(para):
    sents = nltk.sent_tokenize(para)
    return sents

def nest_sentencesV2(document,chunk_length):
    '''
    function to chunk a document
    input:  document           - Input document
            chunk_length        - chunk length
    output: list of chunks. Each chunk is a list of sentences.
    '''
    nested = []
    sent = []
    length = 0
    for sentence in nltk.sent_tokenize(document):
        length += len(sentence.split(" "))
        if length < chunk_length:
            sent.append(sentence)
        else:
            nested.append(sent)
            sent = []
            sent.append(sentence)
            length = 0
    if len(sent)>0:
        nested.append(sent)
    return nested

def nest_sentencesMV2(document_sents,chunk_length):
    '''
    function to chunk a document
    input:  doc_sents           - Input document sentences
            chunk_length        - chunk length
    output: list of chunks. Each chunk is a list of sentences.
    '''
    nested = []
    sent = []
    length = 0
    #modeified v2
    
    for sentence in document_sents:
        length += len((sentence.split(" ")))
        if length < chunk_length:
            sent.append(sentence)
        else:
            nested.append(sent)
            sent = []
            sent.append(sentence)
            length = 0
    if len(sent)>0:
        nested.append(sent)
    return nested

def nest_sentences(document,chunk_length):
    '''
    function to chunk a document
    input:  document           - Input document
            chunk_length        - chunk length
    output: list of chunks. Each chunk is a string.
    '''
    nested = []
    sent = []
    length = 0
    for sentence in nltk.sent_tokenize(document):
        length += len(sentence.split(" "))
        if length < chunk_length:
            sent.append(sentence)
        else:
            nested.append(" ".join(sent))
            sent = []
            sent.append(sentence)
            length = 0
    if len(sent)>0:
        nested.append(" ".join(sent))
    return nested
  

def nest_sentencesV3(doc_sents,chunk_length, dict_sents_labels):
    '''
    function to first segment the document using rhetorical roles and then chunk if required
    input:  doc_sents           - Input document sentences
            chunk_length        - chunk length
            dict_sents_labels   - dictionary for every sentence and label
    output: list of chunks
    '''
    s = list(set(dict_sents_labels.values()))
#     print(s)
    all_chunks = []
    
    for label in s:
        doc_sents_withlabels = []
        for sent in doc_sents:
            if sent == '':continue
            if dict_sents_labels[sent] == label:
                doc_sents_withlabels.append(sent)
        chunks = nest_sentencesMV2(doc_sents_withlabels, chunk_length)
        
        edited_chunks = []
        for chunk in chunks:
            edited_chunks.append(["<" + label + ">"] + chunk)
        
        all_chunks = all_chunks + edited_chunks

    return all_chunks   

def get_doc_sens_and_labels(doc):
    '''
    Function to read a Rhetorically labeled document.
    returns a list of sentences, the label of each sentence, dictionary: keys-sentences, values-labels
    '''
    sents = []
    labels = []
    dict_sents_labels = {}
    ss = doc.split("\n")
    for i in ss:
        try:
            spt = i.split("\t")
            sents.append(spt[0])
            labels.append(spt[1])
            dict_sents_labels[spt[0]] = spt[1] 
        except:
            pass
    return sents, labels, dict_sents_labels

#Source - https://colab.research.google.com/drive/1Cy27V-7qqYatqMA7fEqG2kgMySZXw9I4?usp=sharing&pli=1
class LitModel(pl.LightningModule):
  # Instantiate the model
  def __init__(self, learning_rate, tokenizer, model):
    super().__init__()
    self.tokenizer = tokenizer
    self.model = model
    self.learning_rate = learning_rate
    # self.freeze_encoder = freeze_encoder
    # self.freeze_embeds_ = freeze_embeds
#     self.hparams = argparse.Namespace()

    self.hparams.freeze_encoder = True
    self.hparams.freeze_embeds = True
    self.hparams.eval_beams = 4
    # self.hparams = hparams

    if self.hparams.freeze_encoder:
      freeze_params(self.model.get_encoder())

    if self.hparams.freeze_embeds:
      self.freeze_embeds()
  
  def freeze_embeds(self):
    ''' freeze the positional embedding parameters of the model; adapted from finetune.py '''
    freeze_params(self.model.model.shared)
    for d in [self.model.model.encoder, self.model.model.decoder]:
      freeze_params(d.embed_positions)
      freeze_params(d.embed_tokens)

  # Do a forward pass through the model
  def forward(self, input_ids, **kwargs):
    return self.model(input_ids, **kwargs)
  
  def configure_optimizers(self):
    optimizer = torch.optim.Adam(self.parameters(), lr = self.learning_rate)
    return optimizer

  def training_step(self, batch, batch_idx):
    # Load the data into variables
    src_ids, src_mask = batch[0], batch[1]
    tgt_ids = batch[2]
    # Shift the decoder tokens right (but NOT the tgt_ids)
    decoder_input_ids = shift_tokens_right(tgt_ids, self.tokenizer.pad_token_id)

    # Run the model and get the logits
    outputs = self(src_ids, attention_mask=src_mask, decoder_input_ids=decoder_input_ids, use_cache=False)
    lm_logits = outputs[0]
    # Create the loss function
    ce_loss_fct = torch.nn.CrossEntropyLoss(ignore_index=self.tokenizer.pad_token_id)
    # Calculate the loss on the un-shifted tokens
    loss = ce_loss_fct(lm_logits.view(-1, lm_logits.shape[-1]), tgt_ids.view(-1))

    return {'loss':loss}

  def validation_step(self, batch, batch_idx):

    src_ids, src_mask = batch[0], batch[1]
    tgt_ids = batch[2]

    decoder_input_ids = shift_tokens_right(tgt_ids, self.tokenizer.pad_token_id)
    
    # Run the model and get the logits
    outputs = self(src_ids, attention_mask=src_mask, decoder_input_ids=decoder_input_ids, use_cache=False)
    lm_logits = outputs[0]

    ce_loss_fct = torch.nn.CrossEntropyLoss(ignore_index=self.tokenizer.pad_token_id)
    val_loss = ce_loss_fct(lm_logits.view(-1, lm_logits.shape[-1]), tgt_ids.view(-1))

    return {'loss': val_loss}
  
  # Method that generates text using the BartForConditionalGeneration's generate() method
  def generate_text(self, text, eval_beams, early_stopping = True, max_len = 1024):
    ''' Function to generate text '''
    generated_ids = self.model.generate(
        text["input_ids"],
        attention_mask=text["attention_mask"],
        use_cache=True,
        decoder_start_token_id = self.tokenizer.pad_token_id,
        num_beams= eval_beams,
        max_length = max_len,
        early_stopping = early_stopping
    )
    return [self.tokenizer.decode(w, skip_special_tokens=True, clean_up_tokenization_spaces=True) for w in generated_ids]

def freeze_params(model):
  ''' Function that takes a model as input (or part of a model) and freezes the layers for faster training
      adapted from finetune.py '''
  for layer in model.parameters():
    layer.requires_grade = False


# Create a dataloading module as per the PyTorch Lightning Docs
class SummaryDataModule(pl.LightningDataModule):
  def __init__(self, tokenizer, df, batch_size):
    super().__init__()
    self.tokenizer = tokenizer
    self.batch_size = batch_size
    self.data = df
     
  # Loads and splits the data into training, validation and test sets with a 60/20/20 split
  def prepare_data(self):
    self.train, self.validate, self.test = np.split(self.data.sample(frac=1), [int(.6*len(self.data)), int(.8*len(self.data))])

  # encode the sentences using the tokenizer  
  def setup(self, stage):
    self.train = encode_sentences(self.tokenizer, self.train['source'], self.train['target'])
    self.validate = encode_sentences(self.tokenizer, self.validate['source'], self.validate['target'])
    self.test = encode_sentences(self.tokenizer, self.test['source'], self.test['target'])

  # Load the training, validation and test sets in Pytorch Dataset objects
  def train_dataloader(self):
    dataset = TensorDataset(self.train['input_ids'], self.train['attention_mask'], self.train['labels'])                          
    train_data = DataLoader(dataset, sampler = RandomSampler(dataset), batch_size = self.batch_size)
    return train_data

  def val_dataloader(self):
    dataset = TensorDataset(self.validate['input_ids'], self.validate['attention_mask'], self.validate['labels']) 
    val_data = DataLoader(dataset, batch_size = self.batch_size)                       
    return val_data

  def test_dataloader(self):
    dataset = TensorDataset(self.test['input_ids'], self.test['attention_mask'], self.test['labels']) 
    test_data = DataLoader(dataset, batch_size = self.batch_size)                   
    return test_data



def shift_tokens_right(input_ids, pad_token_id):
  """ Shift input ids one token to the right, and wrap the last non pad token (usually <eos>).
      This is taken directly from modeling_bart.py
  """
  prev_output_tokens = input_ids.clone()
  index_of_eos = (input_ids.ne(pad_token_id).sum(dim=1) - 1).unsqueeze(-1)
  prev_output_tokens[:, 0] = input_ids.gather(1, index_of_eos).squeeze()
  prev_output_tokens[:, 1:] = input_ids[:, :-1]
  return prev_output_tokens

def encode_sentences(tokenizer, source_sentences, target_sentences, max_length=1024, min_length = 512, pad_to_max_length=True, return_tensors="pt"):
  ''' Function that tokenizes a sentence 
      Args: tokenizer - the BART tokenizer; source and target sentences are the source and target sentences
      Returns: Dictionary with keys: input_ids, attention_mask, target_ids
  '''

  input_ids = []
  attention_masks = []
  target_ids = []
  tokenized_sentences = {}

  for sentence in source_sentences:
    encoded_dict = tokenizer(
          sentence,
          max_length=max_length,
          padding="max_length" if pad_to_max_length else None,
          truncation=True,
          return_tensors=return_tensors,
          add_prefix_space = True
      )

    input_ids.append(encoded_dict['input_ids'])
    attention_masks.append(encoded_dict['attention_mask'])

  input_ids = torch.cat(input_ids, dim = 0)
  attention_masks = torch.cat(attention_masks, dim = 0)

  for sentence in target_sentences:
    encoded_dict = tokenizer(
          sentence,
          max_length=min_length,
          padding="max_length" if pad_to_max_length else None,
          truncation=True,
          return_tensors=return_tensors,
          add_prefix_space = True
      )
    # Shift the target ids to the right
    # shifted_target_ids = shift_tokens_right(encoded_dict['input_ids'], tokenizer.pad_token_id)
    target_ids.append(encoded_dict['input_ids'])

  target_ids = torch.cat(target_ids, dim = 0)
  

  batch = {
      "input_ids": input_ids,
      "attention_mask": attention_masks,
      "labels": target_ids,
  }

  return batch
