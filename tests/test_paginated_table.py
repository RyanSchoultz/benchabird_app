from views._paginated_table import paginate, total_pages


def test_paginate_first_page():
    assert paginate(list(range(250)), 0) == list(range(100))


def test_paginate_second_page():
    assert paginate(list(range(250)), 1) == list(range(100, 200))


def test_paginate_last_page():
    assert paginate(list(range(250)), 2) == list(range(200, 250))


def test_paginate_empty():
    assert paginate([], 0) == []


def test_paginate_custom_page_size():
    assert paginate(list(range(20)), 1, page_size=10) == list(range(10, 20))


def test_total_pages_exact():
    assert total_pages(100) == 1


def test_total_pages_overflow():
    assert total_pages(101) == 2


def test_total_pages_empty():
    assert total_pages(0) == 1


def test_total_pages_559():
    assert total_pages(559) == 6


def test_total_pages_custom_page_size():
    assert total_pages(25, page_size=10) == 3
