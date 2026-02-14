import unittest


from models import MessageTemplate as ModelTemplate
from message_templates import MessageTemplateManager


class TestMessageTemplatesCustom(unittest.TestCase):
    def test_models_templates_are_normalized_and_renderable(self):
        custom = [
            ModelTemplate(name="t1", content="Hello {title}", platform="all"),
        ]
        mgr = MessageTemplateManager(custom_templates=custom)
        templates = mgr.get_templates("danggeun")
        self.assertTrue(any(t.name == "t1" for t in templates))

        rendered = mgr.render_template("t1", {"title": "World"})
        self.assertEqual(rendered, "Hello World")


if __name__ == "__main__":
    unittest.main()

