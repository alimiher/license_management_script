import asyncio
import subprocess
import pandas as pd
from IPython.display import HTML
from datetime import datetime
import time
import os
from concurrent.futures import ThreadPoolExecutor

async def get_lmstat_output(port, server_name):
    lmutil_path = "/var/www/html/lms_apps/lmutil"
    cmd = [lmutil_path, 'lmstat', '-A', '-c', f'{port}@{server_name}']
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return stdout.decode()
        else:
            return None
    except FileNotFoundError:
        return None

def is_ignored_line(line):
    ignored_keywords = [
        'vendor_string', 'floating license', 'expiry', 'vendor:', 'license manager:',
        'system clock', 'File ID:', 'Detecting lmgrd processes', 'Feature usage info'
    ]
    return any(keyword in line for keyword in ignored_keywords)

def parse_log(log_data):
    lines = log_data.strip().split('\n')
    license_info = []
    current_license = None

    for line in lines:
        line = line.strip()
        if not line or is_ignored_line(line):
            continue
        
        if line.startswith('Users of'):
            if current_license:
                license_info.append(current_license)
            total_issued = int(line.split('Total of')[1].split()[0])
            total_in_use = int(line.split('Total of')[2].split()[0])
            license_name = line.split()[2].rstrip(':')
            current_license = {
                'license_name': license_name,
                'total_issued': total_issued,
                'total_in_use': total_in_use,
                'users': []
            }
        elif current_license:
            user_data = line.split()
            if len(user_data) >= 4:
                try:
                    user_info = {
                        'user': user_data[0],
                        'station': user_data[1],
                        'details': f"{user_data[3]} {' '.join(user_data[4:])}"
                    }
                    current_license['users'].append(user_info)
                except IndexError:
                    pass
    
    if current_license:
        license_info.append(current_license)
    
    return license_info

def create_dataframe(license_info):
    rows = []
    for license in license_info:
        total_issued = license['total_issued']
        total_in_use = license['total_in_use']
        total_free = total_issued - total_in_use
        for user in license['users']:
            rows.append([license['license_name'], user['user'], user['station'], total_issued, total_in_use, total_free, user['details']])
    
    df = pd.DataFrame(rows, columns=['License', 'User', 'Station', 'Total Issued', 'Total In Use', 'Total Free', 'Details'])
    return df

def style_dataframe(df):
    styled_df = (df.style
                 .set_table_styles([
                     {'selector': 'thead th', 'props': [('background-color', '#4CAF50'), ('color', 'white'), ('font-weight', 'bold'), ('text-align', 'center')]},
                     {'selector': 'td, th', 'props': [('border', '1px solid black'), ('padding', '5px'), ('white-space', 'nowrap'), ('text-align', 'center')]},
                     {'selector': '', 'props': [('border-collapse', 'collapse')]}
                 ])
                 .set_properties(**{'text-align': 'center'}))
    return styled_df

def read_licenses(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    licenses = []
    for line in lines:
        if line.startswith("#") or not line.strip():
            continue
        licenses.append(line.strip().split(','))

    return licenses

def generate_html(license_name, df, error=None):
    common_styles = """
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
            position: relative;
        }
        .timestamp {
            position: absolute;
            top: 20px;
            left: 20px;
            color: #333;
            font-size: 14px;
        }
        h2 {
            text-align: center;
            color: #4CAF50;
        }
        table {
            width: 80%;
            margin: 20px auto;
            border-collapse: collapse;
            box-shadow: 0 2px 3px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #4CAF50;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #e0e0e0;
        }
        a {
            color: #4CAF50;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
    """

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if error:
        html_content = f"""
        <html>
        <head>
            <title>Error for {license_name}</title>
            <meta http-equiv="refresh" content="5">
            {common_styles}
        </head>
        <body>
            <div class="timestamp">Last updated: {current_time}</div>
            <h2>Error for {license_name}</h2>
            <p>{error}</p>
        </body>
        </html>
        """
    else:
        styled_df = style_dataframe(df)
        df_html = styled_df.to_html()

        html_content = f"""
        <html>
        <head>
            <title>{license_name} License Details</title>
            <meta http-equiv="refresh" content="5">
            {common_styles}
        </head>
        <body>
            <div class="timestamp">Last updated: {current_time}</div>
            <h2>{license_name} License Details</h2>
            {df_html}
        </body>
        </html>
        """

    if not os.path.exists('pages'):
        os.makedirs('pages')

    with open(f"pages/{license_name}.html", "w") as file:
        file.write(html_content)

def create_index_html(licenses):
    index_content = """
    <html>
    <head>
        <title>License Index</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
            }
            h2 {
                text-align: center;
                color: #4CAF50;
            }
            table {
                width: 80%;
                margin: 20px auto;
                border-collapse: collapse;
                box-shadow: 0 2px 3px rgba(0,0,0,0.1);
            }
            th, td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #4CAF50;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            tr:hover {
                background-color: #e0e0e0;
            }
            a {
                color: #4CAF50;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h2>License Index</h2>
        <table>
            <tr>
                <th>License Name</th>
                <th>Server Name</th>
                <th>Port</th>
                <th>Details</th>
            </tr>"""

    for license in licenses:
        license_name, server_name, port = [item.strip() for item in license]
        details_link = f"pages/{license_name}.html"
        index_content += f"<tr><td>{license_name}</td><td>{server_name}</td><td>{port}</td><td><a href='{details_link}'>Details</a></td></tr>"

    index_content += """
        </table>
    </body>
    </html>"""

    with open("index.html", "w") as file:
        file.write(index_content)

async def process_license_async(license):
    license_name, server_name, port = [item.strip() for item in license]
    lmstat_output = await get_lmstat_output(port, server_name)
    
    if lmstat_output:
        license_info = parse_log(lmstat_output)
        df = create_dataframe(license_info)
        generate_html(license_name, df)
    else:
        generate_html(license_name, None, error="Unable to retrieve license information.")

async def main_async():
    licenses = read_licenses("licenses.txt")
    create_index_html(licenses)

    tasks = [process_license_async(license) for license in licenses]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    while True:
        asyncio.run(main_async())
        time.sleep(1)
