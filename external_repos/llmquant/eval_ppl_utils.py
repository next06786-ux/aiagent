import time

import torch
import torch.nn as nn



@torch.no_grad()
def llama_eval(model, testenc, dev,  dataset: str, log_wandb: bool = False):
    print("Evaluating ...")
    
    # Hook 已废弃，使用 DuQuantLinear 自定义层

    testenc = testenc.input_ids
    nsamples = testenc.numel() // model.seqlen

    use_cache = model.config.use_cache
    model.config.use_cache = False
    layers = model.model.layers

    model.model.embed_tokens = model.model.embed_tokens.to(dev)
    layers[0] = layers[0].to(dev)

    dtype = next(iter(model.parameters())).dtype
    inps = torch.zeros(
        (nsamples, model.seqlen, model.config.hidden_size), dtype=dtype, device=dev
    )
    cache = {"i": 0, "attention_mask": None, "position_ids": None}
    model_type = model.config.model_type.lower() if hasattr(model.config, "model_type") else ""
    use_position_ids = ("llama" in model_type) or ("qwen" in model_type) or ("gpt" in model_type)

    class Catcher(nn.Module):
        def __init__(self, module):
            super().__init__()
            self.module = module
            if hasattr(module, "attention_type"):
                self.attention_type = module.attention_type

        def __getattr__(self, name):
            try:
                return super().__getattr__(name)
            except AttributeError:
                wrapped = self._modules.get("module")
                if wrapped is not None and hasattr(wrapped, name):
                    return getattr(wrapped, name)
                raise

        def forward(self, inp, **kwargs):
            inps[cache["i"]] = inp
            cache["i"] += 1
            cache["attention_mask"] = kwargs.get("attention_mask", None)
            cache["position_ids"] = kwargs.get("position_ids", None)
            raise ValueError

    layers[0] = Catcher(layers[0])
    for i in range(nsamples):
        batch = testenc[:, (i * model.seqlen) : ((i + 1) * model.seqlen)].to(dev)
        try:
            if use_position_ids:
                batch_size, seq_len = batch.shape
                position_ids = torch.arange(seq_len, dtype=torch.long, device=batch.device)
                position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)
                attention_mask = torch.ones((batch_size, seq_len), dtype=torch.long, device=batch.device)
                model(batch, attention_mask=attention_mask, position_ids=position_ids)
            else:
                model(batch)
        except ValueError:
            pass
    layers[0] = layers[0].module

    layers[0] = layers[0].cpu()
    model.model.embed_tokens = model.model.embed_tokens.cpu()
    torch.cuda.empty_cache()

    outs = torch.zeros_like(inps)
    attention_mask = cache["attention_mask"]
    position_ids = cache.get("position_ids", None)
    use_shared_position_embeddings = (
        hasattr(model, "model")
        and hasattr(model.model, "rotary_emb")
        and (("llama" in model_type) or ("qwen" in model_type))
    )

    def forward_layer_with_position(layer, inp, attention_mask, position_ids=None):
        pos_ids = position_ids
        if pos_ids is None:
            batch_size, seq_len = inp.shape[0], inp.shape[1]
            pos_ids = torch.arange(seq_len, dtype=torch.long, device=inp.device)
            pos_ids = pos_ids.unsqueeze(0).expand(batch_size, -1)
        else:
            pos_ids = pos_ids.to(inp.device)

        if use_shared_position_embeddings:
            try:
                position_embeddings = model.model.rotary_emb(inp, pos_ids)
                return layer(
                    inp,
                    attention_mask=attention_mask,
                    position_ids=pos_ids,
                    position_embeddings=position_embeddings,
                )[0]
            except TypeError:
                pass
        try:
            return layer(inp, attention_mask=attention_mask, position_ids=pos_ids)[0]
        except TypeError:
            return layer(inp, attention_mask=attention_mask)[0]

    for i in range(len(layers)):
        print(i)
        layer = layers[i].to(dev)

        for j in range(nsamples):
            outs[j] = forward_layer_with_position(
                layer,
                inps[j].unsqueeze(0),
                attention_mask,
                position_ids,
            )
        layers[i] = layer.cpu()
        del layer
        torch.cuda.empty_cache()
        inps, outs = outs, inps

    if model.model.norm is not None:
        model.model.norm = model.model.norm.to(dev)
    model.lm_head = model.lm_head.to(dev)

    testenc = testenc.to(dev)
    nlls = []
    total_correct = 0
    total_tokens = 0
    for i in range(nsamples):
        hidden_states = inps[i].unsqueeze(0)
        if model.model.norm is not None:
            hidden_states = model.model.norm(hidden_states)
        lm_logits = model.lm_head(hidden_states)
        shift_logits = lm_logits[:, :-1, :].contiguous()
        shift_labels = testenc[:, (i * model.seqlen) : ((i + 1) * model.seqlen)][:, 1:]
        loss_fct = nn.CrossEntropyLoss()
        loss = loss_fct(
            shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1)
        )
        neg_log_likelihood = loss.float() * model.seqlen
        nlls.append(neg_log_likelihood)
        
        # ⭐ 计算 Next Token Accuracy
        # 1. 获取预测的 token（argmax）
        preds = torch.argmax(shift_logits, dim=-1)  # [batch_size, seq_len-1]
        
        # 2. 处理 mask（检查是否有 padding，通常 -100 或 0 表示 padding）
        # 由于 testenc 是连续序列，理论上没有 padding，但为了安全起见，检查特殊值
        mask = (shift_labels != -100) & (shift_labels >= 0)  # 排除 -100 和负数
        
        # 3. 计算正确数和总 token 数
        correct = ((preds == shift_labels) & mask).sum().item()
        num_tokens = mask.sum().item()
        
        total_correct += correct
        total_tokens += num_tokens
    
    ppl = torch.exp(torch.stack(nlls).sum() / (nsamples * model.seqlen))
    acc = total_correct / total_tokens if total_tokens > 0 else 0.0
    print(f"Perplexity: {ppl.item():3f}, Next Token Accuracy: {acc:.4f} ({total_correct}/{total_tokens})")

    model.config.use_cache = use_cache

