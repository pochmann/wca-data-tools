""" See https://github.com/pochmann/WCA-forum-statistics-tool/ """

import glob, os.path, mysql.connector, time, urllib.request, re, sys, subprocess, zipfile, datetime

# MySQL connection settings
host = 'localhost'
database = 'wca_export'
user = 'wca_export'
password = 'XXX'

def update_export():
    """If export is missing or not current, download the current one."""

    # What do we have here, in the database?
    try:
        cursor.execute('SELECT * FROM export_status')
        here, last_check = next(cursor)
    except:
        here = None

    # Is export missing or older than an hour?
    if not here or datetime.datetime.now() - last_check > datetime.timedelta(hours=1):

        # What's the current export on the WCA site?
        base = 'https://www.worldcubeassociation.org/results/misc/'
        with urllib.request.urlopen(base + 'export.html') as f:
            there = re.search(r'WCA_export\d+_\d+.sql.zip', str(f.read()))
        if not there:
            print('failed looking for the newest export')
            return
        there = there.group(0)

        # Update if newer, otherwise mark local as up-to-date
        if not here or here != there:
            print('updating ...')
            print('  downloading export ' + there + ' ...')
            urllib.request.urlretrieve(base + there, there)
            print('  unzipping ...')
            zipfile.ZipFile(there).extract('WCA_export.sql')
            print('  importing to database ...')
            subprocess.call('mysql --default-character-set=utf8 --host=localhost --user=wca_export --password=XXX wca_export < WCA_export.sql', shell=True)
            here = there
            print('  creating indexes ...')
            for table in 'Competitions Continents Countries Events Formats Persons Rounds'.split():
                cursor.execute('ALTER TABLE ' + table + ' ADD INDEX id (id ASC)')
            print('  deleting files ...')
            os.remove(there)
            os.remove('WCA_export.sql')

        # Store the export status
        cursor.execute('DROP TABLE IF EXISTS export_status')
        cursor.execute('CREATE TABLE export_status SELECT %s here, now() last_check', [here])

def process_statistics():
    print('processing statistics ...')

    cursor.execute('SELECT here FROM export_status')
    export = next(cursor)[0].split('.')[0]
    note = "Using data from [url=https://www.worldcubeassociation.org/results/misc/export.html]" + export + "[/url]" + \
           " and [url=https://github.com/pochmann/WCA-forum-statistics-tool/]Stefan's WCA forum statistics tool[/url]."

    for infile in glob.glob('*.in'):
        name = os.path.splitext(infile)[0]
        outfile = name + '.out'

        # If out-file is missing or older than in-file...
        if not os.path.isfile(outfile) or os.path.getmtime(outfile) < os.path.getmtime(infile):
            print(' ', name, '...')

            # Execute the query
            query = open(infile).read().strip()
            cursor.execute(query)

            # Produce the out-file
            with open(outfile, 'w', encoding='utf8') as outfile:
                print('[SPOILER="' + name + '"]' + note + '\n\n[TABLE="class:grid,align:left"]', file=outfile)
                print('[TR][TD][B]' + '[/B][/TD][TD][B]'.join(n for n in cursor.column_names) + '[/B][/TD][/TR]', file=outfile)
                for row in cursor:
                    tr = '[TR]'
                    for value in row:
                        td = '[TD]' if type(value) is str else '[TD="align:right"]'
                        tr += td + str(value) + '[/TD]'
                    print(tr + '[/TR]', file=outfile)
                print('[/TABLE]\n\n[SPOILER="SQL code"]' + query + '[/SPOILER][/SPOILER]', file=outfile)

# Connect to the database
cnx = mysql.connector.connect(user=user, password=password, host=host, database=database)
cursor = cnx.cursor()

# Do the job
update_export()
process_statistics()

# Finish
cursor.close()
cnx.close()
input('Done (hit enter)')
