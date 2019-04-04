#Catalog App

###Technologies Used

Python 2.7 - Language the project is coded in
Vagrant - For a dev VM
VirtualBox - Required for Vagrant

###System setup and how to view this project
Download and install Vagrant
Download and install Virtual Box

Clone this repository
Run vagrant up command to start up the VM
Run vagrant ssh command to log into the VM.
cd /vagrant to change to your vagrant directory
Move inside the catalog folder cd /vagrant/Projeto - Catalogo App
Initialize the database $ python db_setup.py
Populate the database with some initial data $ python basic.py
Run python application.py
Browse the App at this URL http://localhost:8000/catalog

JSON endpoints:
Returns JSON of all categories
/catalog/category/JSON

Returns JSON of all the items in a specific category
/catalog/<category_name>/JSON

Returns JSON of item setails in a specific category

/catalog/<item_id>/JSON'
