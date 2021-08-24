import os
import json

from rasa_nlu.training_data import load_data
from rasa_nlu.model import Trainer
from rasa_nlu import config


pwd = os.path.dirname(os.path.abspath(__file__))
source_root = os.path.abspath(os.path.join(pwd, ".."))
train_data_path = os.path.join(
    source_root, "assets/empty_nlu_model/raw_training_data.json")

with open(train_data_path) as f:
    data = json.load(f)
data.pop("regex_features")
data.pop("key_words")
data.pop("intent_rules")
data.pop("intent_id2name")

nlu_data = os.path.join(os.path.dirname(train_data_path), "training_data.json")
with open(nlu_data, "w") as f:
    json.dump(data, f, ensure_ascii=False)

nlu_config = os.path.join(
    source_root, "assets/config_jieba_mitie_sklean.yml")
training_data = load_data(nlu_data)
trainer = Trainer(config.load(nlu_config))
trainer.train(training_data)
trainer.persist(source_root,
                project_name="assets", fixed_model_name="empty_nlu_model")
