# coding: utf-8

"""
    Performance and Features html pages
    Linked with mysql database
"""

import re
from docopt import docopt
import MySQLdb
from deepdiff import DeepDiff
import pickle
from bottle import route, run, template, request, get, post, static_file, auth_basic

def check_pass(username, password):
    """
        Check password
    """
    if username == 'massiou' and password == '****':
        return True
    return False

@get('/perf')
@auth_basic(check_pass) # <-- decorator
def perf_form_page():
    """
       Fill performance form
    """
    # connect to database
    cur_db = connect_db("localhost", "massiou", "user", "sandbox")
    cursor = cur_db.cursor()

    modules_query = """SELECT DISTINCT module from t_performance ORDER BY module ASC"""
    versions_query = """SELECT DISTINCT version from t_performance ORDER BY version ASC"""
    scripts_query = """SELECT DISTINCT script_name from t_performance ORDER BY script_name ASC"""
    tags_query = """SELECT DISTINCT name from t_performance ORDER BY name ASC"""

    cursor.execute(modules_query)
    modules = cursor.fetchall()

    cursor.execute(versions_query)
    versions = cursor.fetchall()

    cursor.execute(scripts_query)
    scripts = cursor.fetchall()

    cursor.execute(tags_query)
    tags = cursor.fetchall()

    #Build template page
    with open("./header.html") as header, \
         open('./perf_form.tpl') as perf, \
         open('./footer.html') as footer:
        template_html = header.read() + perf.read() + footer.read()

    html_page = template(template_html, modules=modules, versions=versions,
                         scripts=scripts, tags=tags)

    cursor.close()

    return html_page

@post('/perf')
def perf_result_page():
    """
        Build HTML result page
    """
    # Get all fields from form
    module = request.forms.getall('module')
    version = request.forms.getall('version')
    print version
    script = request.forms.getall('script')
    tag = request.forms.getall('tag')
    value_inf = request.forms.get('value_inf')
    value_sup = request.forms.get('value_sup')

    # Build html
    result = do_perf_request(module_type=module, version=version, tag=tag,
                             value_inf=value_inf, value_sup=value_sup,
                             script_name=script)

    #Build template page
    with open("./header.html") as header, \
         open('./perf.tpl') as perf, \
         open('./footer.html') as footer:
        template_html = header.read() + perf.read() + footer.read()

    if result:
        output = template(template_html, result=result)
    else:
        output = template(template, result=[])

    return output

@get('/features')
#@auth_basic(check_pass) # <-- decorator
def features_form_page():
    """
       Fill performance form
    """
    # connect to database
    cur_db = connect_db("localhost", "massiou", "user", "sandbox")
    cursor = cur_db.cursor()

    modules_query = """SELECT DISTINCT module from t_feature ORDER BY module ASC"""
    versions_query = """SELECT DISTINCT version from t_feature ORDER BY version ASC"""
    sw_query = """SELECT DISTINCT sw from t_feature ORDER BY version ASC"""
    features_query = """SELECT DISTINCT feature from t_feature ORDER BY feature ASC"""

    cursor.execute(modules_query)
    modules = cursor.fetchall()

    cursor.execute(versions_query)
    versions = cursor.fetchall()

    cursor.execute(sw_query)
    software = cursor.fetchall()

    cursor.execute(features_query)
    features = cursor.fetchall()

    #Build template page
    with open("./header.html") as header, \
         open('./features_form.tpl') as features_form, \
         open('./footer.html') as footer:
        template_html = header.read() + features_form.read() + footer.read()

    html_page = template(template_html, modules=modules, versions=versions,
                         sw=software, features=features)

    cursor.close()

    return html_page

@post('/features')
def features_result_page():
    """
        Build HTML result page
    """
    # Get all fields from form
    module = request.forms.getall('module')
    version = request.forms.getall('version')
    software = request.forms.getall('sw')

    # Build html
    module, version, software, result = do_features_request(module_type=module,
                                                            version=version, software=software)

    #Build template page
    with open("./header.html") as header, \
         open('./features.tpl') as features, \
         open('./footer.html') as footer:
        template_html = header.read() + features.read() + footer.read()

    if not result:
        result = []

    output = template(template_html, module=module, version=version, sw=software, result=result)

    return output

