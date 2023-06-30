# what is this
Autogen is a multi-platform engine for automatically generating CTF challenges, designed primarily for self-study.  
  
Challenges are generated using a stack of templates to build a model of a single web server - starting with server software, then site functionality, then a vulnerability.  
  
Autogen supports dynamic content within templates, allowing for a huge number of permutations on a single challenge format.  
  
The best part? It's as simple as running a Python script*.  

*i hope  
  
### If you need more information, check out the [**wiki**](https://github.com/plaaosert/autogen/wiki).

# requirements
You need all of the following:
- a version of Docker installed that can be invoked on the command-line (e.g. `docker ps`)
- Python 3 (tested using Python 3.8 but should be compatible with most installs)
- the port `9008` to be open on the local machine

# how do i use it
(Replace `python3` with the name of your Python install.)  
Just want a challenge? Good. Use `python3 autogen.py -d DIFFICULTY_LEVEL`, where:
```
[0-15]  -> "Easy"
[15-35] -> "Medium"
[35+]   -> "Hard"
```
Note there are currently no templates with difficulty higher than 55. Check out the [how can i help](https://github.com/plaaosert/autogen#how-can-i-help) section if you want to change that :-)

Here's the full output of `python3 autogen -h`:
```
autogen.py [arguments]
    -l <value> (--loglevel)      | Changes the log level to one of the following:
                                 | CRITICAL   (0) 
                                 | INFO_QUIET (1) 
                                 | INFO       (2) 
                                 | DEBUG      (3) 
                                 | Note that DEBUG will reveal the templates selected.
                                 |
    -d <value> (--difficulty)    | Select the difficulty of the randomly chosen vulnerability.
                                 |
    -b <value> (--base-template) | Add a specific base template to use.
                                 | If given multiple times, all provided templates are set as required.
                                 |
    -s <value> (--site-template) | Set a specific site template to be used for generation.
                                 |
    -v <value> (--vuln-template) | Set a specific vulnerability template to use. 
                                 | If given multiple times, all provided templates are set as required.
                                 |
    -h         (--help)          | Show this help message.
                                 |
    -i         (--inspect)       | View all information for any selected templates (using -b, -s, -v).
                                 |
    --list-templates             | List all loaded templates.
```

# how does it do all this then
*i'll rewrite this eventually*  
  
Each challenge is made up of multiple Docker containers, each serving a specific purpose, such as a webserver or an SQL server. The model used to represent this is
a stack of templates. All templates inherit from an abstract class, using the same
main attributes. This means that a theoretically infinite number of templates can be
stacked on top of each other, making compounding changes. Every Docker container
is represented by a single stack.  
  
At the bottom of the stack is a base template. Base templates will typically contain
only a basic Dockerfile and any configuration files which need to be modified. If a
base template is run on its own with no modifications, it should act similar if not
identical to a fresh install of the service.  
  
After selecting a base template, a site template must be selected. Site templates
implement the full functionality of a working website by copying or modifying new
files.  
  
Finally, a vulnerability template slightly changes files placed by previous templates
to open up one or more security vulnerabilities, as well as placing a flag in a relevant
location. Both vulnerability and site templates are only ever applied to the template
stack for a web server, as auxilliary bases are intended to be treated as black boxes
accessible only to the webserver container.  

# how can i help
Autogen runs on templates. We can never be short on templates! Since each template type is modular, making templates is incredibly simple.  
Take a look at the wiki (you should add the wiki here plaao) to learn more.

# 7. Future work
This project was made with the power of insomnia, anxiety, stress and student loans. There's a lot more to add to this thing.
- Why are we still hardcoded to a specific port in the year of our lord 2023. change that
- Vulnerability template attributes:
	- the `tags` attribute is unused currently - can use it to select for a specific vulnerability *type* instead of a certain single one
	- could add a `hints` attribute and allow the program to show steadily more explicit hints on request
- Reworking template difficulty:
	- How to define difficulty?
	- CTF authors get difficulty wrong all the time. What can we do to prevent this?
- More template types:
	- "Hint" templates to make a challenge easier or harder?
	- "flag hiding method" templates to decouple hiding a flag from the vulnerability template itself?
- Multiple vulnerabilities:
	- vulnerability chaining?
	- multiple paths to a single flag?
- Security:
	- Path traversal vulnerabilities when copying host files
	- Safety of being able to edit a Dockerfile on the user's computer
	- Vetting of new templates
	- Should templates be able to run arbitrary Python scripts?
