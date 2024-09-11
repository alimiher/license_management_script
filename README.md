# License Management Script

## Description
This Python script generates HTML reports for license usage based on data from `licenses.txt` and `lmstat` output. The generated HTML files provide a detailed overview of license usage, including hyperlinks to individual server reports.

## Prerequisites
- Python 3.10
- Required Python packages: `pandas`, `jinja2`

## Installation
1. **Clone the repository:**
    ```bash
    git clone <repository_url>
    ```

2. **Navigate to the project directory:**
    ```bash
    cd /path/to/project
    ```

3. **Create and activate a virtual environment:**
    ```bash
    python -m venv myenv
    source myenv/bin/activate
    ```

4. **Install required packages:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration
1. **Prepare the `licenses.txt` file:**

   Place the `licenses.txt` file in the `/path/to/project` directory. Ensure that it contains information on your license servers, formatted correctly.

2. **Update `licenses.txt` file:**

   Update the `licenses.txt` file with the details of your license servers. The script will read this file to generate the necessary reports.

## Usage
1. **Run the script:**
    ```bash
    python generate_license_html_comb.py
    ```

2. **Output:**
   The script will generate HTML reports in the specified output directory. These reports include detailed license usage information.

## Service Setup (Optional)
To run the script as a system service, create a systemd service file. Example configuration:

```ini
[Unit]
Description=License Management Script
After=network.target

[Service]
ExecStart=/path/to/virtualenv/bin/python /path/to/project/generate_license_html_comb.py
Restart=always
User=root
WorkingDirectory=/path/to/project
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=license_script

[Install]
WantedBy=multi-user.target

Place this configuration in /etc/systemd/system/license_script.service, then enable and start the service:

sudo systemctl daemon-reload
sudo systemctl enable license_script.service
sudo systemctl start license_script.service

Troubleshooting
ModuleNotFoundError: Ensure that all required packages are installed in your virtual environment.
Service not starting: Check service logs using journalctl -u license_script.service for detailed error messages.
License
This project is licensed under the MIT License - see the LICENSE file for details.