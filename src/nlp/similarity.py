import torch
from torch import Tensor
from transformers import BertModel, PreTrainedTokenizer


def cosinesim(vec1: Tensor, vec2: Tensor):
    norm = vec1.norm() * vec2.norm()
    if norm.item() == 0:
        return 0
    return (torch.matmul(vec1.unsqueeze(0), vec2.unsqueeze(1)) / norm).item()


# cosine_sim_texts('Бунт начнется с атеизма', 'революция непременно должна начинать с атеизма', model, tokenizer)
def cosine_sim_texts(text1: str, text2: str, model: BertModel, tokenizer: PreTrainedTokenizer):
    return cosinesim(
        model(**tokenizer(text1, return_tensors='pt'))['last_hidden_state'][0][0],
        model(**tokenizer(text2, return_tensors='pt'))['last_hidden_state'][0][0]
    )
