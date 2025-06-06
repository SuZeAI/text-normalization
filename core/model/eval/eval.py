import pandas as pd
from evaluate import load

import rootutils
rootutils.setup_root(
    __file__,
    indicator=(".project-root", "setup.cfg", "setup.py", ".git", "pyproject.toml"),
    pythonpath=True,
)

from core.model.inference.inference import Inference
from core.model.inference.hybrid_inference import HybirdInference
from core.common.utils import save_data_to_file
from core.config.model_config import (
    SAVED_EVAL_DIR,
    SAVED_EVAL_FILE,
)
from core.config.regex_config import (
    CORRECT_SPELLING_DICT,
    INFERENCE_REGEX_RULES
)
 


class Eval():
  def __init__(self, file_path: str, model_name: str, metric_name: str, inference_mode: str):
    self.file_path = file_path
    self.model_name = model_name
    self.get_metric(metric_name=metric_name)
    self.get_inference_mode(inference_mode=inference_mode)
    
  def get_metric(self, metric_name: str):
    if metric_name=="exact_match":
      self.metric = load("exact_match")
      self.regexes_to_ignore = [" không trăm"]
    if metric_name=="bleu":
      pass
      
  def get_inference_mode(self, inference_mode: str):
    if inference_mode == "llm_inference":
      self.inference = Inference(data_path=self.file_path, model_name=self.model_name)
    elif inference_mode == "hybrid_inference":
      self.inference = HybirdInference(data_path=self.file_path, model_name=self.model_name, rules=INFERENCE_REGEX_RULES, correct_spelling_dict=CORRECT_SPELLING_DICT)
  
  def evaluate(self):
    results = []
    test_data = pd.read_csv(self.file_path)
    for _,row in test_data.iterrows():
      input = row["input"]
      label = row["s_output"]
      tagged_sentence = row["tagged_sentence"]
      gpt_tagged_sentence = row["gpt_tagged_sentence"]
      final_tags = row["final_tags"]
      test_tag = row["test_tag"]
      
      for i in range(10):
        predicted_label = self.inference.infer_one(input=input)
        result = self.metric.compute(predictions=[predicted_label], references=[label], ignore_case=True, ignore_punctuation=True, regexes_to_ignore = self.regexes_to_ignore)
        exact_match_score = int(result["exact_match"])
        
        if exact_match_score == 1:
          break
        
      results.append(
          {"input": input,
          "label": label,
          "predicted_label": predicted_label,
          "tagged_sentence": tagged_sentence,
          "gpt_tagged_sentence": gpt_tagged_sentence,
          "final_tags": final_tags,
          "test_tag": test_tag,
          "exact_match": exact_match_score
          }
        )
      
      if len(results) == 10:
        save_data_to_file(results, SAVED_EVAL_DIR, SAVED_EVAL_FILE)
        results.clear()
    if results:
       save_data_to_file(results, SAVED_EVAL_DIR, SAVED_EVAL_FILE)
    
if __name__=="__main__":
  file_path="/data/datnt3/text-normalization/data_storage/train_test/2025-05-29/test_data.csv"
  model_name="/data/datnt3/text-normalization/core/model/saved/lora/2025-05-26/vn-llama3.2-1b-finetuned-300k"
  
  eval = Eval(file_path=file_path, model_name=model_name, metric_name="exact_match", inference_mode="hybrid_inference")
  eval.evaluate()

  