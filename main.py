from os import PRIO_USER
from urllib import response
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import boto3
import PIL
import urllib
from PIL import Image
import pathlib
import requests
from colorizer_app import Colorizer

# import psycopg2

app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3 = boto3.resource('s3')
S3_BUCKET_NAME = "iro-bucket"


class PhotoModel(BaseModel):
    id: int
    photo_name: str
    photo_url: str


colorized_url_set = []


@app.get('/getcolorized')
async def getcolorized():
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(S3_BUCKET_NAME)
    for colorized in bucket.objects.filter(Prefix='colorized/'):
        print(colorized.key)
        colorized_url = f"https://{S3_BUCKET_NAME}.s3.us-west-1.amazonaws.com/{colorized.key}"
        colorized_url_set.append(colorized_url)
    return {'colorized_set': set(colorized_url_set)}


@app.get("/gallery")  # , response_model=List[PhotoModel]
async def get_all_photos():
    return {'colorized_set': set(colorized_url_set)}


@app.post("/photos", status_code=201)
async def add_photo(file: UploadFile):
    print(f"Received: {file.filename}")

    # Upload file to AWS S3
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(S3_BUCKET_NAME)
    bucket.upload_fileobj(file.file, file.filename,
                          ExtraArgs={"ACL": "public-read"})

    uploaded_file_url = f"https://{S3_BUCKET_NAME}.s3.us-west-1.amazonaws.com/{file.filename}"
    urllib.request.urlretrieve(uploaded_file_url, f"images/{file.filename}")

    colorized_url = f"https://{S3_BUCKET_NAME}.s3.us-west-1.amazonaws.com/colorized/{file.filename}"
    _, tmpname = Colorizer(f"images/{file.filename}")
    print("Uploading tmp image to bucket")
    bucket.upload_file(tmpname, f"colorized/{file.filename}",
                       ExtraArgs={"ACL": "public-read"})
    colorized_url_set.append(colorized_url)
    print("Success!")
    return {'colorized_upload': colorized_url}


@app.get("/test")
async def root():
    return {"message": "Hello, world!"}
