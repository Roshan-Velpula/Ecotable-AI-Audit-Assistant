import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
import json
import os
from dotenv import load_dotenv

# Set the current working directory to the script's directory
script_dir = os.path.dirname(__file__)
os.chdir(script_dir)

env_loaded = load_dotenv()
print("Environment loaded:", env_loaded)

embeddings = HuggingFaceEmbeddings(model_name='Lajavaness/sentence-camembert-large')

def excel_to_json(excel_file):
        # Open Excel file as binary and specify encoding
        with open(excel_file, 'rb') as f:
            xls = pd.ExcelFile(f)

        excel_data = {}

        # Iterate through each sheet in the Excel file
        for sheet_name in xls.sheet_names:
            # Read each sheet into a DataFrame
            df = pd.read_excel(xls, sheet_name)
            # Convert DataFrame to list of dictionaries
            sheet_data = df.to_dict(orient='records')
            # Add sheet data to the dictionary with sheet name as key
            excel_data[sheet_name] = sheet_data

        return excel_data

def make_documents(data):


        data_list = []
        aop_list = []
        embeddings_list = []
        ids = []
        metadata_list= []

        idx = 0
        for chapter, content in data.items():

            chapter_name = chapter

            for sub_chapter in content:
                aop_title = sub_chapter.get('AOP', '')
                durable = sub_chapter.get('Durable', '')

                if aop_title != '':

                    aop_list.append(aop_title)
                    string_doc = f"Catégorie: {chapter_name} \n "
                    for key, value in sub_chapter.items():

                        content = f" {key}: {value} \n "

                        string_doc = string_doc + content

                    metadata = {'Catégorie': chapter_name , 'AOP': aop_title, 'Durable': durable}

                    content_embeddings = embeddings.embed_query(string_doc)
                    data_list.append({
                                        'Categorie': chapter_name,
                                        'AOP': aop_title,
                                        'content': string_doc,
                                        'content_vector':content_embeddings,
                                        'durable':durable,
                                    })


        return data_list


viande_excel_dir = os.path.join('data', 'Analyse AOP - viande et fromage - edited-new1.xls')
#other_data_dir = os.path.join('data', 'other data.xls')

json_data_viande = excel_to_json(viande_excel_dir)
#json_data_other = excel_to_json(other_data_dir)

total_data = make_documents(json_data_viande)
#data_list_other = make_documents(json_data_other)


df = pd.DataFrame(total_data)

df.index.name = 'id'

# Export the DataFrame to a CSV file
csv_path = os.path.join("data", "data_with_embeddings.csv")
df.to_csv(csv_path, index=True)

print(f"Data has been successfully saved to {csv_path}")


