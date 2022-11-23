from django.core.paginator import Paginator


def page_obj(request, results, count_on_page):
    '''
    Make Paginator for DB objects and return page with result
    '''
    paginator = Paginator(results, count_on_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
