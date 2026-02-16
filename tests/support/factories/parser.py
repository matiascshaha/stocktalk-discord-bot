from src.ai_parser import AIParser
from tests.support.fakes.ai_clients import FakeOpenAIClient


def parser_with_fake_openai_response(response_text: str) -> AIParser:
    parser = AIParser()
    parser.provider = "openai"
    parser.client = FakeOpenAIClient(response_text)
    return parser
