from django.conf import settings

def maintenance_needed(request):
    """Returns the maintenance message if it is specified in the settings"""
    try:
        maintenance_message = settings.MAINTENANCE_MSG
    except:
        maintenance_message = None
    maintenance_dict = {
        'maintenance_message': maintenance_message,
        }
    return maintenance_dict
