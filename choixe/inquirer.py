from typing import Any, Dict, Sequence, Union
import inquirer
from choixe.configurations import XConfig
from choixe.placeholders import Placeholder, PlaceholderType


class XInquirer(object):

    @classmethod
    def safe_cast_placeholder(cls, value: Any, placeholder_type: PlaceholderType) -> bool:
        """ Checks if the value can be casted to the specified type

        :param value: any value
        :type value: Any
        :param placeholder_type: the placeholder type to check
        :type placeholder_type: PlaceholderType
        :return: either the value can be casted to the specified type or not
        :rtype: bool
        """

        try:
            if placeholder_type == PlaceholderType.BOOL:
                return value is True or value is False
            else:
                PlaceholderType.cast(value, placeholder_type)
            return True
        except Exception as e:
            print(e)
            return False

    @classmethod
    def placeholder_to_question(cls, placeholder: Placeholder) -> Union[inquirer.Text, inquirer.List]:
        """ Converts a placeholder to an inquirer question (to List if the placeholder has
        options or is boolean, Text otherwise)

        :param placeholder: the placeholder
        :type placeholder: Placeholder
        :return: the inquirer question
        :rtype: Union[inquirer.Text, inquirer.List]
        """

        message = f'{placeholder.name} ({placeholder.plain_type})'
        def validation(_, x): return cls.safe_cast_placeholder(x, placeholder.type)

        if len(placeholder.options) > 0 or placeholder.type == PlaceholderType.BOOL:

            if placeholder.type == PlaceholderType.BOOL:
                choices = [True, False]
                default = placeholder.default_value
                if default is not None:
                    default = True if placeholder.default_value.lower() == 'true' else False
            else:
                choices = placeholder.options
                default = placeholder.default_value

            question = inquirer.List(placeholder.name,
                                     message=message,
                                     choices=choices,
                                     default=default,
                                     validate=validation)
        else:
            question = inquirer.Text(placeholder.name,
                                     message=message,
                                     default=placeholder.default_value,
                                     validate=validation)
        return question

    @classmethod
    def unique_placeholders_with_order(cls, placeholders: Dict[str, Placeholder]) -> Sequence[Placeholder]:
        """ Gets uniques placeholders from an xconfig mantaining the order

        :param placeholders: dict of placeholders (the output of XConfig.available_placeholders())
        :type placeholders: Dict[str, Placeholder]
        :return: the unique placeholders
        :rtype: Sequence[Placeholder]
        """

        unique_names = set([ph.name for k, ph in placeholders.items()])
        unique_phs = []
        for k, ph in placeholders.items():
            if ph.name in unique_names:
                unique_phs.append(ph)
                unique_names.remove(ph.name)
        return unique_phs

    @classmethod
    def _system_prompt(cls, questions: Sequence[Union[inquirer.Text, inquirer.List]]) -> dict:
        return inquirer.prompt(questions)

    @classmethod
    def prompt(cls, xconfig: XConfig, close_app: bool = True) -> XConfig:
        """ Prompts the placeholders of an xconfig and fill them
        with the user answers, it returns a copy of the original xconfig

        :param xconfig: the xconfig
        :type xconfig: XConfig
        :param close_app: if True the app will be closed if all the placeholder are not filled, defaults to True
        :type close_app: bool, optional
        :return: the filled xconfig
        :rtype: XConfig
        """

        # copies the xconfig
        xconfig = XConfig.from_dict(xconfig.to_dict())
        # gets unique placeholders preserving order
        unique_phs = cls.unique_placeholders_with_order(xconfig.available_placeholders())
        # user interaction
        questions = [cls.placeholder_to_question(x) for x in unique_phs]
        answers = cls._system_prompt(questions)
        print("ANSW", answers)
        # replaces placeholders with inquirer answers
        xconfig.replace_variables_map(answers)
        xconfig.check_available_placeholders(close_app=close_app)
        return xconfig
