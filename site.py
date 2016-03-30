# coding: utf-8

"""
    Performance and Features html pages
    Linked with mysql database
"""

# General imports
import re
import sys
from docopt import docopt
import MySQLdb
from deepdiff import DeepDiff
import pickle
from bottle import route, run, template, request, get, post, static_file  # , auth_basic

# Parrot imports
from boa.pardb import mantis


def check_pass(username, password):
    """
        Check password
    """
    if username == 'parrot' and password == 'imdb':
        return True
    return False


@get('/perf')
# @auth_basic(check_pass) # <-- decorator
def perf_form_page():
    """
       Fill performance form
    """
    # connect to database
    cur_db = connect_db("172.20.38.50", "mvelay", "user", "sandbox")
    cursor = cur_db.cursor()

    modules_query = """SELECT DISTINCT module from t_performance ORDER BY module ASC"""
    versions_query = """SELECT DISTINCT version from t_performance ORDER BY version ASC"""
    tags_query = """SELECT DISTINCT name from t_performance ORDER BY name ASC"""

    cursor.execute(modules_query)
    modules = cursor.fetchall()

    cursor.execute(versions_query)
    versions = cursor.fetchall()
    versions = [version[0] for version in versions]
    versions.reverse()

    cursor.execute(tags_query)
    tags = cursor.fetchall()

    # Build template page
    with open("./header.html") as header, open('./perf_form.tpl') as perf, open('./footer.html') as footer:
        template_html = header.read() + perf.read() + footer.read()

    html_page = template(template_html, modules=modules, versions=versions, tags=tags)

    cursor.close()

    return html_page


@post('/perf')
def perf_result_page():
    """
        Build HTML result page
    """
    #  Get all fields from form
    module = request.forms.getall('module')
    version = request.forms.getall('version')
    script = request.forms.getall('script')
    tag = request.forms.getall('tag')
    value_inf = request.forms.get('value_inf')
    value_sup = request.forms.get('value_sup')
    # Build html
    result = do_perf_request(module_type=module, version=version, tag=tag,
                             value_inf=value_inf, value_sup=value_sup,
                             script_name=script)

    try:
        kibana_query = 'computer_name:parrotsa* AND name:{0} AND module:{1}'.format(tag[0], module[0])
    except IndexError:
        kibana_query = '*'
    kibana_url = "http://172.20.22.104:5601/app/kibana#/dashboard/performance?_a=(query:(query_string:(query:'{0}')))".format(kibana_query)
    print result
    print kibana_url
    # Build template page
    with open("./header.html") as header, open('./perf.tpl') as perf, open('./footer.html') as footer:
        template_html = header.read() + perf.read() + footer.read()

    if result:
        output = template(template_html, result=result, kibana_url=kibana_url)
    else:
        output = template(template_html, result=[], kibana_url=kibana_url)

    return output


@get('/tunedfields')
def tunedfields_form_page():
    """
    Fill tunedfields form
    """
    #  connect to database
    cur_db = connect_db("172.20.38.50", "mvelay", "user", "darkman")
    cursor = cur_db.cursor()

    mainfields_query = """SELECT DISTINCT mainfield from t_tunedfield ORDER BY mainfield ASC"""

    cursor.execute(mainfields_query)
    mainfields = cursor.fetchall()
    print mainfields
    with open("./header.html") as header, open("./tunedfields_form.tpl") as tune_form, open("./footer.html") as footer:
        template_html = header.read() + tune_form.read() + footer.read()

    html_page = template(template_html, mainfields=mainfields)

    cursor.close()

    return html_page


