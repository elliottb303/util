#!/usr/bin/python
__author__ = 'Elliott Brun'

import converter_model
import json
import os
from sqlobject import *
import datetime
import argparse
import logging
from yaml import load
from gnosis.xml.pickle import dumps


"""
 "The Transformer" is a tool to create files in a set of specific formats based on a common input.
The Transformer will get an input in Yaml format from the file system, convert it to one or multiple formats specified by parameters in the command line, and create a file per output format.

Example:
./the-transformar --input inputfile.yaml --output outputfile.xml --output outputfile.properties --output outputfile.customformat1 --output outputfile.customformat2
"""


class Transformer:
    def __init__(self):
        self.name = None
        self.base_path = os.path.abspath(os.getcwd())
        self.orig_path = None
        self.input = None
        self.output_paths = []
        self.outputs = []
        self.output_types = ['xml', 'json']
        self.conversion_date = str(datetime.datetime.now())

        # logging
        self.logger = logging.getLogger('TransformClass')
        self.logger.setLevel(logging.INFO)
        self.logger.info('creating instance transformer class')

    def database_connect(self, filename):
        """Connect to local path db file and creates tables if needed
        """
        # Put together correct path to sqlite db file.
        db_filename = os.path.abspath(filename)
        db_filename = db_filename.replace(':', '|')

        # Start a connection to the sqlite db file.
        sqlhub.processConnection = connectionForURI('sqlite:' + db_filename)

        # Create tables if they do not exist
        transformerModel.Original.createTable(ifNotExists=True)
        transformerModel.Output.createTable(ifNotExists=True)

    def save_to_database(self, output):
        """
        :return: operations saved to local db
        """
        # create original document record
        orig_entry = transformerModel.Original(name=self.name, path=self.orig_path,
                                               conversion_date=self.conversion_date)
        self.logger.debug('Created original record: %s ' % orig_entry)

        # create output records
        output_path = "%s/%s.%s" % (self.base_path, self.input, output)
        outputs_entry = transformerModel.Output(path=output_path, name=self.name, format=output, original=orig_entry)
        self.logger.debug('Created output record: %s ' % outputs_entry)

    def convert(self, output):
        self.logger.debug('Running conversion to %s' % output)
        outfile = '%s.%s' % (self.input.split('.')[0], output)
        data = None
        with open(self.input, 'r') as infile:

            if output == 'xml':
                data = dumps(load(infile.read()))
            elif output == 'json':
                data = load(infile)

        if not data:
            self.logger.debug('Error with parsing  %s data' % output)
            sys.exit(1)

        with open(outfile, "w") as out:
            if output == 'xml':
                out.write(data)
            elif output == 'json':
                out.write(json.dumps(data, sort_keys=True, indent=4))


def main():

    # logging
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info('Starting transform script....\n')

    t = Transformer()

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Yaml file input",
                        action="store")
    parser.add_argument("-o", "--output", action='append', help="Format or formats to output to. XML or properties avail")
    parser.add_argument("-d", "--debug", action='store_true', help="set script to debug logging")

    # check input args
    flags = parser.parse_args()
    if not flags.output or not flags.input:
        print "Output format required!"
        sys.exit(1)
    for o in flags.output:
        if o not in t.output_types:
            print "Error - %s output type not available, skipping." % o
        else:
            t.outputs.append(o)
    t.input = flags.input
    if '.yaml' not in t.input:
        t.input += ".yaml"
    t.name = flags.input.rstrip('.yaml')
    t.orig_path = "%s/%s.%s" % (t.base_path, t.name, t.input)
    if flags.debug:
        t.logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)


    # convert files and write DB info
    t.database_connect('dbfile')
    for out in t.outputs:
        t.convert(out)
        t.save_to_database(out)

    # print output some history to date from stored DB
    outputs = transformerModel.Output.select()
    for o in outputs:
        print "Output file %s output path: %s " % (o.name, o.path)


if __name__ == '__main__':
    main()
