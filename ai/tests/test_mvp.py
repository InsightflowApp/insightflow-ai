from ai.mvp import MODEL, quick_test

TEST_COUNTRY = 'Australia'
TEST_CAPITAL = 'Canberra'

def test_quick_test():
  response = quick_test(country=TEST_COUNTRY)
  assert TEST_CAPITAL in response