def do_mainfield_request(mainfield=None):
    """
    Build SQL result request
    @param mainfield: list of mainfields request
    @return: list of SQL results
    """
    # Connect to database
    cur_db = connect_db("172.20.38.50", "mvelay", "user", "darkman")
    cursor = cur_db.cursor()
    conditions = []

    # Connect to Mantis
    mantis_c = mantis.Mantis('jenkins_auto', '1234')
    mantis_project_name = None

    # Build condition with potential multiple selections
    if mainfield and mainfield[0] != 'All':
        conditions.append('WHERE ')
        condition = ' OR '.join(['mainfield="%s"' % name for name in mainfield])
        conditions.append('(' + condition + ')')
        conditions.append('ORDER BY name')
        mantis_project_name = ''

    # build whole query
    cur_query = """ SELECT mainfield, name, description, level, project, category, products
                    FROM t_tunedfield %s;""" % ("".join(conditions))
    cursor.execute(cur_query)
    results = list(cursor.fetchall())

    mantis_project_id = 0

    if results:
        results = results[:1000]  # Limit to first 1000 results
        # Loop on all results
        for index, result in enumerate(results):
            products = []
            results[index] = list(results[index])
            result = list(result)
            # Parse products results
            p_id_queries = ("SELECT platform, package from t_product WHERE pkey='%s'" % id
                            for id in result[6].split('/'))
            for c_query in p_id_queries:
                cursor.execute(c_query)
                product = cursor.fetchall()
                products.append(' '.join(product[0]))
            # Substitute product indexes to product strings
            results[index][6] = '//'.join(products)

            # Substitute Mantis project id by name
            if mantis_project_name is not None and results[index][4] != mantis_project_id:  # Improve number of Mantis requests
                mantis_project_id = results[index][4]
                try:
                    mantis_project_name = mantis_c.get_project_name_from_id(results[index][4])
                except Exception as exc:  # Ignore Mantis Exceptions
                    print exc.message
                    mantis_project_name = mantis_project_id
            results[index][4] = mantis_project_name
    else:
        results = None
    cursor.close()

    return results


@post('/tunedfields')
def tunedfields_result_page():
    """
        Build HTML result page
    """
    #  Get all fields from form
    mainfield = request.forms.getall('mainfields')

    # Build html
    result = do_mainfield_request(mainfield=mainfield)

    # Build template page
    with open("./header.html") as header, open('./mainfields.tpl') as mainfield, open('./footer.html') as footer:
        template_html = header.read() + mainfield.read() + footer.read()

    if result:
        output = template(template_html, result=result)
    else:
        output = template(template, result=[])

    return output


@get('/features')
# @auth_basic(check_pass) # <-- decorator
def features_form_page():
    """
       Fill features form
    """
    #  connect to database
    cur_db = connect_db("172.20.38.50", "mvelay", "user", "sandbox")
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

    # Build template page
    with open("./header.html") as header, open('./features_form.tpl') as features_form, open('./footer.html') as footer:
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
    #  Get all fields from form
    module = request.forms.getall('module')
    version = request.forms.getall('version')
    software = request.forms.getall('sw')

    # Build html
    module, version, software, result = do_features_request(module_type=module,
                                                            version=version, software=software)

    # Build template page
    with open("./header.html") as header, open('./features.tpl') as features, open('./footer.html') as footer:
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
    #  Get all fields from form
    features = request.forms.getall('features')

    # Build html
    features_2, result = do_features_request_2(features=features)

    # Build template page
    with open("./header.html") as header, open('./features_2.tpl') as features, open('./footer.html') as footer:
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
    #  connect to database
    cur_db = connect_db("172.20.38.50", "mvelay", "user", "sandbox")
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

    # Build template page
    with open("./header.html") as header, open('./config_form.tpl') as config_form, open('./footer.html') as footer:
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
    #  Get all fields from form
    module = request.forms.getall('module')
    client = request.forms.getall('client')
    version1 = request.forms.getall('version1')
    version2 = request.forms.getall('version2')

    # Build html
    modif = do_ck5050_ini_diff_request(module, client, version1, version2)

    # Build template page
    with open("./header.html") as header, open('./config.tpl') as config, open('./footer.html') as footer:
        template_html = header.read() + config.read() + footer.read()

    if not modif:
        modif = {}

    output = template(template_html, module=module, client=client, version1=version1,
                      version2=version2, modif=modif)

    return output


