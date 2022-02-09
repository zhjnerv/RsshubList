import requests
import json
import bs4
import time


def check_server(url):
    print("[%s]checking server" % url)
    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            raise Exception("Http Error %s" % response.status_code)

        content = response.content.decode("utf8")
        soup = bs4.BeautifulSoup(content, 'lxml')

        if soup.title.text == 'Welcome to RSSHub!' and 'If you see this page, the RSSHub is successfully installed and working.' in content:
            print("[%s]server ok" % url)

            return 1
        else:
            print("[%s]not rsshub server" % url)

            return 0

    except Exception as e:
        print("[%s]server error" % url)

        return -1


def check_rss_app(url, app):
    print("[%s]check app %s" % (url, app))
    try:
        response = requests.get("%s%s" % (url, app), timeout=10)
        if response.status_code != 200:

            raise Exception("Http Error %s" % response.status_code)

        return True

    except Exception as e:
        print("[%s]check app fail %s" % (url, str(e)))

        return False


def load_check_app():
    with open("app.json", encoding='utf8') as f:
        apps = json.loads(f.read())

        return apps


def load_database():
    with open("database.json", encoding='utf8') as f:
        try:
            data = json.loads(f.read())
            print("load %s data in database file" % len(data))
            return data
        except Exception as e:
            print("database file read error %s" % e)
            print("create empty database")

            return {}


def load_servers():
    servers = []
    with open("servers.txt", encoding='utf8') as f:
        for line in f.readlines():
            server = line.replace("\n", "").replace(" ", "")
            if server != "" and server not in servers:
                servers.append(server)

    print("load %s server in servers.txt" % len(servers))

    return servers


def timestamp_to_str(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def build_data():
    database = load_database()

    result = []
    for _, data in database.items():
        server = {
            "url": data['url'],
            "last_check_time": timestamp_to_str(data['last_check_time'])
        }
        if data['last_error_time'] is not None and data['last_error_time'] != "":
            if int(time.time()) - int(data['last_error_time']) > 6000:
                print("server down skip")
                continue
            else:
                server["status"] = "DOWN"
                server['last_error_time'] = timestamp_to_str(
                    data['last_error_time'])
                server['apps'] = {}
        else:
            server["status"] = "UP"
            server['last_error_time'] = None
            server['apps'] = data['apps']

        result.append(server)

    with open("docs/data.json", "w", encoding='utf8') as f:
        f.write(json.dumps(result))

        print("build data file to docs/data.json")

    with open("README.template.md", "r", encoding='utf8') as fr:
        template = fr.read()
        
        template = template.replace("{{generated_at}}",
                         timestamp_to_str(int(time.time())))
        apps = load_check_app()
        template = template.replace("{{server_apps}}", " | ".join(
            [app['name'].upper() for app in apps]))
        template = template.replace("{{server_tabs}}", " | ".join(["----" for _ in apps]))
        table = ""
        for d in result:
            print(d)
            row = "| %s | %s | %s | %s |" % (
                d['url'], d['status'], d['last_check_time'], d['last_error_time'])
            for _, value in d['apps'].items():
                if value:
                    row += "OK"
                row += "|"
            row += "  \n"
            table += row

        template = template.replace("{{server_list}}", table)
        with open("README.md", "w", encoding='utf8') as fw:
            fw.write(template)
        print("generate readme.md file")


if __name__ == "__main__":

    apps = load_check_app()
    database = load_database()
    servers = load_servers()

    for server in servers:
        timestamp = int(time.time())
        if server in database:
            data = database[server]
        else:
            data = {}
        check_result = check_server(server)
        data['url'] = server
        data['last_check_time'] = timestamp
        if check_result != 1:
            data['last_error_time'] = timestamp
            data['last_error_code'] = check_result
        else:
            data['last_error_time'] = ""
            data['last_error_code'] = ""
            data['apps'] = {}
            for app in apps:
                data['apps'][app['name']] = check_rss_app(server, app['path'])

        database[server] = data

        with open("database.json", "w") as f:
            f.write(json.dumps(database))

    build_data()
