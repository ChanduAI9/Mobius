import pytest

from app.application.ideas.idea_service import IdeaService


class TestIdeaTriggerDetection:
    def setup_method(self):
        self.service = IdeaService(session=None)  # type: ignore

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("I have an idea for a new app", True),
            ("I've got an idea about async video", True),
            ("new idea: AI code reviewer", True),
            ("What if we build a marketplace", True),
            ("Hello, how are you?", False),
            ("I think this is good", False),
        ],
    )
    def test_detect_idea_trigger(self, text, expected):
        assert self.service.detect_idea_trigger(text) == expected

    def test_extract_idea_content(self):
        text = "I have an idea for a platform that does async video meetings"
        extracted = self.service.extract_idea_content(text)
        assert "async video" in extracted.lower()