@get('/')
def display_home():
    """
        Display home page
    """

    # Build template page
    with open("./header.html", "r") as header, open("./home.html", "r") as home, open("./footer.html", "r") as footer:
        template_html = header.read() + home.read() + "<br>" * 10 + footer.read()

    output = template(template_html)

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

    #  connect to database
    cur_db = connect_db("172.20.38.50", "mvelay", "user", "sandbox")
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
        conditions.append('(' + condition + ')')

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
        results = results[:1000]  # Limit to first 1000 results
    else:
        results = None

    return results


def do_features_request(module_type=None, version=None, software=None):
    """
        perform request on t_feature table
    """

    #  connect to database
    cur_db = connect_db("172.20.38.50", "mvelay", "user", "sandbox")
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
        results = results[:1000]  # Limit to first 1000 results
    else:
        results = None

    return module_type[0], version[0], software[0], results


def do_features_request_2(features=None):
    """
        perform request on t_feature table
    """

    #  connect to database
    cur_db = connect_db("172.20.38.50", "mvelay", "user", "sandbox")
    cursor = cur_db.cursor()

    # build whole query
    cur_query = """ SELECT module, sw, version FROM t_feature
                    WHERE feature="%s" AND supported=1;""" % (features[0])

    print cur_query
    cursor.execute(cur_query)
    results = cursor.fetchall()
    cursor.close()

    if results:
        results = results[:1000]  # Limit to first 1000 results
    else:
        results = None

    return features[0], results


def do_ck5050_ini_diff_request(module, client, version1, version2):
    """
        perform diff request between ck5050_ini files
    """

    #  connect to database
    cur_db = connect_db("172.20.38.50", "mvelay", "user", "sandbox")
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
    try:
        ck5050_ini1 = pickle.loads(results_1[0][0])
        ck5050_ini2 = pickle.loads(results_2[0][0])
        for typemodif, value in DeepDiff(ck5050_ini1, ck5050_ini2).items():
            modif[str(typemodif)] = '\n'.join(value)
            print modif
    except IndexError as c_exc:
        print 'Failed in loaded ck5050.ini'
        print c_exc.message

    return modif


def get_test_to_redo_stats(url):
    """
        Get from DBPhone test_to_redo stats
    """
    import os
    import requests
    from lxml import etree
    from collections import OrderedDict

    categories = [('avrcp',),  ('usb',),  ('wifi',), ('upnp',), ('mtp',), ('ipod',),
                  ('3way',),  ('map',), ('pan',),  ('dun',),  ('pandora',),
                  ('hdmi',), ('bt_streaming', 'a2dp', 'avhfp'), ('opp',),  ('synchro',), ('sms', 'ssp',),
                  ('usb_tethering',),  ('usb_modem',),  ('robustness', ),
                  ('telephony', 'dial', 'discreet', 'phonecall', 'voicereco', 'wbs', 'redial', 'reject'),
                  ('connexion',), ('confcall',), ('indicators', 'battery', 'callerid', 'network', 'provider')]


    tmp_file = '/tmp/test_to_redo.xml'
    with open(tmp_file, 'w') as xml_tests:
        content = requests.get(url)
        if content.status_code == 200:
            xml_tests.write(content.text)
        else:
            return None, None

    xml_tree = etree.parse(tmp_file)

    tests = {}

    # Parse XML test to redo
    authorized_locations = ["Parrot France", "Parrot Shenzen", "Subcontractor"]
    for test in xml_tree.xpath('TEST'):
        datas = test.getchildren()
        # Only take into account FCxxxx product
        if any(data.text.startswith('FC') for data in datas if data.get('name') == 'prod'):
            locations = [d.getchildren() for d in datas if d.get('name') == 'location']
            mainfield = [data.text.lower() for data in datas if data.get('name') == 'mainfield'][0]
            tunedfield = [data.text.lower() for data in datas if data.get('name') == 'tunedfield'][0]

            if any([a.text in authorized_locations for l in locations for a in l]):
                # Update tests dictionary
                tests.setdefault(mainfield, []).append(tunedfield)

    # Build categories dictionary
    stats_categories = OrderedDict()
    for _, value in tests.iteritems():
        for category in categories:
            stats_categories[category] = sum(len(value) for mainfield, value in tests.iteritems()
                                                   if any(mainfield.startswith('compatibility_{}'.format(cat_string))
                                                          for cat_string in category)),\
                                         [value for mainfield, value in tests.iteritems()
                                          if any(mainfield.startswith('compatibility_{}'.format(cat_string))
                                                  for cat_string in category)]


    os.remove(tmp_file)
    return tests, stats_categories


