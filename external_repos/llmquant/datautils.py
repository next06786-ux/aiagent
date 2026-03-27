import random
import sys
import asyncio

import numpy as np
import torch
from datasets import load_dataset, DownloadConfig
from transformers import AutoTokenizer, LlamaTokenizer
import os

# Import for network error handling
try:
    from aiohttp.client_exceptions import ConnectionTimeoutError
except ImportError:
    # Fallback if aiohttp is not available
    ConnectionTimeoutError = Exception


def set_seed(seed):
    np.random.seed(seed)
    torch.random.manual_seed(seed)

'''
Generate tokenizer and return it to preload datasets by converting them to embedded vectors instead of natural words
'''
def get_tokenizer(model):
    # ⭐ 使用 AutoTokenizer 自动适配 Llama 2/3/3.1 及其他模型
    tokenizer = AutoTokenizer.from_pretrained(model, use_fast=False)
    
    # ⭐ 只对 Llama 2 修复 token ID（Llama 3.1 token 已正确配置）
    if "llama" in model.lower():
        # Llama 2: bos=1, eos=2
        # Llama 3/3.1: bos=128000, eos=128001（新 tokenizer）
        if tokenizer.bos_token_id not in [1, 128000]:
            try:
                tokenizer.bos_token_id = 1
                tokenizer.eos_token_id = 2
            except AttributeError:
                pass
    
    return tokenizer


def get_wikitext2(nsamples, seed, seqlen, model, tokenizer):
    traindata = load_dataset('wikitext', 'wikitext-2-raw-v1', split='train')
    testdata = load_dataset('wikitext', 'wikitext-2-raw-v1', split='test')

    trainenc = tokenizer(' '.join(traindata['text']), return_tensors='pt')
    testenc = tokenizer('\n\n'.join(testdata['text']), return_tensors='pt')

    random.seed(seed)
    trainloader = []
    for _ in range(nsamples):
        i = random.randint(0, trainenc.input_ids.shape[1] - seqlen - 1)
        j = i + seqlen
        inp = trainenc.input_ids[:, i:j]
        tar = inp.clone()
        tar[:, :-1] = -100
        trainloader.append((inp, tar))
    return trainloader, testenc
import sys 
def get_ptb(nsamples, seed, seqlen, model, tokenizer):
    print("Loading PTB dataset...", flush=True)
    sys.stdout.flush()
    import os
    os.environ.setdefault('HF_DATASETS_TIMEOUT', '300')
    download_config = DownloadConfig(
        max_retries=10,  # Increase retry attempts
        num_proc=1,
    )
    
    try:
        print("Downloading PTB training data (this may take a while due to network issues)...", flush=True)
        sys.stdout.flush()
        traindata = load_dataset(
            'ptb_text_only', 
            'penn_treebank', 
            split='train',
            download_config=download_config
        )
        print("Downloading PTB test data...", flush=True)
        sys.stdout.flush()
        testdata = load_dataset(
            'ptb_text_only', 
            'penn_treebank', 
            split='test',
            download_config=download_config
        )
        print("PTB dataset loaded successfully!", flush=True)
        sys.stdout.flush()
    except Exception as e:
        print(f"Error loading PTB dataset: {e}", flush=True)
        sys.stdout.flush()
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"Failed to load PTB dataset. Network timeout or connection issue. Please check your network connection or try again later. Error: {e}")
       
    print("Tokenizing PTB data...", flush=True)
    sys.stdout.flush()
    trainenc = tokenizer(" ".join(traindata['sentence']), return_tensors='pt')
    testenc = tokenizer(" ".join(testdata['sentence']), return_tensors='pt')

    random.seed(seed)
    trainloader = []
    for _ in range(nsamples):
        i = random.randint(0, trainenc.input_ids.shape[1] - seqlen - 1)
        j = i + seqlen
        inp = trainenc.input_ids[:, i:j]
        tar = inp.clone()
        tar[:, :-1] = -100
        trainloader.append((inp, tar))
    return trainloader, testenc

class TokenizerWrapper:
    def __init__(self, input_ids):
        self.input_ids = input_ids



def get_c4(nsamples, seed, seqlen, model, tokenizer):
    # 本地路径配置
    local_c4_path = '/map-vepfs/haozhe/BiDIT/qqllm/CACHE/my_c4_data'
    train_file = os.path.join(local_c4_path, 'en', 'c4-train.00000-of-01024.json.gz')
    val_file = os.path.join(local_c4_path, 'en', 'c4-validation.00000-of-00008.json.gz')
    
    print(f"Loading C4 dataset from local path: {local_c4_path}", flush=True)
    

    # 加载数据集
    print("Loading training data...", flush=True)
    traindata = load_dataset(
        'json',
        data_files={'train': train_file},
        split='train'
    )
    print("Loading validation data...", flush=True)
    valdata = load_dataset(
        'json',
        data_files={'validation': val_file},
        split='validation'
    )
    
    print(f"Loaded {len(traindata)} training samples, {len(valdata)} validation samples", flush=True)
    

    random.seed(seed)
    trainloader = []
    for _ in range(nsamples):
        while True:
            i = random.randint(0, len(traindata) - 1)
            trainenc = tokenizer(traindata[i]['text'], return_tensors='pt')
            if trainenc.input_ids.shape[1] > seqlen:
                break
        i = random.randint(0, trainenc.input_ids.shape[1] - seqlen - 1)
        j = i + seqlen
        inp = trainenc.input_ids[:, i:j]
        tar = inp.clone()
        tar[:, :-1] = -100
        trainloader.append((inp, tar))

    valenc = tokenizer(' '.join(valdata[:1100]['text']), return_tensors='pt')
    valenc = valenc.input_ids[:, : (256 * seqlen)]

    valenc = TokenizerWrapper(valenc)

    return trainloader, valenc




def get_loaders(name, nsamples=128, seed=0, seqlen=2048, model=''):
    cache_file=f'cache/{name}_{nsamples}_{seed}_{seqlen}_{model}.pt'
    try:
        return torch.load(cache_file)
    except:
        pass

    tokenizer = get_tokenizer(model)
    
    if 'wikitext2' in name:
        loaders= get_wikitext2(nsamples, seed, seqlen, model, tokenizer)
    if 'ptb' in name:
        loaders= get_ptb(nsamples, seed, seqlen, model, tokenizer)
    if 'c4' in name:
        loaders= get_c4(nsamples, seed, seqlen, model, tokenizer)
    directory='/'.join(cache_file.split('/')[:-1])
    if not os.path.exists(directory):
        os.makedirs(directory)

    torch.save(loaders,cache_file)
    return loaders
