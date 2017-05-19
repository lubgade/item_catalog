# Item Catalog

## Overview
This application provides a list of items within a variety of categories. Also provides a user registration and authentication system. Registered users will have the ablity to add, edit and delete their own items.

## Setup
* Install Vagrant & VirtualBox

## Usage
* To use this project - 
  * Clone the repo using `git clone https://github.com/lubgade/item_catalog` 
  * Fork the repo
* Launch the Vagrant VM using `vagrant up`
* Run `vagrant ssh` which takes you to vagrant shell
* At the command line `cd /vagrant`
* Move to the project folder
* Run `python items.py` to populate test items in the database(optional)
* Run the application using `python project.py`
* Access and test the application at `http://localhost:8000`

## Features
* Provides JSON API endpoints to the whole catalog, category with all its items as well as for a particular item
* Provides a third party(Google) authentication & authorization service
* 
