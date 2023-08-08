# PanelFileSync
A small application that connects to the webserver of a Comfort Panel and copies all files from a directory to a local directory.

## Prequesits
- Firefox >= V.115 must be installed on the system
- [Geckodriver ](https://github.com/mozilla/geckodriver/releases) must be in the direcotry of the executable (mostly geckodriver-v0.33.0-win64.zip)

## Usage

1. Download and extract the zip file
2. Place the geckodriver.exe within the same directory as the executable
3. Update the parameters in the config.ini file according to your needs. 
_(sync_folder must be absolute path, save_directory can be absolute or relative path)_

## Known issues
- png/jpg files cannot be downloaded
