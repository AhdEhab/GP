import numpy as np
import pandas as pd
import gspread
import sklearn
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from google.oauth2.service_account import Credentials

#import the model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def cosine_similarity(A, B):
  A = A.reshape(1, -1)
  B = B.reshape(1, -1)

  cosine = cosine_similarity(A,B)[0][0]
  return cosine

def compute_similarity(x,y):
      embedding_1= model.encode(x, convert_to_tensor=True)
      embedding_2 = model.encode(y, convert_to_tensor=True)
      cosi = cosine_similarity(dim=0)
      output = (cosi(embedding_1, embedding_2)+1)/2
      return output

#Accessing the data in the sheet
doc_id="16zMI3339L9uZFGRG275w7DZ0-TlPMd4f8KDdDlrQQuA"
tab_name="Sheet1"
url = "https://docs.google.com/spreadsheets/d/{0}/gviz/tq?tqx=out:csv&sheet={1}".format(doc_id, tab_name)[:-1]
projects=pd.read_csv(url)

#Google Sheet API
scopes = ["https://www.googleapis.com/auth/spreadsheets"] 
creds= Credentials.from_service_account_file("key.json",scopes=scopes)
client = gspread.authorize(creds)

def append_data_to_sheet(new_idea):
   sheet = client.open_by_key(doc_id).sheet1
   #get the last cell in the sheet
   last_row_values = sheet.get_all_values()[-1]
   last_number = int(last_row_values[0])
   ID = int(last_number) + 1
   new_data = [ID,new_idea]
   sheet.append_row(new_data)
   return f"Data appended successfully!"

def remove_data(search_value):
  sheet = client.open_by_key(doc_id).sheet1
  all_values = sheet.get_all_values()
  row_index = None
  for i, row in enumerate(all_values):
        if row[1] == search_value:
            row_index = i 
  if row_index is not None:
        del all_values[row_index]
        sheet.clear()  
        sheet.update(all_values)
        msg="Project data was removed successfully!"
  else:
        msg="No such project found."
  return msg


from fastapi import FastAPI, File, UploadFile, HTTPException
app=FastAPI()

@app.get("/")
def root():
    return{"Similarity checker"}

@app.post("/similarity")
def search_match(idea):
  max_score = 0
  most_similar_project_index = None
  for i in range(len(projects["Idea"])):
    score = compute_similarity(idea, str(projects.loc[i, "Idea"])) * 100
    if score > max_score:
      max_score = score
      most_similar_project_index = i

  if max_score > 80:
    msg = "Match Found"
    data = {
      "match": projects.loc[most_similar_project_index, "Idea"],
      "score": round(float(max_score), 2)
    }
  elif 70 <= max_score <= 80:  
    msg = "Neutral"
    data = {
      "match": projects.loc[most_similar_project_index, "Idea"],
      "score": round(float(max_score), 2)
    }
  else:
    msg = "No match"
    data = None  

  return msg, data

@app.get("/add")
def append_data_route(new_idea):
    try:
        result_message = append_data_to_sheet(new_idea)
        return {"message": result_message}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/delete")
def remove_project(idea):
   try:
      result_message = remove_data(idea)
      return {"message": result_message}
   except Exception as e:
      return {"error": str(e)}

  


