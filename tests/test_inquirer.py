import inquirer
from choixe.placeholders import PlaceholderType
from choixe.configurations import XConfig
from choixe.inquirer import XInquirer


class TestInquirer(object):

    def test_xinquirer(self):

        assert XInquirer.safe_cast_placeholder(10, PlaceholderType.INT)
        assert XInquirer.safe_cast_placeholder(10, PlaceholderType.FLOAT)
        assert XInquirer.safe_cast_placeholder(10, PlaceholderType.STR)
        assert XInquirer.safe_cast_placeholder('10', PlaceholderType.INT)
        assert not XInquirer.safe_cast_placeholder('a string', PlaceholderType.INT)
        assert not XInquirer.safe_cast_placeholder('another string', PlaceholderType.FLOAT)
        assert XInquirer.safe_cast_placeholder(True, PlaceholderType.BOOL)
        assert not XInquirer.safe_cast_placeholder(0, PlaceholderType.BOOL)
        assert XInquirer.safe_cast_placeholder('hello', PlaceholderType.PATH)
        assert XInquirer.safe_cast_placeholder('what time is it?', PlaceholderType.DATE)

        d = {
            'a_int': '@int(a_int)',
            'another_int': '@int(a_int)',
            'a_float': '@float(a_float)',
            'a_bool': '@bool(a_bool)',
            'a_str1': '@str(a_str1)',
            'a_str2': '@str(a_str2,hello,hi)',
            'a_str3': '@str(a_str3,one,two,three,default=one)'
        }
        xconfig = XConfig.from_dict(d)
        placeholders = list(xconfig.available_placeholders().values())
        for ph in placeholders:
            q = XInquirer.placeholder_to_question(ph)
            if len(ph.options) > 0:
                assert isinstance(q, inquirer.List)
                assert len(q.choices) == len(ph.options)
            elif ph.type == PlaceholderType.BOOL:
                assert isinstance(q, inquirer.List)
                assert len(q.choices) == 2
            else:
                assert isinstance(q, inquirer.Text)
            assert q.name == ph.name
            assert q.default == ph.default_value

        unique_phs = XInquirer.unique_placeholders_with_order(xconfig.available_placeholders())
        assert len(unique_phs) == 6
        assert unique_phs[0].name == 'a_int'
        assert unique_phs[1].name == 'a_float'
        assert unique_phs[2].name == 'a_bool'
        assert unique_phs[3].name == 'a_str1'
        assert unique_phs[4].name == 'a_str2'
        assert unique_phs[5].name == 'a_str3'