@get('/tests_to_redo')
def test_to_redo():
    """
        Build test_to_redo stats (IOP matrix cleaning)
    """
    from collections import OrderedDict
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator, FormatStrFormatter

    url_base = 'http://172.20.38.50/iop/test_to_redo/dbphone_test_to_redo_'
    year = 2016
    week = 8
    url = '{0}{1}_w{2}.xml'.format(url_base, year, week)

    # Build mainfields dictionary
    stats_mainfields = OrderedDict()
    stats_categories = OrderedDict()

    tests, tests_cat = get_test_to_redo_stats(url)
    while tests and tests_cat:
        stats_mainfields[week] = tests
        stats_categories[week] = tests_cat
        week += 1
        url = '{0}{1}_w{2}.xml'.format(url_base, year, week)

        tests, tests_cat = get_test_to_redo_stats(url)

    c_week = week - 1
    weeks = [w for w, _ in stats_categories.iteritems()]

    with open("./header.html", "r") as header,\
         open("./tests_to_redo.tpl", "r") as tests_to_redo,\
         open("./footer.html", "r") as footer:
        template_html = header.read() + tests_to_redo.read() + "<br>" * 10 + footer.read()

    for category, value in stats_categories[c_week].iteritems():
        x = weeks
        y = [stats_categories[w][category][0] for w in weeks]
        ax = plt.subplot(111)
        ax.plot(x, y, lw=1)

        # set the basic properties
        ax.set_xlabel('Weeks')
        ax.set_ylabel('Tests')
        ax.set_title("{} evolution".format(category[0]))
        xlab = ax.xaxis.get_label()
        ylab = ax.yaxis.get_label()
        xlab.set_style('italic')
        xlab.set_size(10)
        ylab.set_style('italic')
        ylab.set_size(10)
        # set the grid on
        ax.grid('on')

        ax.fill_between(x, 0, y, alpha=0.2)
        majorLocator   = MultipleLocator(0.5)
        ax.xaxis.set_major_locator(majorLocator)

        plt.savefig("static/img/{}.svg".format(category[0]), format='svg')
        plt.close()
    output = template(template_html, stats_mainfields=stats_mainfields, stats_categories=stats_categories, week=c_week)
    return output


@route('/static/img/<filename>')
def server_static_img(filename):
    """
        Enable static image directory
    """
    return static_file(filename, root='static/img')


@route('/stats/<filename>')
def server_static(filename):
    """
        Enable static stats directory
    """
    return static_file(filename, root='static/stats')


def set_options():
    """
        Arguments management using docopt
    """
    help_f = """%s
 
Usage:
  %s -h <host> -p <port>
 
Options:
  -i, --help          
  -h, --host=<host>
  -p, --port=<port>
 
""" % (sys.argv[0], sys.argv[0])
    arguments = docopt(help_f)
    return arguments


def change_header(host="172.20.22.104", port=8081):
    """
        Change IP adress in header
    """

    # Read header template
    with open("./header_template.html", "r") as header:
        content = header.read()

    content_modified = re.sub("172.20.22.104:8081", "%s:%s" % (host, port), content)

    # Modify header with host:port
    with open("./header.html", "w") as header:
        header.write(content_modified)


def main(host="172.20.22.104", port=8081):
    """
        Entry point
    """
    # Parse arguments
    arguments = set_options()

    if arguments.get('--host', None):
        host = arguments['--host']

    if arguments.get('--port', None):
        port = arguments['--port']

    if host and port:
        change_header(host=host, port=port)

    run(host=host, port=port, reloader=True)


if __name__ == '__main__':
    main()