@post('/features_2')
def features_2_result_page():
    """
        Build HTML result page
    """
    # Get all fields from form
    features = request.forms.getall('features')

    # Build html
    features_2, result = do_features_request_2(features=features)

    #Build template page
    with open("./header.html") as header, \
         open('./features_2.tpl') as features, \
         open('./footer.html') as footer:
        template_html = header.read() + features.read() + footer.read()

    if not result:
        result = []

    output = template(template_html, features=features_2, result=result)

    return output

@get('/config')
def config_diff_form_page():
    """
       Fill config diff form page
    """
    # connect to database
    cur_db = connect_db("localhost", "massiou", "user", "sandbox")
    cursor = cur_db.cursor()

    modules_query = """SELECT DISTINCT module from t_ck5050_ini ORDER BY module ASC"""
    versions_query = """SELECT DISTINCT version from t_ck5050_ini ORDER BY version DESC"""
    clients_query = """SELECT DISTINCT client from t_ck5050_ini ORDER BY client DESC"""

    cursor.execute(modules_query)
    modules = cursor.fetchall()

    cursor.execute(versions_query)
    versions = cursor.fetchall()

    cursor.execute(clients_query)
    clients = cursor.fetchall()

    #Build template page
    with open("./header.html") as header, \
         open('./config_form.tpl') as config_form, \
         open('./footer.html') as footer:
        template_html = header.read() + config_form.read() + footer.read()

    html_page = template(template_html, modules=modules, versions=versions,
                         clients=clients)

    cursor.close()

    return html_page

@post('/config')
def perform_diff_config_result_page():
    """
        Display diff config result page
    """
    # Get all fields from form
    module = request.forms.getall('module')
    client = request.forms.getall('client')
    version1 = request.forms.getall('version1')
    version2 = request.forms.getall('version2')

    # Build html
    modif = do_ck5050_ini_diff_request(module, client, version1, version2)

    #Build template page
    with open("./header.html") as header, \
         open('./config.tpl') as config, \
         open('./footer.html') as footer:
        template_html = header.read() + config.read() + footer.read()

    if not modif:
        modif = {}

    output = template(template_html, module=module, client=client, version1=version1,
                      version2=version2, modif=modif)

    return output

def connect_db(host=None, user=None, pwd=None, db_name=None):
    """
        Connect to SQL Database
    """
    db_c = MySQLdb.connect(host, user, pwd, db_name)
    return db_c

def do_perf_request(script_name=None, module_type=None, tag=None,
                    version=None, value_sup=None, value_inf=None):
    """
        perform request on t_performance table
    """

    # connect to database
    cur_db = connect_db("localhost", "massiou", "user", "sandbox")
    cursor = cur_db.cursor()

    conditions = []

    if script_name and script_name[0] != 'All':
        condition = ' OR '.join(['script_name="%s"' % name for name in script_name])
        conditions.append('(' + condition + ')')

    if module_type and module_type[0] != 'All':
        condition = ' OR '.join(['module="%s"' % mod_type for mod_type in module_type])
        conditions.append('(' + condition + ')')

    if tag and tag[0] != 'All':
        condition = ' OR '.join(['name="%s"' % cur_tag for cur_tag in tag])
        conditions.append('(' + condition + ')')

    if version and version[0] != 'All':
        condition = ' OR '.join(['version="%s"' % cur_ver for cur_ver in version])
        conditions.append('(' + condition  + ')')

    if value_inf:
        conditions.append('value>=%s' % value_inf)

    if value_sup:
        conditions.append('value<=%s' % value_sup)

    # build sql conditions
    if conditions:
        query_conditions = 'WHERE ' + ' AND '.join(conditions)
    else:
        query_conditions = ''
    # build whole query
    cur_query = """ SELECT module, version, sw, name, title, script_name, value, date
                    FROM t_performance %s;""" % query_conditions

    print cur_query
    cursor.execute(cur_query)
    results = cursor.fetchall()
    cursor.close()

    if results:
        results = results[:1000] #Limit to first 1000 results
    else:
        results = None

    return results

