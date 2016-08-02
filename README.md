# omeka-bulk-deploy
Python programme intended to bulk install Omeka instances.

## Usage
Run it as root with --xvfb as argument followed by a space and the number of installations you want to launch.

To be run from /var/www/html/omeka (or anywhere else if you adjust the paths in the script). 

You can pimp your initial .zip by adding extensions, they should be automatically installed along Omeka. 

## Disclaimer
I am not the original author of the script, but I don't know who is. I have adapted it to work with the newer version of Omeka (2.4.1 at the time of this writing).

## Additional info

This script is used for one of [MaSTIC](http://mastic.ulb.ac.be)'s classes at the [Université libre de Bruxelles](http://ulb.ac.be), for which we ask 500+ students every year to work in small groups on an Omeka instance.
