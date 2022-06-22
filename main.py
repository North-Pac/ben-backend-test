from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import boto3
import psycopg2

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


@app.get("/photos", response_model=List[PhotoModel])
async def get_all_photos():
    # Connect to our database
    conn = psycopg2.connect(
        database="irodb", user="docker", password="docker", host="0.0.0.0"
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM photo ORDER BY id DESC")
    rows = cur.fetchall()

    formatted_photos = []
    for row in rows:
        formatted_photos.append(
            PhotoModel(
                id=row[0], photo_name=row[1], photo_url=row[2]
            )
        )

    cur.close()
    conn.close()
    return formatted_photos


@app.post("/photos", status_code=201)
async def add_photo(file: UploadFile):
    print("Endpoint hit!!")
    print(file.filename)
    print(file.content_type)

    # Upload file to AWS S3
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(S3_BUCKET_NAME)
    bucket.upload_fileobj(file.file, file.filename,
                          ExtraArgs={"ACL": "public-read"})

    uploaded_file_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{file.filename}"

    # Store URL in database
    conn = psycopg2.connect(
        database="irodb", user="docker", password="docker", host="0.0.0.0"
    )
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO photo (photo_name, photo_url) VALUES ('{file.filename}', '{uploaded_file_url}' )"
    )
    conn.commit()
    cur.close()
    conn.close()


@app.get("/test")
async def root():
    return {"message": "Hello, world!"}
