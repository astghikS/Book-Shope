import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine('postgres://euinfxrujlnvji:0490cab71448c7b5d145ed80c01edb626a53756b8d9122c9d1e46206641826c7@ec2-54-247-85-251.eu-west-1.compute.amazonaws.com:5432/dcsmlvui4fnad7')
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv", "r")
    reader = csv.reader(f)
    next(reader)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                {"isbn": isbn, "title": title, "author": author, "year" :year})
    db.commit() 
    print(f"Added book with ISBN: {isbn} Title: {title}  Author: {author}  Year: {year}")

if __name__ == "__main__":
    main()
