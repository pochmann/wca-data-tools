""" See https://github.com/pochmann/wca-statistics-tools """

import mysql.connector, itertools, operator, re, os.path, shutil
from collections import *
from time import time

def __internal(filename):
    return os.path.join('internal', filename)

# Load the configuration (if necessary, create it first)
if not os.path.isfile(__internal('config.py')):
    shutil.copy(__internal('config.template.py'), __internal('config.py'))
from internal.config import config

#-----------------------------------------------------------------------------
#   Database stuff
#-----------------------------------------------------------------------------

# TODO: Proper module structure with main?

# TODO: With python code for forum posts, turn the "wca" in "from wca import" into a link to the github repo
#       Maybe like "from [U][URL=foo]wca[/URL][/U] import" or even
#       "[/noparse]from [U][URL=foo]wca[/URL][/U][noparse] import
# TODO: Rename to "db" because you might want to support commands?
#       Nah, for commands the "rows = " doesn't make sense.
#       But do support commands and find good names for both.
def query(q):

    # Connect to the database
    # TODO: Put it in a config
    cnx = mysql.connector.connect(host='localhost', database='wca_export', user='wca_export', password='XXX')
    cursor = cnx.cursor()

    # Get the raw data
    cursor.execute(q)
    rows = list(cursor)

    # Close
    cursor.close()
    cnx.close()

    return rows

#-----------------------------------------------------------------------------
#   Helpers
#-----------------------------------------------------------------------------

#def person_name(id):
    # TODO: Use the mysql query params support instead of python's format
    #return query("SELECT name FROM Persons WHERE id='{}' and subId=1".format(id))[0][0]
    # Make it "name(id)" instead, just like "link(id)"?
    # Use cellName where applicable?
    #   Or id for competitions? (nah, it's good for devs, but "bad" for the public)

def group(rows, index):
    return itertools.groupby(rows, operator.itemgetter(index))

#-----------------------------------------------------------------------------
#   Formatting
#-----------------------------------------------------------------------------

def person_link(id, addon=None):
    if addon is None:
        page = 'p.php?i=' + id
    elif '#' in addon:
        page = 'p.php?i=' + id + addon
    elif '@' in addon:
        page = 'c.php?byPerson=1&i=' + addon[1:] + '#' + id
    return '[url=https://www.worldcubeassociation.org/results/' + page + ']' + person_name[id] + '[/url]'

    # Abolish, use link(id) instead

def link(id):
    pass
    # TODO: Either detect the type of id (person, competition, event, ...) or
    #       build a dictionary of all links when the module is loaded (and after
    #       an sql/tsv update) and just access that. In the latter case, you
    #       could make "link" a dictionary rather than a function, if it's
    #       accessible in the using script. Although function is cleaner and
    #       more consistent. Yeah, use a function.

#def link(text, page):
#    return '[url=https://www.worldcubeassociation.org/results/{}]{}[/url]'.format(page, text)

def create_post(infile, column_names, rows):
    if os.path.isfile(infile):
        dirname, basename = os.path.split(infile)
        name, ext = os.path.splitext(basename)
        outfile = os.path.join(dirname, name + '.out')
        #name, sourcetype = infile.split('.')
        sourcetype = {'.in': 'SQL', '.py': 'Python'}[ext]
        source = open(infile).read().strip()
        source_spoiler = '\n\n[SPOILER="' + sourcetype + '"][CODE][NOPARSE]' + source + '[/NOPARSE][/CODE][/SPOILER]'
    else:
        name = infile
        outfile = os.path.join('inout', name + '.out')
        source_spoiler = ''

    # Prepare a note
    export = query('SELECT here FROM export_status')[0][0].split('.')[0]
    note = "Using data from [url=https://www.worldcubeassociation.org/results/misc/export.html]" + export + "[/url]" + \
           " and Stefan's [url=https://github.com/pochmann/wca-statistics-tools/]WCA Statistics Tools[/url]."

    # Produce the out-file
    #ctr, rank = 0, None
    with open(outfile, 'w', encoding='utf8') as outfile:
        print('[SPOILER="' + name + '"]' + note + '\n\n[TABLE="class:grid,align:left"]', file=outfile)
        print('[TR][TD][B]' + '[/B][/TD][TD][B]'.join(n.split('[')[0] for n in column_names) + '[/B][/TD][/TR]', file=outfile)
        for row in rows:
            tr = '[TR]'
            for column_name, value in zip(column_names, row):
                if type(value) is str and re.match(r'\d{4}[A-Z]{4}\d\d', value):
                    value = re.sub(r'(\d{4}[A-Z]{4}\d\d)([#@]\w+)?', auto_person, value)
                if value in event_name:
                    eventId = value
                    value = event_name[value]
                if value in competition_name:
                    value = competition_name[value]
                align_right = type(value) is not str or re.match(r'\d+(\.\d+)?%?$', value)
                if type(value) is int and column_name == 'Time':
                    # or recognize by turning a result like 142 into a string like 'r:142'?
                    # Or with an instruction in the column name?
                    value = format_value(value)
                    align_right = True
                if type(value) is int and '[R]' in column_name:
                    value = format_value(value, event_format[eventId])
                    align_right = True
                td = '[TD="align:right"]' if align_right else '[TD]'
                tr += td + str(value) + '[/TD]'
            print(tr + '[/TR]', file=outfile)
        print('[/TABLE]' + source_spoiler + '[/SPOILER]', file=outfile)

def auto_person(match):
    personId, addon = match.groups()
    return person_link(personId, addon)

def format_value(value, measure='time'):
    if value < -2: return 'error'
    if value == -1: return 'DNF'
    if value == -2: return 'DNS'
    if value == 0: return ''
    if measure == 'number':
        return str(value)
    if measure == 'time':
        if value < 60 * 100: return '{:.2f}'.format(value / 100.0)
        if value < 60 * 60 * 100: return '{}:{:05.2f}'.format(value // 6000, value % 6000 / 100.0)
        return '{}:{:02}:{:05.2f}'.format(value // 360000, value % 360000 // 6000, value % 6000 / 100.0)
    if measure == 'multi':
        return format_multi_value(value)
    return 'error'

def format_multi_value(value):

    # Extract the value parts
    if value >= 1000000000:
        solved = 99 - value // 10000000 % 100
        attempted = value // 100000 % 100
        time = value % 100000
    else:
        difference = 99 - value // 10000000
        time = value // 100 % 100000
        missed = value % 100
        solved = difference + missed
        attempted = solved + missed

    # Build the time string
    if time == 99999:
        time = '?:??:??'
    elif time < 60 * 60:
        time = '{}:{:02}'.format(time//60, time%60)
    else:
        time = '{}:{:02}:{:02}'.format(time//3600, time//60%60, time%60)

    #--- Combine.
    return "{}/{} ([SIZE=1]{}[/SIZE])".format(solved, attempted, time)

# Fetch person/event/competition names for automatically turning ids into names/links
person_name = dict(query('SELECT id, name FROM Persons WHERE subId=1'))
event_name = dict(query('SELECT id, cellName FROM Events'))
competition_name = dict(query('SELECT id, cellName FROM Competitions'))

event_format = dict(query('SELECT id, format FROM Events'))
