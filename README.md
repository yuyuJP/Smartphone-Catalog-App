# Smartphone Catalog App

This repository is for Udacity Full Stack Web Developer Nanodegree Program Submission

# Getting Started
## Vagrant
### Change directory
```
$ cd vagrant/
```
### Set up a vagrant machine
```
$ vagrant up
```
### Log in to a vagrant machine
```
$ vagrant ssh
```

## Set up database
### Change directory
```
$ cd catalog/
```
### Configure database
You can setup database for the web application following by
```
$ python database_setup.py
```

### Add sample items
To test the web app, add several sample items to your database following by
```
$ python addmanyitems.py
```

# Running and Testing
You can start the web application following by
```
$ python application.py
```
Open your web browser and open link `localhost:8000`
