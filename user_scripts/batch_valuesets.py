import sys
import re
from optparse import OptionParser
from nomination.models import Value, ValueSet, Valueset_Values
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import IntegrityError


def addToValset(inputfile, valset):
    """Add a batch of valuesets to database."""
    reg = re.compile("(.*)\t(.*)\t(.*)")
    # rff format should be [key]\t[value]\t[value_order]
    rff = open(inputfile, 'r')

    if valset != "":
        for line in rff:
            res = reg.match(line)
            try:
                Valueset_Values.objects.get(valueset__name=valset, value__key=res.group(1))
            except ObjectDoesNotExist:
                try:
                    valueobj, vcreated = Value.objects.get_or_create(key=res.group(1),
                                                                     value=res.group(2))
                    valuesetobj, screated = ValueSet.objects.get_or_create(name=valset)
                    Valueset_Values.objects.create(valueset=valuesetobj, value=valueobj,
                                                   value_order=res.group(3))
                except IntegrityError:
                    print("Failed to add value '%s' to value set '%s'" % (res.group(1), valset))
            except MultipleObjectsReturned:
                print("Failed to add value '%s' to value set '%s'" % (res.group(1), valset))
    else:
        print("specify a valueset if you want to do something here")

    rff.close()


if __name__ == "__main__":
    usage = "usage: %prog [options] <input file>"
    parser = OptionParser(usage)
    parser.add_option("--valset", action="store", type="string",
                      dest="valset", default="",
                      help="The value set to which values should be added.")

    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        sys.exit(1)
    addToValset(args[0], options.valset)
