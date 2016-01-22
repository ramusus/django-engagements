from django.conf import settings

from open_facebook import OpenFacebook

graph = OpenFacebook(settings.FACEBOOK_API_ACCESS_TOKEN)



def recursive_graph_call(graph_id, *args, **kwargs):

    '''
        response = recursive_graph_call('147863265269488_588392457883231/likes', limit=500)
    '''

    if 'limit' not in kwargs:
        kwargs['limit'] = 100

    response = {}

    while True:
        r = graph.get(graph_id, *args, **kwargs)

        if not response: # first call
            response = r
        else:
            response['data'] += r['data']

        if 'paging' in r:
            kwargs['after'] = r['paging']['cursors']['after']
        else:
            break

    return response
