# user_weather
Basic User Signup and Login System along with the functionality of accessing weather details via token authentication.

# APIs
The service consists of 7 endpoints as following:
1. / - home page for signup or login
2. signup/ - registering as a new user
3. activate/<uidb64>/<token> - email verification after registration
4. login/ - login as an existing user
5. profile/ - user profile
6. weather/ - accessing weather details based on region
7. logout/ - logouts of the session

# Installation
To install the required packages, run the following command in the project directory:

    pip install -r requirements.txt
    
Usage

To create tables and make migrations, run the below commands:

        python manage.py makemigrations
        python manage.py migrate

To start the server, run the below command:

    python mange.py runserver
  
  The local server starts running on http://127.0.0.1:8000
  
  (Example url: http://127.0.0.1:8000/monitor/{end_point})

Note: setup the database 