def do_features_request(module_type=None, version=None, software=None):
    """
        perform request on t_feature table
    """

    # connect to database
    cur_db = connect_db("localhost", "massiou", "user", "sandbox")
    cursor = cur_db.cursor()

    # build whole query
    cur_query = """ SELECT feature, supported FROM t_feature
                    WHERE module="%s" AND version="%s" AND sw="%s";""" \
                % (module_type[0], version[0], software[0])

    print cur_query
    cursor.execute(cur_query)
    results = cursor.fetchall()
    cursor.close()

    if results:
        results = results[:1000] #Limit to first 1000 results
    else:
        results = None

    return module_type[0], version[0], software[0], results

def do_features_request_2(features=None):
    """
        perform request on t_feature table
    """

    # connect to database
    cur_db = connect_db("localhost", "massiou", "user", "sandbox")
    cursor = cur_db.cursor()

    # build whole query
    cur_query = """ SELECT module, sw, version FROM t_feature
                    WHERE feature="%s" AND supported=1;""" % (features[0])

    print cur_query
    cursor.execute(cur_query)
    results = cursor.fetchall()
    cursor.close()

    if results:
        results = results[:1000] #Limit to first 1000 results
    else:
        results = None

    return features[0], results

def do_ck5050_ini_diff_request(module, client, version1, version2):
    """
        perform diff request between ck5050_ini files
    """

    # connect to database
    cur_db = connect_db("localhost", "massiou", "user", "sandbox")
    cursor = cur_db.cursor()

    # build whole query
    cur_query_1 = """SELECT ck5050 FROM t_ck5050_ini
                   WHERE module='%s' AND client='%s' AND version='%s'""" \
                   % (module[0], client[0], version1[0])

    cursor.execute(cur_query_1)
    results_1 = cursor.fetchall()

    cur_query_2 = """SELECT ck5050 FROM t_ck5050_ini
                   WHERE module='%s' AND client='%s' AND version='%s'""" \
                   % (module[0], client[0], version2[0])

    cursor.execute(cur_query_2)
    results_2 = cursor.fetchall()

    modif = {}
    if results_1:
        ck5050_ini1 = pickle.loads(results_1[0][0])

    if results_2:
        ck5050_ini2 = pickle.loads(results_2[0][0])

    # MUST have 2 'not empty' ck5050ini
    if results_1 and results_2:
        for typemodif, value in DeepDiff(ck5050_ini1, ck5050_ini2).items():
            modif[str(typemodif)] = '\n'.join(value)
            print modif
    return modif


@route('/static/img/<filename>')
def server_static(filename):
    """
        Enable static image directory
    """
    return static_file(filename, root='static/img')

def set_options():
    """
        Arguments management using docopt
    """
    help_f = """site.py
 
Usage:
  site.py -h <host> -p <port>
 
Options:
  -i, --help          
  -h, --host=<host>
  -p, --port=<port>
 
"""
    arguments = docopt(help_f)
    return arguments

def change_header(host="localhost", port=8081):
    """
        Change IP adress in header
    """

    with open("./header.html", "r+") as header:
        content = header.read()
        content_modified = re.sub("localhost:8081", "%s:%s" % (host, port), content)
        print content_modified
        header.write(content_modified)

def main(host="localhost", port=8081):
    """
        Entry point
    """
    #Parse arguments
    arguments = set_options()

    if arguments.get('--host', None):
        host = arguments['--host']

    if arguments.get('--port', None):
        port = arguments['--port']

    run(host=host, port=port, reloader=True)

if __name__ == '__main__':
    main()

