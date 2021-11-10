import inquirer
from schema import Schema
from choixe.placeholders import PlaceholderType
from choixe.configurations import XConfig
from choixe.inquirer import XInquirer


class TestInquirer(object):
    def test_xinquirer(self):

        assert XInquirer.safe_cast_placeholder(10, PlaceholderType.INT)
        assert XInquirer.safe_cast_placeholder(10, PlaceholderType.FLOAT)
        assert XInquirer.safe_cast_placeholder(10, PlaceholderType.STR)
        assert XInquirer.safe_cast_placeholder("10", PlaceholderType.INT)
        assert not XInquirer.safe_cast_placeholder("a string", PlaceholderType.INT)
        assert not XInquirer.safe_cast_placeholder(
            "another string", PlaceholderType.FLOAT
        )
        assert XInquirer.safe_cast_placeholder(True, PlaceholderType.BOOL)
        assert XInquirer.safe_cast_placeholder(0, PlaceholderType.BOOL)
        assert XInquirer.safe_cast_placeholder("hello", PlaceholderType.PATH)
        assert XInquirer.safe_cast_placeholder("what time is it?", PlaceholderType.DATE)

        d = {
            "a_int": "@int(a_int)",
            "another_int": "@int(a_int)",
            "a_float": "@float(a_float)",
            "a_bool1": "@bool(a_bool1)",
            "a_bool2": "@bool(a_bool2, default=AA)",
            "a_bool3": "@bool(a_bool3, default=yEs)",
            "a_str1": "@str(a_str1)",
            "a_str2": "@str(a_str2,hello,hi)",
            "a_str3": "@str(a_str3,one,two,three,default=one)",
        }
        xconfig = XConfig.from_dict(d)
        placeholders = list(xconfig.available_placeholders().values())
        for ph in placeholders:
            q = XInquirer.placeholder_to_question(ph)
            assert q.name == ph.name
            if ph.type == PlaceholderType.BOOL:
                assert isinstance(q, inquirer.Confirm)
                assert isinstance(q.default, bool)
                assert q.default == XInquirer.to_bool(ph.default_value)
            elif len(ph.options) > 0:
                assert isinstance(q, inquirer.List)
                assert len(q.choices) == len(ph.options)
                assert q.default == ph.default_value
            else:
                assert isinstance(q, inquirer.Text)
                assert q.default == ph.default_value

        unique_phs = XInquirer.unique_placeholders_with_order(
            xconfig.available_placeholders()
        )
        assert len(unique_phs) == 8
        assert unique_phs[0].name == "a_int"
        assert unique_phs[1].name == "a_float"
        assert unique_phs[2].name == "a_bool1"
        assert unique_phs[3].name == "a_bool2"
        assert unique_phs[4].name == "a_bool3"
        assert unique_phs[5].name == "a_str1"
        assert unique_phs[6].name == "a_str2"
        assert unique_phs[7].name == "a_str3"

    def test_prompt(self, monkeypatch, tmpdir_factory):

        d = {
            "a_int": "@int(a_int)",
            "another_int": "@int(a_int)",
            "a_float": "@float(a_float)",
            "a_bool": "@bool(a_bool)",
            "a_str1": "@str(a_str1)",
            "a_str2": "@str(a_str2,hello,hi)",
            "a_str3": "@str(a_str3,one,two,three,default=one)",
        }

        fills = {
            "a_int": 2,
            "another_int": 666,
            "a_float": 2.22,
            "a_bool": True,
            "a_str1": "hello",
            "a_str2": "hi",
            "a_str3": "three",
        }

        def custom_prompt(questions):
            return fills

        # old_prompt = XInquirer._system_prompt
        monkeypatch.setattr(XInquirer, "_system_prompt", custom_prompt, raising=True)

        # from dict
        xconfig = XConfig.from_dict(d)
        xconfig.set_schema(Schema({}))
        new_xconfig = XInquirer.prompt(xconfig, close_app=False)

        assert len(new_xconfig.available_placeholders()) == 0
        assert xconfig._filename == new_xconfig._filename
        assert xconfig.get_schema() == new_xconfig.get_schema()

        # from file
        filename = tmpdir_factory.mktemp("configuration") / "cfg.yml"
        xconfig.save_to(filename)
        xconfig = XConfig(filename=filename)
        new_xconfig = XInquirer.prompt(xconfig, close_app=False)

        assert len(new_xconfig.available_placeholders()) == 0
        assert xconfig._filename == new_xconfig._filename
        assert xconfig.get_schema() == new_xconfig.get_schema()
