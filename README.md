# LendTrax

LendTrax is a utility for tracking lender consents for optional mandatory payments on syndicated term loans.
The application provides functionality for:
< This section to be completed >
* the administrator to create new end points for new deals
* the admin to upload a list of lenders in an excel (or csv) format, automatically populating the lender list in the database
* the current status of consenting, non-consenting, or unactioned lenders to be viewed through a page on the site in the administrator's view
    * this can also be downloaded to a csv file for distribution

## Composition
The project is primarily written in Python (with html and css where applicable) within the Flask web framework and uses MySql for data persistence. 

## Improvements
This project was done prior to my time at ZipCode Wilmington and prior to my awareness of object oriented programming concepts, unit testing, design patterns, etc. Once I find the time, I intend to go back and transform the project from an all-encompassing god script into separate objects within a true MVC framework, written as an object oriented application. Additionally, I would like to change the lender-access process into something more robust than sharing a deal name, as well as add a true authentication procedure. 

## Motivation
I created this app out of a desire to see if I could replicate a concept I was aware of in the syndicated loan space using skills I developed in my spare time with Python.
