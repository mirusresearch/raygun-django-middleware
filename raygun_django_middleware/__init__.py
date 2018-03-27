import logging
import pprint

from raygun4py import raygunprovider

from django.conf import settings
# from django.http import HttpResponse

logger = logging.getLogger(__name__)


class RaygunMiddleware(object):

    def __init__(self):
        apiKey = getattr(settings, 'RAYGUN4PY_API_KEY', None)
        if not apiKey:
            apiKey = getattr(settings, 'RAYGUN4PY_CONFIG', {}).get('api_key')
        if not apiKey:
            raise Exception('Missing raygun API key')
        self.sender = raygunprovider.RaygunSender(apiKey)

    def process_exception(self, request, exception):
        raygunRequest = self._mapRequest(request)

        # checking debug is what's different from raygun's provided middleware
        # is_unittesting = settings.IS_UNIT_TESTING if hasattr(settings, 'IS_UNIT_TESTING') else False
        is_unittesting = getattr(settings, 'IS_UNITTESTING', None)
        if is_unittesting is None:
            is_unittesting = getattr(settings, 'IS_UNIT_TESTING', False)
        raygun_force = getattr(settings, 'RAYGUN_FORCE', False)  # to test raygun erros
        if not raygun_force and (settings.DEBUG or is_unittesting):
            logger.debug("Not sending error to raygun because DEBUG or IS_UNITTESTING. request to send = \n%s" % pprint.pformat(raygunRequest))
        else:
            logger.debug("Sending to raygun. %s" % pprint.pformat({
                'RAYGUN_FORCE': raygun_force,
                'IS_UNITTESTING': is_unittesting,
                'DEBUG': settings.DEBUG,
            }))
            self.sender.send_exception(exception=exception, request=raygunRequest)
            # return HttpResponse('<h1>Server Error (500)</h1>', status=500)

    def _mapRequest(self, request):
        headers = request.META.items()
        _headers = dict()
        for k, v in headers:
            if not k.startswith('wsgi'):
                _headers[k] = v

        raw_data = None
        # F. Henard 3/27/18 - should not access body in middleware for post requests - see https://docs.djangoproject.com/en/1.11/topics/http/middleware/
        # if hasattr(request, 'body'):
        #     raw_data = request.body
        # elif hasattr(request, 'raw_post_data'):
        #     raw_data = request.raw_post_data
        if hasattr(request, 'raw_post_data'):
            raw_data = request.raw_post_data

        return {
            'hostName': request.get_host(),
            'url': request.path,
            'httpMethod': request.method,
            'ipAddress': request.META.get('REMOTE_ADDR', '?'),
            'queryString': dict((key, request.GET[key]) for key in request.GET),
            # F. Henard - 2/19/18 - bad practice to access request.POST in middleware - see https://stackoverflow.com/a/28641930
            # 'form': dict((key, request.POST[key]) for key in request.POST),
            'form': {},
            'headers': _headers,
            'rawData': raw_data,
        }
