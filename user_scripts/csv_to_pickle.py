import csv
import pickle
import sys
from optparse import OptionParser


def csvToPickle(csvfile, outfile, fdelim, multidelim):
    """Convert csv of url nominations to pickled obj.

    csv may contain multiple values per attribute, the delimiter of these
    multiple values must be given at run time (or defaults to ';'). csv
    currently must have fields defined on first row of file. The resulting
    file from this script makes good input for fielded_batch_ingest.py
    when using the -d option.
    """
    picklef = open(outfile, 'a')
    with open(csvfile) as f:
        reader = csv.DictReader(f, delimiter=fdelim)
        for row in reader:
            if row['url'] == '':
                # we aren't inputting your metadata without a url!
                continue
            for k, v in row.items():
                if multidelim in v:
                    # parse multiple value with delimiter and store as list
                    newval = v.split(multidelim)
                    row[k] = newval
            pickle.dump(row, picklef)

    picklef.close()


if __name__ == '__main__':
    usage = 'usage: %prog [options] <csv input> <output file>'
    parser = OptionParser(usage)
    parser.add_option('-f', '--fielddelim', action='store', type='string',
                      dest='fdelim', default=',', help='The field delimiter for records.')
    parser.add_option('-m', '--multival', action='store', type='string',
                      dest='multidelim', default=';',
                      help='The delimiter of values within a field (gets converted to list obj).')

    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.print_help()
        sys.exit(1)
    csvToPickle(args[0], args[1], options.fdelim, options.multidelim)
