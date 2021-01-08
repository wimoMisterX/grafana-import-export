import requests, json, re, os, argparse

GRAFANA_URL = os.getenv('GRAFANA_URL', 'http://localhost:3000')
TOKEN = os.getenv('GRAFANA_TOKEN', '')

def grafana_get(url):
    response = requests.get(
        "{}{}".format(GRAFANA_URL, url),
        headers={'Authorization': 'Bearer %s' % TOKEN}, 
        verify=True,
    )
    response.raise_for_status()
    return response

def grafana_post(url, payload):
    response = requests.post(
        "{}{}".format(GRAFANA_URL, url),
        headers={'Authorization': 'Bearer %s' % TOKEN}, 
        json=payload,
        verify=True,
    )
    response.raise_for_status()
    return response

def get_folder_id_from_old_folder_url(folder_url):
    if folder_url != "":
        # Get folder uid
        matches = re.search('dashboards\/[A-Za-z0-9]{1}\/(.*)\/.*', folder_url)
        uid = matches.group(1)
        return grafana_get("/api/folders/{0}".format(uid)).json()['id']
    return 0

def read_file(file_path):
    with open(file_path, 'r') as f:
        return json.loads(f.read())

def save_file(path, obj, content):
    with open(os.path.join(path, obj['uid']), 'w') as f:
        f.write(json.dumps(content, indent=2))
    print("saved %s" % obj['title'])

def import_folders(folders_path):
    for path in os.listdir(folders_path):
        grafana_post('/api/folders', read_file(os.path.join(folders_path, path)))

def import_dashboards(dashboards_path):
    for path in os.listdir(dashboards_path):
        content = read_file(os.path.join(dashboards_path, path))
        content['dashboard']['id'] = None
        grafana_post('/api/dashboards/db', {
            'dashboard': content['dashboard'],
            'folderId': get_folder_id_from_old_folder_url(content['meta']['folderUrl']),
            'overwrite': True
        })

def export_folders(folders_path):
    os.makedirs(folders_path, exist_ok=True)
    for folder in grafana_get('/api/search/?type=dash-folder').json():
        save_file(
            folders_path, 
            folder, 
            grafana_get("/api/folders/{0}".format(folder['uid'])).json(),
        )

def export_dashboards(dashboards_path):
    os.makedirs(dashboards_path, exist_ok=True)
    for board in grafana_get('/api/search/?type=dash-db&limit=5000&page=1').json():
        save_file(
            dashboards_path, 
            board, 
            grafana_get("/api/dashboards/{0}".format(board['uri'])).json(),
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['import', 'export'])
    parser.add_argument('path')
    args = parser.parse_args()

    folders_path = os.path.join(args.path, 'folders')
    dashboards_path = os.path.join(args.path, 'dashboards')

    if args.action == 'import':
        import_folders(folders_path)
        import_dashboards(dashboards_path)
    elif args.action == 'export':
        export_folders(folders_path)
        export_dashboards(dashboards_path)
