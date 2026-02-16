from types import SimpleNamespace


class FakeOpenAIClient:
    def __init__(self, response_text: str):
        self._response_text = response_text
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        _ = kwargs
        message = SimpleNamespace(content=self._response_text)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class CapturingOpenAIClient:
    def __init__(self, response_text: str):
        self._response_text = response_text
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self._response_text)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class ErrorOpenAIClient:
    def __init__(self):
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        raise RuntimeError("response_format unsupported")


class FakeAnthropicClient:
    def __init__(self, response_text: str):
        self.calls = []
        self._response_text = response_text
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(text=self._response_text)])


class FakeGoogleClient:
    def __init__(self, response_text: str):
        self.calls = []
        self._response_text = response_text

    def generate_content(self, prompt):
        self.calls.append(prompt)
        return SimpleNamespace(text=self._response_text)
