import csv
from redis import Redis
import numpy as np
from sentence_transformers import SentenceTransformer
from redis.commands.search.query import Query
from redis.commands.search.field import (
    NumericField,
    TagField,
    TextField,
    VectorField,
)
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

host = os.getenv('REDIS_HOST', default = "localhost")
port = os.getenv('REDIS_PORT', default = 7000)
pwd = os.getenv('REDIS_PWD', default = '') 

redis = Redis(host=host, port=port, password=pwd)
redis.flushdb()

# Load the machine learning model
model = SentenceTransformer('sentence-transformers/all-distilroberta-v1')



with open('./Labelled Tweets.csv', newline='') as csvfile:
     csvreader = csv.reader(csvfile)
     tweethash={}
     for tweet in csvreader:
        #p = redis.pipeline(transaction=False)
        keyname = "tweet:{}".format(tweet[0])
        #del tweet["specs"]
        tweethash["text"]=tweet[2]
        tweethash["text_embeddings"] = model.encode(tweet[2]).astype(np.float32).tobytes()
        redis.hset(keyname, mapping=tweethash)
        #p.hset(keyname, mapping=tweethash)
        #p.execute()
# Create an index
indexDefinition = IndexDefinition(
    prefix=["tweet:"],
    index_type=IndexType.HASH,
)

number_of_vectors=2000
redis.ft("tweet:idx").create_index(
    (
        TextField("text", no_stem=True, sortable=True),
        #TagField("symbol"),
        #NumericField("price", sortable=True),
        VectorField("text_embeddings", "FLAT", {  "TYPE": "FLOAT32", 
                                                  "DIM": 768, 
                                                  "DISTANCE_METRIC": "COSINE",
                                                  "INITIAL_CAP": number_of_vectors, 
                                                  "BLOCK_SIZE": number_of_vectors
                                                })
    ),
    definition=indexDefinition
)
