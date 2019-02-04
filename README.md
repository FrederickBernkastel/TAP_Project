Publicly Hosted API
	http://brianchew.pythonanywhere.com

Requirements
> Local SQl server

Configuration
> /instance/config.py
> > Configure sensitive information such as MySQL URI
> /config.py
> > Configure DEBUG / TESTING settings

Running Test cases
> /tests/db_test.py
> > Runs tests on /app/db.py, using SQLite
> > Tests transactions with the database
> /tests/app_test.py
> > Runs tests on /app/__init__.py, using SQLite
> > Tests app API responses

Running application on server
> Execute /run.py
