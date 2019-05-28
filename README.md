# Book shope

#### Web Programming with Python and JavaScript

**Set up**
```sh
pip3 install virtualenv  
virtualenv venv  
source venv/bin/activate  
pip3 install -r requirements.txt  
export FLASK_APP=application.py  
export FLASK_DEBUG=1  
export   DATABASE_URL=postgres://euinfxrujlnvji:0490cab71448c7b5d145ed80c01edb626a53756b8d9122c9d1e46206641826c7@ec2-54-247-85-251.eu-west-1.compute.amazonaws.com:5432/dcsmlvui4fnad7  
flask run  
```

##### This application allow you to find books, see their ratings and featback of users. You can login, logout. You can leave comments for each book. Also you can give rating to the choosen book.