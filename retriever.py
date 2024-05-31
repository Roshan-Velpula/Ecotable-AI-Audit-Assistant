from data_ingestion import connect_db
#from prompts import custom_answer_prompt_template_reform, summary_prompt, ques_check_prompt
import psycopg2
import os
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from prompts import sql_query_prompt
import re
import time

import pickle

env_loaded = load_dotenv()

groq_api = os.getenv('GROQ_API')

#embeddings = HuggingFaceEmbeddings(model_name='Lajavaness/sentence-camembert-large')
   
sql_query = PromptTemplate(template=sql_query_prompt, input_variables=['query'])

chat = ChatGroq(temperature=0, groq_api_key = groq_api, model_name="Llama3-70b-8192")

import os

def load_or_cache_embeddings(model_name, cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            embeddings = pickle.load(f)
    else:
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        with open(cache_file, 'wb') as f:
            pickle.dump(embeddings, f)
    return embeddings

cache_file = 'embeddings_cache.pkl'
embeddings = load_or_cache_embeddings('Lajavaness/sentence-camembert-large', cache_file)


def query_neon(query, collection_name, cursor, vector_name="content_vector", top_k=5):
    try:
        # Create an embedding vector from the user query
        start_time = time.time()
        embedded_query = embeddings.embed_query(query)
        end_time = time.time()
        
        print("Time for embedding:", {end_time - start_time})
        # Convert the embedded_query to PostgreSQL compatible format
        embedded_query_pg = "[" + ",".join(map(str, embedded_query)) + "]"

        # Create the SQL query
        start_time = time.time()
        query_sql = f"""
        SELECT content, durable
        FROM {collection_name}
        ORDER BY {vector_name} <=> '{embedded_query_pg}'
        LIMIT {top_k};
        """
        # Execute the query
        cursor.execute(query_sql)
        results = cursor.fetchall()
        end_time = time.time()
        
        print("Time for retrieval:", {end_time - start_time})

        return results

    except (psycopg2.Error) as e:
        # Roll back the transaction if an error occurs
        cursor.execute("ROLLBACK;")
        print(f"Error executing SQL query: {e}")
        return []


def format_results(results):
    formatted_string = ""
    if len(results) > 1:
        for i, result in enumerate(results, start=1):
            content, durable = result
            formatted_string += f"*Document {i}:content: {content}\ndurable: {durable}\n "
    else:
        formatted_string = f"{results[0]}"
    return formatted_string

query = "How many fromage francaise are durable?"  

#results = query_neon(query, 'viande_fromage', cursor=connect_db()[1])

#print(format_results(results))
#sql_query = PromptTemplate(template=sql_query_prompt, input_variables=['query'])

def sql_result(query, cursor):
    query = chat.invoke(sql_query.format_prompt(query = query)).content
    #print(query)
    query_sql = extract_sql_query(query)
    #print(query_sql)
    if query_sql:
        
        query_pull = f"""
        
        {query_sql}
        
        """
    
    #print(query_pull)
    try:
        cursor.execute(query_pull)
        results = cursor.fetchall()
        return results
    except (psycopg2.Error) as e:
        # Roll back the transaction if an error occurs
        cursor.execute("ROLLBACK;")
        print(f"Error executing SQL query: {e}")
        return []
    
    
def extract_sql_query(text):
    """
    Extracts the SQL query that starts with 'SELECT' and ends with a semicolon from the given text.
    
    Args:
    text (str): The input text containing the SQL query.
    
    Returns:
    str: The extracted SQL query or a message indicating no query was found.
    """
    # Define a regular expression pattern to match a SQL query starting with SELECT and ending with ;
    pattern = re.compile(r'SELECT.*?;', re.DOTALL | re.IGNORECASE)
    match = pattern.search(text)
    
    if match:
        return match.group(0).strip()
    else:
        return "No SQL query found."
    
def gen_context(query):
    
    sql_res = sql_result(query, cursor=connect_db()[1])
    
    if len(sql_res)!=0:
        
        return "SQL Result:" + format_results(sql_res)
    else:
        results = query_neon(query, 'viande_fromage', cursor=connect_db()[1])
        
        return "Retrieved Documents\n"+ format_results(results)
        


#print(format_results(sql_result(query, cursor=connect_db()[1])))

#print(gen_context(query))

#print(chat.invoke("How are you?").content)