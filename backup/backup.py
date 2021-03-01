from __future__ import print_function
import pickle
import requests
import datetime
import os
import io
import sys
import subprocess

from apiclient import errors
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive.metadata',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.appdata'
]

def get_drive_service(refresh_path='token.pickle', credentials_path='gdrive.json'):
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    print('Authenticating with gdrive api')
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(refresh_path):
        with open(refresh_path, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        # fixme: not sure what the best model for something like this is, but all
        # of this gdrive auth flow seems wrong
        # with open(refresh_path, 'wb') as token:
        #     pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)
    print('Authenticated with gdrive api')
    return service


def upload_file(service: Resource, file_path, file_metadata):
    print('Starting file upload')
    media = MediaFileUpload(file_metadata['name'])
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print('Finished file upload')
    print('File ID: %s' % file.get('id'))


def create_tar_file(output_filename, file_to_archive, name):
    print(f'Starting file compression to tar {output_filename} for {name}')
    subprocess.call(['mkdir', '-p', '/temp/data/'])

    if 'postgres' in name:
        username = os.getenv('POSTGRESQL_USER', 'postgres')
        host = os.getenv('POSTGRESQL_HOST', 'postgres')
        db = os.getenv('POSTGRESQL_DATABASE', 'earney')
        os.environ['PGPASSWORD'] = os.getenv('POSTGRESQL_PASSWORD', 'noop')
        with open('/temp/data/dump.sql', 'w') as outfile:
            args = ['pg_dump', '-U', username, '-h', host, db]
            subprocess.call(args, env=os.environ.copy(), stdout=outfile)
    else:
        subprocess.call(['cp', '-r', file_to_archive, '/temp/data'])
    
    subprocess.call(['tar', '-cvf', output_filename, '/temp/data'])
    subprocess.call(['rm', '-rf', '/temp/data'])
    print('Finished file compression to tar')


def healthcheck(uuid=None, status=''):
    try:
        endpoint = os.getenv('HEALTHCHECK_ENDPOINT', 'https://hc-ping.com/')
        healthcheck_endpoint = f'{endpoint}{uuid}{status}'
        requests.get(healthcheck_endpoint, timeout=10)
    except requests.RequestException as e:
        print("Ping failed: %s" % e)


if __name__ == '__main__':
    healthcheck_uuid = os.getenv('HEALTHCHECK_UUID')
    healthcheck(healthcheck_uuid, '/start')

    refresh_path = os.getenv('REFRESH_PATH')
    credentials_path = os.getenv('CREDENTIALS_PATH')
    parent_folder = os.getenv('PARENT_FOLDER')

    file_name = os.getenv('NAME', 'default')
    file_path = os.getenv('FILE_PATH', '/temp/data')

    ts = os.getenv('TS', datetime.datetime.now().strftime("%Y-%m-%dT%H%M%SZ"))
    ts_file_name = f'{file_name}_{ts}.tar'
    metadata = {
        'name': ts_file_name,
        'parents': [parent_folder]
    }

    try:
        service = get_drive_service(refresh_path, credentials_path)
        create_tar_file(ts_file_name, file_path, file_name)
        upload_file(service, file_path, metadata)
        healthcheck(healthcheck_uuid, '')
    except Exception as err:
        print(err)
        healthcheck(healthcheck_uuid, '/fail')
        exit(1)