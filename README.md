# LendTrax

> LendTrax is a utility for tracking lender consents for optional mandatory payments on syndicated term loans.
> The application provides functionality for:
>* The administrator to create new end points for new deals
>* The administrator to upload a list of lenders in an excel (or csv) format, automatically populating the lender list in the database
>* The current status of consenting, non-consenting, or unactioned lenders to be viewed through a page on the site in the administrator's view
>    * This can also be downloaded to a csv file for distribution
>* The lender to log in and either consent or not consent to the payment
## Composition
The project is primarily written in Python (with html and css where applicable) within the Flask web framework and uses MySql for data persistence. 

## To Run
#### Database
* The file 'lendtrax.sql' can be imported into mysql to create the appropriate schema.
* A 'credentials.txt' file should be created including your mysql host, user, password, and database name per your instance, in that order on separate lines.
   * If 'lendrax.sql' is imported, database will be named "lendtrax".
#### Main Application
* Install all the neccessary libraries:
   * python3-flask
   * flask_session
   * pandas
   * sqlalchemy
   * pymysql
   * mysql-connector-python
* In the main directory, run `export FLASK_APP=application.py`
* Run the command `flask run`
   * The application should now be available on localhost:5000
#### Where To Start
* The default administrative agent view credentials are:
   * deal:test
   * mei:agentbank
   * password:password
* Here you can upload a new deal from a lenderlist csv file

## Utilities
Within the utilities folder is a small script for creating dummy lender lists that can be uploaded into the application through the gui for testing purposes.

## Improvements
This project was done prior to my time at ZipCode Wilmington and prior to my awareness of object oriented programming concepts, unit testing, design patterns, etc. Once I find the time, I intend to go back and transform the project from an all-encompassing god script into separate objects within a true MVC framework, written as an object oriented application. I would also like to change the lender-access process into something more robust than sharing a deal name, as well as add a true authentication procedure. Additionaly, there are many non-parameterized SQL queries that need cleaning up as well as variable naming conventions that would make Robert "Uncle Bob" Martin very sad.

## Motivation
I created this app out of a desire to see if I could replicate a concept I was aware of in the syndicated loan space using skills I developed in my spare time with Python.