@torch.no_grad()
def opt_eval(model, testenc, dev, dataset: str, log_wandb: bool = False):
    print('Evaluating ...')
    
    # Hook 已废弃，使用 DuQuantLinear 自定义层

    testenc = testenc.input_ids
    nsamples = testenc.numel() // model.seqlen

    use_cache = model.config.use_cache
    model.config.use_cache = False
    layers = model.model.decoder.layers

    model.model.decoder.embed_tokens = model.model.decoder.embed_tokens.to(dev)
    model.model.decoder.embed_positions = model.model.decoder.embed_positions.to(dev)
    if hasattr(model.model.decoder, 'project_out') and model.model.decoder.project_out:
        model.model.decoder.project_out = model.model.decoder.project_out.to(dev) 
    if hasattr(model.model.decoder, 'project_in') and model.model.decoder.project_in:
        model.model.decoder.project_in = model.model.decoder.project_in.to(dev) 
    layers[0] = layers[0].to(dev)

    dtype = next(iter(model.parameters())).dtype
    inps = torch.zeros(
        (nsamples, model.seqlen, model.config.hidden_size), dtype=dtype, device=dev
    )
    cache = {'i': 0, 'attention_mask': None}

    class Catcher(nn.Module):
        def __init__(self, module):
            super().__init__()
            self.module = module
            if hasattr(module, "attention_type"):
                self.attention_type = module.attention_type

        def __getattr__(self, name):
            try:
                return super().__getattr__(name)
            except AttributeError:
                wrapped = self._modules.get("module")
                if wrapped is not None and hasattr(wrapped, name):
                    return getattr(wrapped, name)
                raise
        def forward(self, inp, **kwargs):
            inps[cache['i']] = inp
            cache['i'] += 1
            cache['attention_mask'] = kwargs.get('attention_mask', None)
            raise ValueError
    layers[0] = Catcher(layers[0])
    for i in range(nsamples):
        batch = testenc[:, (i * model.seqlen):((i + 1) * model.seqlen)].to(dev)
        try:
            model(batch)
        except ValueError:
            pass
    layers[0] = layers[0].module

    layers[0] = layers[0].cpu()
    model.model.decoder.embed_tokens = model.model.decoder.embed_tokens.cpu()
    model.model.decoder.embed_positions = model.model.decoder.embed_positions.cpu()
    if hasattr(model.model.decoder, 'project_out') and model.model.decoder.project_out:
        model.model.decoder.project_out = model.model.decoder.project_out.cpu()
    if hasattr(model.model.decoder, 'project_in') and model.model.decoder.project_in:
        model.model.decoder.project_in = model.model.decoder.project_in.cpu()
    torch.cuda.empty_cache()

    outs = torch.zeros_like(inps)
    attention_mask = cache['attention_mask']

    for i in range(len(layers)):
        print(i)
        layer = layers[i].to(dev)

        for j in range(nsamples):
            outs[j] = layer(inps[j].unsqueeze(0), attention_mask=attention_mask)[0]
        layers[i] = layer.cpu()
        del layer
        torch.cuda.empty_cache()
        inps, outs = outs, inps

    if model.model.decoder.final_layer_norm is not None:
        model.model.decoder.final_layer_norm = model.model.decoder.final_layer_norm.to(dev)
    if model.model.decoder.project_out is not None:
        model.model.decoder.project_out = model.model.decoder.project_out.to(dev)
    model.lm_head = model.lm_head.to(dev)

    testenc = testenc.to(dev)
    nlls = []
    total_correct = 0
    total_tokens = 0
    for i in range(nsamples):
        hidden_states = inps[i].unsqueeze(0)
        if model.model.decoder.final_layer_norm is not None:
            hidden_states = model.model.decoder.final_layer_norm(hidden_states)
        if model.model.decoder.project_out is not None:
            hidden_states = model.model.decoder.project_out(hidden_states)
        lm_logits = model.lm_head(hidden_states)
        shift_logits = lm_logits[:, :-1, :].contiguous()
        shift_labels = testenc[
            :, (i * model.seqlen):((i + 1) * model.seqlen)
        ][:, 1:]
        loss_fct = nn.CrossEntropyLoss()
        loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
        neg_log_likelihood = loss.float() * model.seqlen
        nlls.append(neg_log_likelihood)
        
        # ⭐ 计算 Next Token Accuracy
        # 1. 获取预测的 token（argmax）
        preds = torch.argmax(shift_logits, dim=-1)  # [batch_size, seq_len-1]
        
        # 2. 处理 mask（检查是否有 padding，通常 -100 或 0 表示 padding）
        # 由于 testenc 是连续序列，理论上没有 padding，但为了安全起见，检查特殊值
        mask = (shift_labels != -100) & (shift_labels >= 0)  # 排除 -100 和负数
        
        # 3. 计算正确数和总 token 数
        correct = ((preds == shift_labels) & mask).sum().item()
        num_tokens = mask.sum().item()
        
        total_correct += correct
        total_tokens += num_tokens
    
    ppl = torch.exp(torch.stack(nlls).sum() / (nsamples * model.seqlen))
    acc = total_correct / total_tokens if total_tokens > 0 else 0.0
    print(f"Perplexity: {ppl.item():3f}, Next Token Accuracy: {acc:.4f} ({total_correct}/{total_tokens})")
    print({f'{dataset}/perplexity': ppl.item()})

    model.config.use_cache = use_cache
