from typing import Dict, Sequence, Union, cast
import inquirer
from choixe.configurations import XConfig
from choixe.placeholders import Placeholder, PlaceholderType


class XInquirer(object):

    @classmethod
    def safe_cast_placeholder(cls, value, placeholder_type):
        try:
            PlaceholderType.cast(value, placeholder_type)
            return True
        except:
            return False

    @classmethod
    def placeholder_to_question(cls, placeholder: Placeholder) -> Sequence[Union[inquirer.Text, inquirer.List]]:
        message = f'{placeholder.name} ({placeholder.plain_type})'
        validation = lambda _, x: cls.safe_cast_placeholder(x, placeholder.type)

        if len(placeholder.options) > 0:
            question = inquirer.List(placeholder.name,
                                     message=message,
                                     choices=placeholder.options,
                                     default=placeholder.default_value,
                                     validate=validation)
        else:
            question = inquirer.Text(placeholder.name,
                                     message=message,
                                     default=placeholder.default_value,
                                     validate=validation)
        return question

    @classmethod
    def unique_placeholders_with_order(cls, placeholders: Dict[str, Placeholder]):
        unique_names = set([ph.name for k, ph in placeholders.items()])
        unique_phs = []
        for k, ph in placeholders.items():
            if ph.name in unique_names:
                unique_phs.append(ph)
                unique_names.remove(ph.name)
        return unique_phs

    @classmethod
    def prompt(cls, xconfig: XConfig, close_app: bool = True) -> XConfig:
        # copies the xconfig
        xconfig = XConfig.from_dict(xconfig.to_dict())
        # gets unique placeholders preserving order
        unique_phs = cls.unique_placeholders_with_order(xconfig.available_placeholders())
        # user interaction
        questions = [cls.placeholder_to_question(x) for x in unique_phs]
        answers = inquirer.prompt(questions)
        # replaces placeholders with inquirer answers
        xconfig.replace_variables_map(answers)
        xconfig.check_available_placeholders(close_app=close_app)
        return xconfig
