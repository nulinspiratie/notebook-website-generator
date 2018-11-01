# notebook-website-generator
Website generator for Jupyter Notebooks

This program allows you to automatically convert groups of [Jupyter Notebooks](http://jupyter.org/) into a website.
It is designed for Jupyter Notebooks that are used as log notebooks, such as a measurement logs.

## Getting started
The first step is to download this repository to your local hard drive, for this tutorial we assume it is in `C:\notebook_website_generator`.
Once downloaded, the converter can be run straight away by opening a command prompt, navigating to `C:\notebook_website_generator`, and running `python convert_notebooks.py`. By default, the notebook will convert the notebooks in the folder `example_notebooks` into the folder `docs`.
One additional step is required, namely manually copying the folder `site-libs` into the folder `docs`.  
Once these steps have been completed, the notebook website can be run by opening `docs\index.html`.

## Setup instructions for FQT users
For any experiments using Jupyter Notebooks for logging, it is recommended to use this converter to add the notebooks to the group website. This website can be accessed by anyone in our group, and requires a password.  

Steps are as follows:
1. Contact Mark to gain access to the group NAS (`\\FQT_NAS`).
2. Copy `config.yml` to the main folder of the notebooks, which for this tutorial we shall assume is in  `C:\experiment\config.yml`.
3. Go through the `C:\experiment\config.yml`, and modify the settings in there to suit your experiment. Be sure to change `html_target_dir` to point to the NAS
4. Open a terminal, navigate to the converter main directory, and run `python convert_notebooks.py C:\experiment\config.yml`

If all goes well, a new folder should be created in `\\FQT_NAS\web\{experiment_name}` where `experiment_name` is defined in the config.
The website should now be accessible via `{NAS-IP}/{experiment_name}`. 

Once a new experiment has been added to the NAS, please let Serwan know, so he can add your project to the front page.

Note that if the website is sent to the NAS, the `site-libs` folder does not need to be copied.

## Setting up automated website updates
It is recommended to setup a periodic task that automatically converts all your notebooks into webpages and saves them to the NAS. This ensures that the project information on the website is kept up to date, and allows everyone in the project/group to easily access the recent information. A periodic task can be setup in windows using Task Scheduler. The general procedure is described here: https://www.dummies.com/computers/pcs/how-to-create-a-task-to-run-a-program-in-windows-task-scheduler/
Be sure to use the following settings:
**program/scripts**: `python`
**add arguments (optional)**: `convert_notebooks.py C:\experiment\config.yml`
**start in (optional)**: `C:\notebook_website_generator`

Be sure to replace the paths above with the correct ones.
