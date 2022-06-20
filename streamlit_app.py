import streamlit as st
from redis import Redis
import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from redis.commands.search.query import Query

#st.set_page_config(layout="wide")


host = os.getenv('REDIS_HOST', default = "localhost")
port = os.getenv('REDIS_PORT', default = 7000)
pwd = os.getenv('REDIS_PWD', default = '') 

redis = Redis(host=host, port=port, password=pwd)

@st.cache(allow_output_mutation=True)
def get_model():
    return SentenceTransformer('sentence-transformers/all-distilroberta-v1')

model = get_model()
st.title("Redis Vector Similarity Search")

user_query = st.text_input("Query:", 'apple slowdown')
print("search string:"+user_query)
index_type = st.radio(
     "Index type:",
     ('VSS', 'Full Text'))
if index_type=='VSS':
    q = Query("*=>[KNN 10 @text_embeddings $vector AS result_score]")\
                .return_fields("result_score","text")\
                .dialect(2)\
                .sort_by("result_score", True)
    query_vector=model.encode(user_query).astype(np.float32).tobytes()
        #print(model.encode(user_query))
    res = redis.ft("tweet:idx").search(q, query_params={"vector": query_vector})
    #df=pd.json_normalize(res['docs'])
    df = pd.DataFrame([t.__dict__ for t in res.docs ]).drop(columns=["payload"])
    body="""
    **Index creation:**
    ```python
    indexDefinition = IndexDefinition(
        prefix=["tweet:"],
        index_type=IndexType.HASH,
    )

    number_of_vectors=12000
    redis.ft("tweet:idx").create_index(
        (
            VectorField("text_embeddings", "FLAT", {  "TYPE": "FLOAT32", 
                                                    "DIM": 768, 
                                                    "DISTANCE_METRIC": "COSINE",
                                                    "INITIAL_CAP": number_of_vectors, 
                                                    "BLOCK_SIZE": number_of_vectors
                                                    })
        ),
        definition=indexDefinition
    )
    ```
    **Insert Data:**
    ```python
    model = SentenceTransformer('sentence-transformers/all-distilroberta-v1')

    keyname = "tweet:{}".format(id)
    tweethash["text"]=text
    tweethash["text_embeddings"] = model.encode(text).astype(np.float32).tobytes()
    redis.hset(keyname, mapping=tweethash)
    ```
    **Query:**
    ```python
    query_vector=model.encode(user_query).astype(np.float32).tobytes()

    q = Query("*=>[KNN 10 @text_embeddings $vector AS result_score]")
        .return_fields("result_score","text")
        .dialect(2)
        .sort_by("result_score", True)
    res = redis.ft("tweet:idx").search(q, query_params={"vector": query_vector})
    ```
    """
    with st.expander('Code example', expanded=False):
        st.markdown(body)
    st.table(df)
if index_type=='Full Text':
    body="""
    **Index creation:**
    ```python
    indexDefinition = IndexDefinition(
        prefix=["tweet:"],
        index_type=IndexType.HASH,
    )

    redis.ft("tweet:idx").create_index(
        (
         TextField("text", no_stem=True, sortable=True),
        ),
        definition=indexDefinition
    )
    ```
    **Insert Data:**
    ```python
    keyname = "tweet:{}".format(id)
    tweethash["text"]=text
    redis.hset(keyname, mapping=tweethash)
    ```
    **Query:**
    ```python
    res = redis.ft("tweet:idx").search("@text:"+user_query)
    ```
    """
    with st.expander('Code example', expanded=False):
        st.markdown(body)
    res = redis.ft("tweet:idx").search("@text:"+user_query)
    #res
    #df=pd.json_normalize(res['docs'])
    if res.total>0:
        df = pd.DataFrame([t.__dict__ for t in res.docs ]).drop(columns=["payload","text_embeddings"])
        st.table(df)
    else:
        st.warning('no results found')
#for doc in res.docs:
#    doc.text, doc.result_score