from views._paginated_table import paginate, total_pages

# PAGE_SIZE is 50 — tests use explicit page_size or account for the new default


def test_paginate_first_page():
    assert paginate(list(range(130)), 0) == list(range(50))


def test_paginate_second_page():
    assert paginate(list(range(130)), 1) == list(range(50, 100))


def test_paginate_last_page():
    assert paginate(list(range(130)), 2) == list(range(100, 130))


def test_paginate_empty():
    assert paginate([], 0) == []


def test_paginate_custom_page_size():
    assert paginate(list(range(20)), 1, page_size=10) == list(range(10, 20))


def test_total_pages_exact():
    assert total_pages(50) == 1


def test_total_pages_overflow():
    assert total_pages(51) == 2


def test_total_pages_empty():
    assert total_pages(0) == 1


def test_total_pages_559():
    assert total_pages(559) == 12


def test_total_pages_custom_page_size():
    assert total_pages(25, page_size=10) == 3


def test_paginate_out_of_bounds():
    assert paginate(list(range(10)), 5) == []
