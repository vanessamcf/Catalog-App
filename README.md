# Catalog App

### Technologies Used

**Python 2.7** - Language the project is coded in
**Vagrant** - For a dev VM
**VirtualBox** - Required for Vagrant

### System setup and how to view this project
1- Download and install Vagrant
2- Download and install Virtual Box
3- Clone this repository
4- Run `vagrant up` command to start up the VM
5- Run `vagrant ssh` command to log into the VM.
6- `cd /vagrant` to change to your vagrant directory
7- Move inside the catalog folder `cd /vagrant/Projeto - Catalogo App`
8- Initialize the database $ `python db_setup.py`
9- Populate the database with some initial data $ `python basic.py`
10- Run `python application.py`
11- Browse the App at this URL http://localhost:8000/catalog

**JSON endpoints**:
Returns JSON of all categories
`/catalog/category/JSON`

Returns JSON of all the items in a specific category
`/catalog/<category_name>/JSON`

Returns JSON of item setails in a specific category

`/catalog/<item_id>/JSON'`

