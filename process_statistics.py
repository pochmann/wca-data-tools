""" See https://github.com/pochmann/wca-statistics-tools """

import glob, os.path, mysql.connector, time, urllib.request, re, sys, subprocess, zipfile, datetime
from wst import *

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

        # Update if necessary
        if not here or here != there:
            print('updating ...')
            print('  downloading export ' + there + ' ...')
            urllib.request.urlretrieve(base + there, there)
            print('  unzipping ...')
            zipfile.ZipFile(there).extract('WCA_export.sql')
            print('  importing to database ...')
            command = 'mysql --default-character-set=utf8 --host={host} --user={user} --password={password} {database} < WCA_export.sql'.format(**config['mysql'])
            subprocess.call(command, shell=True)
            print('  creating indexes ...')
            for table in 'Competitions Continents Countries Events Formats Persons Rounds'.split():
                cursor.execute('ALTER TABLE ' + table + ' ADD INDEX id (id ASC)')
            print('  deleting files ...')
            os.remove(there)
            os.remove('WCA_export.sql')

            # Yup, we did it
            here = there

        # Store the export status
        cursor.execute('DROP TABLE IF EXISTS export_status')
        cursor.execute('CREATE TABLE export_status SELECT %s here, now() last_check', [here])

def process_statistics():
    print('processing statistics ...')

    # Process the query in-files
    for (dirpath, dirnames, filenames) in os.walk('inout'):
        for filename in filenames:
            if filename.endswith('.in'):
                name = os.path.splitext(filename)[0]
                infile = os.path.join(dirpath, filename)
                outfile = os.path.join(dirpath, name + '.out')

                # If out-file is missing or older than in-file...
                if not os.path.isfile(outfile) or os.path.getmtime(outfile) < os.path.getmtime(infile):
                    print(' ', name, '...')

                    # Execute the query
                    query = open(infile).read().strip()
                    for result in cursor.execute(query, multi=True):
                        if result.with_rows:
                            column_names = list(result.column_names)
                            rows = list(result)

                    # Produce the out-file
                    create_post(infile, column_names, rows)

# Connect to the database
cnx = mysql.connector.connect(**config['mysql'])
cursor = cnx.cursor()

# Do the job
update_export()
process_statistics()

# Finish
cursor.close()
cnx.close()
input('Done (hit enter)')
