class MockEnvoy(object):
  """Mocking the envoy package."""

  def __init__(self, return_text):
    self.return_text = return_text

  class Response(object):
    """Mock envoy response."""

    def __init__(self, return_text):
      self.std_out = return_text
      self.status_code = 0

  def run(self, _):
    return self.Response(self.return_text)
